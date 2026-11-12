[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PackageRoot = [System.IO.Path]::GetFullPath($PackageRoot)
$installer = Join-Path $PackageRoot "scripts\install_windows_update.ps1"
$packageExe = Join-Path $PackageRoot "DGM-MAT.exe"
$checksumFile = Join-Path $PackageRoot "DGM-MAT.exe.sha256"

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdministrator)) {
    $arguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", ('"' + $PSCommandPath + '"'),
        "-PackageRoot", ('"' + $PackageRoot + '"')
    )
    $elevated = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $arguments -Wait -PassThru
    exit $elevated.ExitCode
}

foreach ($required in @($installer, $packageExe, $checksumFile)) {
    if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
        throw "Update package is incomplete. Missing required file: $required"
    }
}

$checksumText = Get-Content -LiteralPath $checksumFile -Raw -ErrorAction Stop
$match = [regex]::Match($checksumText, '(?im)^\s*([a-f0-9]{64})\s+DGM-MAT\.exe\s*$')
if (-not $match.Success) {
    throw "The package SHA-256 sidecar is malformed. No installation changes were made."
}

$expectedHash = $match.Groups[1].Value.ToUpperInvariant()
Write-Host "DGM-MAT Windows update"
Write-Host "Package: $packageExe"
Write-Host "Expected SHA-256: $expectedHash"
Write-Host "The updater will verify the digest, request graceful shutdown, back up local state and replace only managed runtime files."

try {
    & $installer -PackageExe $packageExe -ExpectedExeSha256 $expectedHash
}
catch {
    Write-Error ("DGM-MAT update failed: " + $_.Exception.GetType().Name + ": " + $_.Exception.Message)
    exit 1
}
