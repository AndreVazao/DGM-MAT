# Path: C:\ProgramasGodMode\DGM-MAT\scripts\autostart\install_local_bootstrap_credential.ps1
[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$securityDirectory = Join-Path $env:LOCALAPPDATA "DGM-MAT\security"
$credentialPath = Join-Path $securityDirectory "bootstrap.token"

if ((Test-Path -LiteralPath $credentialPath) -and -not $Force) {
    throw "Bootstrap credential already exists. Use -Force only to rotate it deliberately."
}

New-Item -ItemType Directory -Path $securityDirectory -Force | Out-Null
$currentIdentity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$systemIdentity = "SYSTEM"

$directoryAcl = New-Object System.Security.AccessControl.DirectorySecurity
$directoryAcl.SetAccessRuleProtection($true, $false)
$directoryAcl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    $currentIdentity, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
)))
$directoryAcl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    $systemIdentity, "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
)))
Set-Acl -LiteralPath $securityDirectory -AclObject $directoryAcl

$randomBytes = New-Object byte[] 64
$generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $generator.GetBytes($randomBytes)
}
finally {
    $generator.Dispose()
}
$secret = [BitConverter]::ToString($randomBytes).Replace("-", "").ToLowerInvariant()
[System.IO.File]::WriteAllText($credentialPath, $secret, [System.Text.Encoding]::ASCII)

$fileAcl = New-Object System.Security.AccessControl.FileSecurity
$fileAcl.SetAccessRuleProtection($true, $false)
$fileAcl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    $currentIdentity, "FullControl", "Allow"
)))
$fileAcl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    $systemIdentity, "FullControl", "Allow"
)))
Set-Acl -LiteralPath $credentialPath -AclObject $fileAcl

$storedLength = (Get-Item -LiteralPath $credentialPath).Length
if ($storedLength -ne 128) {
    Remove-Item -LiteralPath $credentialPath -Force
    throw "Credential verification failed; the incomplete file was removed."
}

Write-Output "Bootstrap credential installed with restricted Windows ACL."
Write-Output "Path: $credentialPath"
Write-Output "Secret value was not displayed."
