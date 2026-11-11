
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PackageExe,

    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[A-Fa-f0-9]{64}$")]
    [string]$ExpectedExeSha256,

    [string]$TargetExe = "C:\ProgramasGodMode\DGM-MAT\installed\DGM-MAT.exe",

    [string]$BackupRoot = "C:\ProgramasGodMode\DGM-MAT\update-backups"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-DgmMatCockpitShortcut {
    param(
        [Parameter(Mandatory = $true)][string]$ExecutablePath,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory
    )

    $desktopPath = [Environment]::GetFolderPath("Desktop")
    if (-not $desktopPath -or -not (Test-Path -LiteralPath $desktopPath)) {
        throw "The current user's Desktop directory is unavailable."
    }

    $shortcutPath = Join-Path $desktopPath "DGM-MAT Chat.lnk"
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $ExecutablePath
    $shortcut.Arguments = "--cockpit-only"
    $shortcut.WorkingDirectory = $WorkingDirectory
    $shortcut.Description = "Open the DGM-MAT chat cockpit; the backend must already be running."
    $shortcut.IconLocation = "$ExecutablePath,0"
    $shortcut.Save()
    return $shortcutPath
}

function Test-DgmMatApiPortOpen {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $pending = $client.BeginConnect("127.0.0.1", 8181, $null, $null)
        if (-not $pending.AsyncWaitHandle.WaitOne(1000)) { return $false }
        $client.EndConnect($pending)
        return $true
    }
    catch { return $false }
    finally { $client.Close() }
}

function Assert-ExpectedRuntimeOwner {
    param([Parameter(Mandatory = $true)][string]$ExecutablePath)

    $fullPath = [System.IO.Path]::GetFullPath($ExecutablePath)
    try {
        $listeners = @(Get-NetTCPConnection -LocalPort 8181 -State Listen -ErrorAction Stop)
    }
    catch {
        throw "Cannot identify the process listening on API port 8181. Refusing to stop any process."
    }
    if (-not $listeners) {
        throw "API port 8181 was reported open but has no identifiable listener. Refusing to stop any process."
    }
    foreach ($listener in $listeners) {
        $owner = Get-CimInstance Win32_Process -Filter "ProcessId = '$($listener.OwningProcess)'"
        if (-not $owner -or -not $owner.ExecutablePath -or
            [System.IO.Path]::GetFullPath($owner.ExecutablePath) -ine $fullPath) {
            throw "API port 8181 is owned by a process other than the target DGM-MAT executable. Refusing shutdown."
        }
    }
}

function Request-GracefulRuntimeShutdown {
    param([Parameter(Mandatory = $true)][string]$ExecutablePath)

    if (-not (Test-DgmMatApiPortOpen)) { return }
    Assert-ExpectedRuntimeOwner -ExecutablePath $ExecutablePath

    $bootstrapPath = Join-Path $env:LOCALAPPDATA "DGM-MAT\security\bootstrap.token"
    if (-not (Test-Path -LiteralPath $bootstrapPath -PathType Leaf)) {
        throw "The local bootstrap credential is unavailable. Runtime was not stopped; no installation changes were made."
    }
    $bootstrap = (Get-Content -LiteralPath $bootstrapPath -Raw -ErrorAction Stop).Trim()
    if ($bootstrap.Length -lt 60) {
        throw "The local bootstrap credential is invalid. Runtime was not stopped."
    }

    $sessionArgs = @{
        Method = "Post"
        Uri = "http://127.0.0.1:8181/auth/session"
        Headers = @{ Authorization = "Bearer $bootstrap" }
        ContentType = "application/json"
        Body = (@{ client_id = "dgm-mat-windows-installer" } | ConvertTo-Json -Compress)
        TimeoutSec = 5
    }
    $session = Invoke-RestMethod @sessionArgs
    $accessToken = [string]$session.access_token
    if ($accessToken.Length -lt 20) {
        throw "The local API did not issue a shutdown session. Runtime was not stopped."
    }

    $shutdownArgs = @{
        Method = "Post"
        Uri = "http://127.0.0.1:8181/runtime/shutdown"
        Headers = @{ Authorization = "Bearer $accessToken" }
        ContentType = "application/json"
        Body = "{}"
        TimeoutSec = 5
    }
    $shutdown = Invoke-RestMethod @shutdownArgs
    if ($shutdown.status -ne "shutdown_requested") {
        throw "The runtime did not acknowledge an orderly shutdown request."
    }

    $deadline = (Get-Date).AddSeconds(30)
    while (Test-DgmMatApiPortOpen) {
        if ((Get-Date) -ge $deadline) {
            throw "The runtime did not close its API port within 30 seconds. No process was killed and installation was aborted."
        }
        Start-Sleep -Milliseconds 500
    }
}

