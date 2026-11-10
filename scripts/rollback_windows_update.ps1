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
    $matching = Get-CimInstance Win32_Process -Filter "Name = 'DGM-MAT.exe'" |
        Where-Object {
            $_.ExecutablePath -and
            [System.IO.Path]::GetFullPath($_.ExecutablePath) -ieq $targetPath
        }
    if (-not $matching) {
        throw "The API port is active, but no process matches the rollback target executable. Refusing to stop an unrelated runtime."
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

$restoreTemp = "$targetPath.rollback"
Copy-Item -LiteralPath $backupPath -Destination $restoreTemp -Force
$expectedHash = (Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash
$actualHash = (Get-FileHash -LiteralPath $restoreTemp -Algorithm SHA256).Hash
if ($expectedHash -ne $actualHash) {
    Remove-Item -LiteralPath $restoreTemp -Force -ErrorAction SilentlyContinue
    throw "Rollback copy failed SHA-256 verification."
}
Move-Item -LiteralPath $restoreTemp -Destination $targetPath -Force

$launcherTarget = [string]$manifest.launcher_target
$launcherBackup = [string]$manifest.previous_launcher_backup
if ($launcherTarget -and $launcherBackup -and (Test-Path -LiteralPath $launcherBackup)) {
    $launcherRestoreTemp = "$launcherTarget.rollback"
    Copy-Item -LiteralPath $launcherBackup -Destination $launcherRestoreTemp -Force
    $launcherExpectedHash = (Get-FileHash -LiteralPath $launcherBackup -Algorithm SHA256).Hash
    $launcherActualHash = (Get-FileHash -LiteralPath $launcherRestoreTemp -Algorithm SHA256).Hash
    if ($launcherExpectedHash -ne $launcherActualHash) {
        Remove-Item -LiteralPath $launcherRestoreTemp -Force -ErrorAction SilentlyContinue
        throw "Rollback service launcher copy failed SHA-256 verification."
    }
    Move-Item -LiteralPath $launcherRestoreTemp -Destination $launcherTarget -Force
}
elseif ($launcherTarget -and -not $manifest.launcher_previous_sha256) {
    Remove-Item -LiteralPath $launcherTarget -Force -ErrorAction SilentlyContinue
}

Write-Host "Previous DGM-MAT executable restored: $targetPath"
if ($launcherTarget) { Write-Host "Previous service launcher restored: $launcherTarget" }
Write-Host "Persistent data was left untouched."
