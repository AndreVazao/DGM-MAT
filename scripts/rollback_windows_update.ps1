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

$running = Get-CimInstance Win32_Process -Filter "Name = 'DGM-MAT.exe'" |
    Where-Object {
        $_.ExecutablePath -and
        [System.IO.Path]::GetFullPath($_.ExecutablePath) -ieq $targetPath
    }
foreach ($processInfo in $running) {
    Stop-Process -Id $processInfo.ProcessId -Force
}

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8181/health" -UseBasicParsing -TimeoutSec 2
    if ($response.StatusCode -eq 200) {
        throw "DGM-MAT API is still active. Stop the runtime before rollback."
    }
}
catch {
    if ($_.Exception.Message -like "DGM-MAT API is still active*") {
        throw
    }
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
Write-Host "Previous DGM-MAT executable restored: $targetPath"
Write-Host "Persistent data was left untouched."