function Assert-RuntimeStopped {
    if (Test-DgmMatApiPortOpen) {
        throw "DGM-MAT API is still listening on 127.0.0.1:8181. Stop the runtime before updating."
    }
}

function Wait-NoInstalledProcess {
    param([Parameter(Mandatory = $true)][string]$ExecutablePath)

    $fullPath = [System.IO.Path]::GetFullPath($ExecutablePath)
    $deadline = (Get-Date).AddSeconds(20)
    while ($true) {
        $running = @(Get-CimInstance Win32_Process -Filter "Name = 'DGM-MAT.exe'" |
            Where-Object {
                $_.ExecutablePath -and
                [System.IO.Path]::GetFullPath($_.ExecutablePath) -ieq $fullPath
            })
        if (-not $running) { return }

        $cockpit = @($running | Where-Object { $_.CommandLine -match "--cockpit-only" })
        if ($cockpit) {
            $ids = ($cockpit | ForEach-Object { $_.ProcessId }) -join ", "
            throw "Close the DGM-MAT Chat cockpit process(es) $ids and rerun the installer. No process was killed."
        }
        if ((Get-Date) -ge $deadline) {
            $ids = ($running | ForEach-Object { $_.ProcessId }) -join ", "
            throw "Runtime process(es) $ids did not exit after orderly shutdown. No process was killed."
        }
        Start-Sleep -Milliseconds 500
    }
}

function Backup-PreservedPath {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$RelativeDestination,
        [Parameter(Mandatory = $true)][string]$BackupDirectory
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        return [PSCustomObject]@{
            source = $Source
            exists = $false
            backup = $null
            kind = "missing"
        }
    }

    $destination = Join-Path $BackupDirectory $RelativeDestination
    $item = Get-Item -LiteralPath $Source -Force

    if ($item.PSIsContainer) {
        New-Item -ItemType Directory -Path $destination -Force | Out-Null
        & robocopy.exe $Source $destination /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
        $copyCode = $LASTEXITCODE
        if ($copyCode -ge 8) {
            throw "Backup failed for '$Source' (robocopy exit code $copyCode)."
        }
        $kind = "directory"
    }
    else {
        $destinationParent = Split-Path -Parent $destination
        New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
        Copy-Item -LiteralPath $Source -Destination $destination -Force
        $kind = "file"
    }

    return [PSCustomObject]@{
        source = $Source
        exists = $true
        backup = $destination
        kind = $kind
    }
}

$packagePath = (Resolve-Path -LiteralPath $PackageExe).Path
$targetPath = [System.IO.Path]::GetFullPath($TargetExe)
$targetDirectory = Split-Path -Parent $targetPath

if (-not (Test-Path -LiteralPath $packagePath -PathType Leaf)) {
    throw "Package executable does not exist: $packagePath"
}
if ((Get-Item -LiteralPath $packagePath).Length -lt 10MB) {
    throw "Package executable is unexpectedly small; refusing installation."
}
if ($packagePath -ieq $targetPath) {
    throw "PackageExe and TargetExe refer to the same file. Extract the package first."
}

# Verify the executable against the digest obtained separately from the official
# GitHub Actions artifact before creating directories, backups, or stopping runtime.
$packageHash = (Get-FileHash -LiteralPath $packagePath -Algorithm SHA256).Hash
if (-not [string]::Equals($packageHash, $ExpectedExeSha256, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Package executable SHA-256 does not match the independently supplied expected digest. No installation changes were made."
}

Request-GracefulRuntimeShutdown -ExecutablePath $targetPath
Assert-RuntimeStopped
Wait-NoInstalledProcess -ExecutablePath $targetPath

New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDirectory = Join-Path $BackupRoot $timestamp
New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $backupDirectory "exe") -Force | Out-Null

