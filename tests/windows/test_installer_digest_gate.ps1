$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$installer = Join-Path $repoRoot "scripts\install_windows_update.ps1"
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
    throw "Installer script not found: $installer"
}

$tokens = $null
$parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
    $installer,
    [ref]$tokens,
    [ref]$parseErrors
) | Out-Null
if ($parseErrors.Count -gt 0) {
    $parseErrors | ForEach-Object { Write-Error $_.Message }
    throw "Installer PowerShell syntax validation failed."
}

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("dgm-installer-digest-" + [Guid]::NewGuid().ToString("N"))
$packageDirectory = Join-Path $tempRoot "package"
$targetDirectory = Join-Path $tempRoot "target\installed"
$backupRoot = Join-Path $tempRoot "backups"
$packageExe = Join-Path $packageDirectory "DGM-MAT.exe"
$targetExe = Join-Path $targetDirectory "DGM-MAT.exe"

try {
    New-Item -ItemType Directory -Path $packageDirectory -Force | Out-Null
    $stream = [System.IO.File]::Open(
        $packageExe,
        [System.IO.FileMode]::CreateNew,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $stream.SetLength(10MB + 1)
    }
    finally {
        $stream.Dispose()
    }

    $actualDigest = (Get-FileHash -LiteralPath $packageExe -Algorithm SHA256).Hash
    $wrongDigest = if ($actualDigest -eq ("0" * 64)) { "1" * 64 } else { "0" * 64 }
    $failedClosed = $false

    try {
        & $installer -PackageExe $packageExe -ExpectedExeSha256 $wrongDigest -TargetExe $targetExe -BackupRoot $backupRoot
    }
    catch {
        $failedClosed = $true
        if ($_.Exception.Message -notmatch "SHA-256 does not match") {
            throw "Installer failed for an unexpected reason: $($_.Exception.Message)"
        }
    }

    if (-not $failedClosed) {
        throw "Installer accepted a mismatched executable digest."
    }
    if (Test-Path -LiteralPath $targetDirectory) {
        throw "Target directory was created before digest rejection."
    }
    if (Test-Path -LiteralPath $backupRoot) {
        throw "Backup directory was created before digest rejection."
    }

    Write-Host "PASS: installer rejects a mismatched SHA-256 before creating target or backup directories."
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}
