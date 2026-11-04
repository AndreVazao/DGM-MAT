[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PackageExe,

    [string]$TargetExe = "C:\ProgramasGodMode\DGM-MAT\installed\DGM-MAT.exe",

    [string]$BackupRoot = "C:\ProgramasGodMode\DGM-MAT\update-backups"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Stop-ExactInstalledProcess {
    param([Parameter(Mandatory = $true)][string]$ExecutablePath)

    $fullPath = [System.IO.Path]::GetFullPath($ExecutablePath)
    $running = Get-CimInstance Win32_Process -Filter "Name = 'DGM-MAT.exe'" |
        Where-Object {
            $_.ExecutablePath -and
            [System.IO.Path]::GetFullPath($_.ExecutablePath) -ieq $fullPath
        }

    foreach ($processInfo in $running) {
        Stop-Process -Id $processInfo.ProcessId -Force
        $deadline = (Get-Date).AddSeconds(15)
        do {
            Start-Sleep -Milliseconds 250
            $stillRunning = Get-Process -Id $processInfo.ProcessId -ErrorAction SilentlyContinue
        } while ($stillRunning -and (Get-Date) -lt $deadline)

        if ($stillRunning) {
            throw "Could not stop the installed DGM-MAT process (PID $($processInfo.ProcessId))."
        }
    }
}

function Assert-RuntimeStopped {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8181/health" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            throw "DGM-MAT API is still responding on 127.0.0.1:8181. Stop the runtime before updating so its database is not being written."
        }
    }
    catch {
        if ($_.Exception.Message -like "DGM-MAT API is still responding*") {
            throw
        }
        # Connection refusal/timeout means no local API was confirmed.
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

New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDirectory = Join-Path $BackupRoot $timestamp
New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $backupDirectory "exe") -Force | Out-Null

Stop-ExactInstalledProcess -ExecutablePath $targetPath
Assert-RuntimeStopped

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
    @{ Source = (Join-Path $installRoot ".runtime"); Relative = "data\repository\.runtime" },
    @{ Source = (Join-Path $targetDirectory ".runtime"); Relative = "data\installed\.runtime" }
)

$backupRecords = @()
foreach ($entry in $preserved) {
    $backupRecords += Backup-PreservedPath -Source $entry.Source -RelativeDestination $entry.Relative -BackupDirectory $backupDirectory
}

$sourceHash = (Get-FileHash -LiteralPath $packagePath -Algorithm SHA256).Hash
$stagedPath = Join-Path $targetDirectory "DGM-MAT.exe.new"
try {
    Copy-Item -LiteralPath $packagePath -Destination $stagedPath -Force
    $stagedHash = (Get-FileHash -LiteralPath $stagedPath -Algorithm SHA256).Hash
    if ($stagedHash -ne $sourceHash) {
        throw "Staged executable SHA-256 does not match the package."
    }

    Move-Item -LiteralPath $stagedPath -Destination $targetPath -Force
    $installedHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash
    if ($installedHash -ne $sourceHash) {
        throw "Installed executable SHA-256 does not match the package."
    }
}
catch {
    Remove-Item -LiteralPath $stagedPath -Force -ErrorAction SilentlyContinue
    if ($oldExeBackup -and (Test-Path -LiteralPath $oldExeBackup)) {
        Copy-Item -LiteralPath $oldExeBackup -Destination $targetPath -Force
    }
    throw
}

$manifest = [ordered]@{
    schema = "dgm-mat-safe-windows-update.v1"
    installed_at = (Get-Date).ToString("o")
    package_exe = $packagePath
    target_exe = $targetPath
    new_sha256 = $sourceHash
    previous_sha256 = $oldExeHash
    previous_exe_backup = $oldExeBackup
    backup_directory = $backupDirectory
    preserved_data = $backupRecords
    deliberately_untouched = @(
        (Join-Path $localDgmRoot "security"),
        (Join-Path $userDgmRoot "worktrees"),
        (Join-Path $installRoot "DGM-MAT-Memory"),
        (Join-Path $installRoot "memory_sync"),
        (Join-Path $installRoot "storage\runtime"),
        (Join-Path $installRoot ".runtime")
    )
    note = "Only the executable was replaced. Configuration, credentials, runtime data, memory repositories and worktrees were not uninstalled or deleted."
}
$manifestPath = Join-Path $backupDirectory "INSTALL-MANIFEST.json"
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8

Write-Host "DGM-MAT executable updated successfully."
Write-Host "Installed: $targetPath"
Write-Host "SHA-256: $sourceHash"
Write-Host "Backup: $backupDirectory"
Write-Host "Manifest: $manifestPath"
Write-Host "The runtime was not started. Start it only after reviewing the backup manifest."