$oldExeBackup = $null
$oldExeHash = $null
if (Test-Path -LiteralPath $targetPath) {
    $oldExeHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash
    $oldExeBackup = Join-Path $backupDirectory "exe\DGM-MAT.exe.previous"
    Copy-Item -LiteralPath $targetPath -Destination $oldExeBackup -Force
}

$installRoot = Split-Path -Parent (Split-Path -Parent $targetPath)
$localDgmRoot = Join-Path $env:LOCALAPPDATA "DGM-MAT"
$userDgmRoot = Join-Path $env:USERPROFILE ".dgm-mat"

# Back up data directories that may be migrated or written by the new runtime.
# Credentials under AppData\Local\DGM-MAT\security are deliberately excluded
# and left in place; the worktree directory is also left in place.
$preserved = @(
    @{ Source = (Join-Path $localDgmRoot "runtime"); Relative = "data\localappdata\DGM-MAT\runtime" },
    @{ Source = (Join-Path $localDgmRoot "recovery-inbox"); Relative = "data\localappdata\DGM-MAT\recovery-inbox" },
    @{ Source = (Join-Path $localDgmRoot "diagnostics"); Relative = "data\localappdata\DGM-MAT\diagnostics" },
    @{ Source = (Join-Path $localDgmRoot "reports"); Relative = "data\localappdata\DGM-MAT\reports" },
    @{ Source = (Join-Path $userDgmRoot "recovery-ledger.sqlite3"); Relative = "data\userprofile\.dgm-mat\recovery-ledger.sqlite3" },
    @{ Source = (Join-Path $installRoot "DGM-MAT-Memory"); Relative = "data\DGM-MAT-Memory" },
    @{ Source = (Join-Path $installRoot "memory_sync"); Relative = "data\memory_sync" },
    @{ Source = (Join-Path $installRoot "storage\runtime"); Relative = "data\repository\storage\runtime" },
    @{ Source = (Join-Path $installRoot "storage\cognition"); Relative = "data\repository\storage\cognition" },
    @{ Source = (Join-Path $installRoot ".runtime"); Relative = "data\repository\.runtime" },
    @{ Source = (Join-Path $installRoot "logs"); Relative = "data\repository\logs" },
    @{ Source = (Join-Path $targetDirectory ".runtime"); Relative = "data\installed\.runtime" }
)

$backupRecords = @()
foreach ($entry in $preserved) {
    $backupRecords += Backup-PreservedPath -Source $entry.Source -RelativeDestination $entry.Relative -BackupDirectory $backupDirectory
}

# The startup shortcut calls this source-tree service manager. Update it together
# with the executable so the next boot launches the frozen build, not main.py.
$launcherSource = Join-Path (Split-Path -Parent $packagePath) "scripts\autostart\backend_service.py"
$launcherTarget = Join-Path $installRoot "scripts\autostart\backend_service.py"
if (-not (Test-Path -LiteralPath $launcherSource -PathType Leaf)) {
    throw "The package is missing scripts\autostart\backend_service.py. Refusing a partial runtime update."
}
New-Item -ItemType Directory -Path (Split-Path -Parent $launcherTarget) -Force | Out-Null
$launcherBackupRecord = Backup-PreservedPath -Source $launcherTarget -RelativeDestination "launcher\backend_service.py.previous" -BackupDirectory $backupDirectory
$backupRecords += $launcherBackupRecord
$oldLauncherBackup = $launcherBackupRecord.backup
$oldLauncherHash = $null
if (Test-Path -LiteralPath $launcherTarget) {
    $oldLauncherHash = (Get-FileHash -LiteralPath $launcherTarget -Algorithm SHA256).Hash
}

