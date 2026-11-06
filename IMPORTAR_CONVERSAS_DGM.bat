@echo off
setlocal
pushd "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scripts\import_chrome_conversation_archive.py
) else (
  python scripts\import_chrome_conversation_archive.py
)

set "RESULT=%errorlevel%"
if not "%RESULT%"=="0" (
  echo.
  echo Import finished with status %RESULT%. Review the output above.
  pause
)
popd
endlocal & exit /b %RESULT%
