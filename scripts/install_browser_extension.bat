@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_browser_extension.ps1"
if errorlevel 1 (
  echo.
  echo Browser extension installation failed. The previous backup, if any, was preserved.
  pause
  exit /b 1
)
echo.
pause