$sourceHash = $packageHash
$launcherSourceHash = (Get-FileHash -LiteralPath $launcherSource -Algorithm SHA256).Hash
$stagedPath = Join-Path $targetDirectory "DGM-MAT.exe.new"
$stagedLauncherPath = "$launcherTarget.new"
try {
    Copy-Item -LiteralPath $packagePath -Destination $stagedPath -Force
    $stagedHash = (Get-FileHash -LiteralPath $stagedPath -Algorithm SHA256).Hash
    if ($stagedHash -ne $sourceHash) {
        throw "Staged executable SHA-256 does not match the package."
    }

    Copy-Item -LiteralPath $launcherSource -Destination $stagedLauncherPath -Force
    $stagedLauncherHash = (Get-FileHash -LiteralPath $stagedLauncherPath -Algorithm SHA256).Hash
    if ($stagedLauncherHash -ne $launcherSourceHash) {
        throw "Staged service launcher SHA-256 does not match the package."
    }

    Move-Item -LiteralPath $stagedPath -Destination $targetPath -Force
    Move-Item -LiteralPath $stagedLauncherPath -Destination $launcherTarget -Force

    $installedHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash
    if ($installedHash -ne $sourceHash) {
        throw "Installed executable SHA-256 does not match the package."
    }
    $installedLauncherHash = (Get-FileHash -LiteralPath $launcherTarget -Algorithm SHA256).Hash
    if ($installedLauncherHash -ne $launcherSourceHash) {
        throw "Installed service launcher SHA-256 does not match the package."
    }
}
catch {
    Remove-Item -LiteralPath $stagedPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $stagedLauncherPath -Force -ErrorAction SilentlyContinue
    if ($oldExeBackup -and (Test-Path -LiteralPath $oldExeBackup)) {
        Copy-Item -LiteralPath $oldExeBackup -Destination $targetPath -Force
    }
    if ($oldLauncherBackup -and (Test-Path -LiteralPath $oldLauncherBackup)) {
        Copy-Item -LiteralPath $oldLauncherBackup -Destination $launcherTarget -Force
    }
    elseif (-not $oldLauncherHash) {
        Remove-Item -LiteralPath $launcherTarget -Force -ErrorAction SilentlyContinue
    }
    throw
}

$cockpitShortcutPath = $null
try {
    $cockpitShortcutPath = New-DgmMatCockpitShortcut -ExecutablePath $targetPath -WorkingDirectory $installRoot
}
catch {
    Write-Warning "The runtime was updated, but the DGM-MAT Chat desktop shortcut could not be created: $($_.Exception.GetType().Name)"
}

$manifest = [ordered]@{
    schema = "dgm-mat-safe-windows-update.v1"
    installed_at = (Get-Date).ToString("o")
    package_exe = $packagePath
    target_exe = $targetPath
    new_sha256 = $sourceHash
    expected_exe_sha256 = $ExpectedExeSha256.ToUpperInvariant()
    package_sha256_verified_before_mutation = $true
    previous_sha256 = $oldExeHash
    previous_exe_backup = $oldExeBackup
    launcher_target = $launcherTarget
    launcher_new_sha256 = $launcherSourceHash
    launcher_previous_sha256 = $oldLauncherHash
    cockpit_shortcut = $cockpitShortcutPath
    previous_launcher_backup = $oldLauncherBackup
    backup_directory = $backupDirectory
    preserved_data = $backupRecords
    deliberately_untouched = @(
        (Join-Path $localDgmRoot "security"),
        (Join-Path $userDgmRoot "worktrees"),
        (Join-Path $installRoot "DGM-MAT-Memory"),
        (Join-Path $installRoot "memory_sync"),
        (Join-Path $installRoot "storage\runtime"),
        (Join-Path $installRoot "storage\cognition"),
        (Join-Path $installRoot ".runtime")
    )
    note = "The executable and its managed startup launcher were replaced. Configuration, credentials, runtime/cognition data, memory repositories and worktrees were not uninstalled or deleted."
}
$manifestPath = Join-Path $backupDirectory "INSTALL-MANIFEST.json"
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8

Write-Host "DGM-MAT executable updated successfully."
Write-Host "Installed: $targetPath"
Write-Host "SHA-256: $sourceHash"
Write-Host "Service launcher: $launcherTarget"
Write-Host "Launcher SHA-256: $launcherSourceHash"
Write-Host "Backup: $backupDirectory"
Write-Host "Manifest: $manifestPath"
if ($cockpitShortcutPath) { Write-Host "Chat cockpit shortcut: $cockpitShortcutPath" }
Write-Host "The runtime was not started. The startup shortcut will now launch the installed executable through the updated service manager."