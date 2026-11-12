@echo off
setlocal
set "PACKAGE_ROOT=%~dp0"
set "UPDATER=%PACKAGE_ROOT%scripts\install_dgm_mat_update.ps1"

if not exist "%UPDATER%" (
    echo DGM-MAT update package is incomplete.
    echo Missing: "%UPDATER%"
    pause
    exit /b 2
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%UPDATER%" -PackageRoot "%PACKAGE_ROOT%"
set "RESULT=%ERRORLEVEL%"

if not "%RESULT%"=="0" (
    echo.
    echo DGM-MAT update did not complete. No automatic process termination was attempted.
    echo Review the message above and keep the existing installation.
    pause
    exit /b %RESULT%
)

echo.
echo DGM-MAT update completed. The runtime remains stopped until you launch it.
pause
exit /b 0
