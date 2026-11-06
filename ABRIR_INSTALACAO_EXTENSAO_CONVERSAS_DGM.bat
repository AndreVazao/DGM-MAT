@echo off
setlocal
set "ROOT=%~dp0"
set "EXTENSION_DIR=%ROOT%extensions\dgm-mat-conversation-archive"
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"

if not exist "%EXTENSION_DIR%\manifest.json" (
  echo ERROR: DGM-MAT Chrome extension folder not found.
  pause
  exit /b 1
)

if exist "%CHROME%" (
  start "" "%CHROME%" "chrome://extensions"
) else (
  start "" "chrome://extensions"
)

start "" explorer.exe "%EXTENSION_DIR%"

echo.
echo DGM-MAT Conversation Archive is ready to load.
echo In Chrome: enable Developer mode, click Load unpacked, and select the folder opened in Explorer.
echo Review and approve the Chrome history permission.
echo Do not load this extension into a different Chrome profile.
echo.
endlocal
