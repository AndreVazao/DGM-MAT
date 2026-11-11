[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ManifestPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$manifestFile = (Resolve-Path -LiteralPath $ManifestPath).Path
$manifest = Get-Content -LiteralPath $manifestFile -Raw | ConvertFrom-Json

if ($manifest.schema -ne "dgm-mat-safe-windows-update.v1") {
    throw "Unsupported DGM-MAT update manifest."
}
if (-not $manifest.previous_exe_backup -or -not (Test-Path -LiteralPath $manifest.previous_exe_backup)) {
    throw "The manifest does not contain a recoverable previous executable."
}

$targetPath = [System.IO.Path]::GetFullPath([string]$manifest.target_exe)
$backupPath = (Resolve-Path -LiteralPath $manifest.previous_exe_backup).Path

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

if (Test-DgmMatApiPortOpen) {
    try {
        $listeners = @(Get-NetTCPConnection -LocalPort 8181 -State Listen -ErrorAction Stop)
    }
    catch {
        throw "Cannot identify the process listening on API port 8181. Rollback refused without stopping any process."
    }
    if (-not $listeners) {
        throw "API port 8181 was reported open but has no identifiable listener. Rollback refused."
    }
    foreach ($listener in $listeners) {
        $owner = Get-CimInstance Win32_Process -Filter "ProcessId = '$($listener.OwningProcess)'"
        if (-not $owner -or -not $owner.ExecutablePath -or
            [System.IO.Path]::GetFullPath($owner.ExecutablePath) -ine $targetPath) {
            throw "API port 8181 is owned by a process other than the rollback target executable. Rollback refused."
        }
    }
    $bootstrapPath = Join-Path $env:LOCALAPPDATA "DGM-MAT\security\bootstrap.token"
    if (-not (Test-Path -LiteralPath $bootstrapPath -PathType Leaf)) {
        throw "Local bootstrap credential is unavailable; rollback stopped without killing any process."
    }
    $bootstrap = (Get-Content -LiteralPath $bootstrapPath -Raw -ErrorAction Stop).Trim()
    if ($bootstrap.Length -lt 60) { throw "Local bootstrap credential is invalid." }
    $sessionArgs = @{
        Method = "Post"
        Uri = "http://127.0.0.1:8181/auth/session"
        Headers = @{ Authorization = "Bearer $bootstrap" }
        ContentType = "application/json"
        Body = (@{ client_id = "dgm-mat-windows-rollback" } | ConvertTo-Json -Compress)
        TimeoutSec = 5
    }
    $session = Invoke-RestMethod @sessionArgs
    $accessToken = [string]$session.access_token
    if ($accessToken.Length -lt 20) { throw "Local API session exchange failed." }
    $shutdownArgs = @{
        Method = "Post"
        Uri = "http://127.0.0.1:8181/runtime/shutdown"
        Headers = @{ Authorization = "Bearer $accessToken" }
        ContentType = "application/json"
        Body = "{}"
        TimeoutSec = 5
    }
    $shutdown = Invoke-RestMethod @shutdownArgs
    if ($shutdown.status -ne "shutdown_requested") { throw "Runtime did not acknowledge orderly shutdown." }
    $deadline = (Get-Date).AddSeconds(30)
    while (Test-DgmMatApiPortOpen) {
        if ((Get-Date) -ge $deadline) { throw "Runtime did not stop within 30 seconds; no process was killed." }
        Start-Sleep -Milliseconds 500
    }
}

$deadline = (Get-Date).AddSeconds(20)
while ($true) {
    $running = @(Get-CimInstance Win32_Process -Filter "Name = 'DGM-MAT.exe'" |
        Where-Object {
            $_.ExecutablePath -and
            [System.IO.Path]::GetFullPath($_.ExecutablePath) -ieq $targetPath
        })
    if (-not $running) { break }
    $cockpit = @($running | Where-Object { $_.CommandLine -match "--cockpit-only" })
    if ($cockpit) {
        $ids = ($cockpit | ForEach-Object { $_.ProcessId }) -join ", "
        throw "Close DGM-MAT cockpit process(es) $ids and rerun rollback. No process was killed."
    }
    if ((Get-Date) -ge $deadline) {
        $ids = ($running | ForEach-Object { $_.ProcessId }) -join ", "
        throw "Runtime process(es) $ids did not exit after orderly shutdown. No process was killed."
    }
    Start-Sleep -Milliseconds 500
}

# Validate every previous artifact before replacing either target. This prevents
# a bad launcher backup from leaving a mixed executable/launcher installation.
$expectedHash = [string]$manifest.previous_sha256
if ($expectedHash -notmatch "^[A-Fa-f0-9]{64}$") {
    throw "Manifest does not contain a valid previous executable SHA-256; rollback refused."
}
$backupHash = (Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash
if (-not [string]::Equals($backupHash, $expectedHash, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Previous executable backup does not match the manifest SHA-256; rollback refused."
}

$launcherTarget = [string]$manifest.launcher_target
$launcherBackup = [string]$manifest.previous_launcher_backup
$launcherExpectedHash = [string]$manifest.launcher_previous_sha256
$restoreLauncher = $false
if ($launcherTarget) {
    if ($launcherExpectedHash -match "^[A-Fa-f0-9]{64}$") {
        if (-not $launcherBackup -or -not (Test-Path -LiteralPath $launcherBackup -PathType Leaf)) {
            throw "Previous launcher backup is missing; rollback refused before modifying the executable."
        }
        $launcherBackupHash = (Get-FileHash -LiteralPath $launcherBackup -Algorithm SHA256).Hash
        if (-not [string]::Equals($launcherBackupHash, $launcherExpectedHash, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Previous launcher backup does not match the manifest SHA-256; rollback refused."
        }
        $restoreLauncher = $true
    }
    elseif ($launcherExpectedHash) {
        throw "Manifest contains an invalid previous launcher SHA-256; rollback refused."
    }
}

$restoreTemp = "$targetPath.rollback"
if ($expectedHash -notmatch "^[A-Fa-f0-9]{64}$") {
    throw "Manifest does not contain a valid previous executable SHA-256; rollback refused."
}
$backupHash = (Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash
if (-not [string]::Equals($backupHash, $expectedHash, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Previous executable backup does not match the manifest SHA-256; rollback refused."
}
Copy-Item -LiteralPath $backupPath -Destination $restoreTemp -Force
$actualHash = (Get-FileHash -LiteralPath $restoreTemp -Algorithm SHA256).Hash
if (-not [string]::Equals($expectedHash, $actualHash, [StringComparison]::OrdinalIgnoreCase)) {
    Remove-Item -LiteralPath $restoreTemp -Force -ErrorAction SilentlyContinue
    throw "Rollback copy failed manifest SHA-256 verification."
}
Move-Item -LiteralPath $restoreTemp -Destination $targetPath -Force

if ($restoreLauncher) {
    $launcherRestoreTemp = "$launcherTarget.rollback"
    Copy-Item -LiteralPath $launcherBackup -Destination $launcherRestoreTemp -Force
    $launcherActualHash = (Get-FileHash -LiteralPath $launcherRestoreTemp -Algorithm SHA256).Hash
    if (-not [string]::Equals($launcherExpectedHash, $launcherActualHash, [StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $launcherRestoreTemp -Force -ErrorAction SilentlyContinue
        throw "Rollback service launcher copy failed manifest SHA-256 verification."
    }
    Move-Item -LiteralPath $launcherRestoreTemp -Destination $launcherTarget -Force
}
elseif ($launcherTarget -and -not $launcherExpectedHash) {
    Remove-Item -LiteralPath $launcherTarget -Force -ErrorAction SilentlyContinue
}

Write-Host "Previous DGM-MAT executable restored: $targetPath"
if ($launcherTarget) { Write-Host "Previous service launcher restored: $launcherTarget" }
Write-Host "Persistent data was left untouched."
