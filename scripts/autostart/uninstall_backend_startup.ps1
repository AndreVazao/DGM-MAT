# Path: C:\ProgramasGodMode\DGM-MAT\scripts\autostart\uninstall_backend_startup.ps1
$ErrorActionPreference = 'Stop'
$StartupFolder = [Environment]::GetFolderPath('Startup')
$ShortcutPath = Join-Path $StartupFolder 'DGM-MAT Headless.lnk'
$BackupPath = Join-Path $env:LOCALAPPDATA 'DGM-MAT\startup-backup\DGM-MAT Headless.original.lnk'
if (Test-Path $BackupPath) {
    Copy-Item -LiteralPath $BackupPath -Destination $ShortcutPath -Force
    Write-Output "RESTORED original startup shortcut: $ShortcutPath"
} elseif (Test-Path $ShortcutPath) {
    Remove-Item -LiteralPath $ShortcutPath -Force
    Write-Output "REMOVED DGM-MAT startup shortcut: $ShortcutPath"
} else {
    Write-Output 'NO_CHANGE: no DGM-MAT startup shortcut found.'
}
Write-Output 'The running backend is not stopped by this script.'
Write-Output 'To stop the API separately, run backend_service.py stop.'
