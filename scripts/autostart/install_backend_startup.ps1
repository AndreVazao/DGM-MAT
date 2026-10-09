# Path: C:\ProgramasGodMode\DGM-MAT\scripts\autostart\install_backend_startup.ps1
$ErrorActionPreference = 'Stop'
$ProjectRoot = 'C:\ProgramasGodMode\DGM-MAT'
$Python = (Get-Command python.exe -ErrorAction Stop).Source
$PythonW = Join-Path (Split-Path $Python) 'pythonw.exe'
$Manager = Join-Path $ProjectRoot 'scripts\autostart\backend_service.py'
$StartupFolder = [Environment]::GetFolderPath('Startup')
$ShortcutPath = Join-Path $StartupFolder 'DGM-MAT Headless.lnk'
$BackupFolder = Join-Path $env:LOCALAPPDATA 'DGM-MAT\startup-backup'
$BackupPath = Join-Path $BackupFolder 'DGM-MAT Headless.original.lnk'
if (-not (Test-Path $Manager)) { throw "Backend manager not found: $Manager" }
if (-not (Test-Path $PythonW)) { throw "pythonw.exe not found: $PythonW" }
New-Item -ItemType Directory -Path $BackupFolder -Force | Out-Null
if ((Test-Path $ShortcutPath) -and -not (Test-Path $BackupPath)) {
    Copy-Item -LiteralPath $ShortcutPath -Destination $BackupPath
}
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PythonW
$Shortcut.Arguments = '"' + $Manager + '" start'
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.WindowStyle = 7
$Shortcut.Description = 'Starts only the DGM-MAT API in the background; no dashboard or autonomous workers.'
$Shortcut.Save()
Write-Output "INSTALLED: $ShortcutPath"
Write-Output "TARGET: $PythonW"
Write-Output "BACKUP: $BackupPath"
