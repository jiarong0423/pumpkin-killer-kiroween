@echo off
setlocal
set "ROOT=%~dp0"
set "PORT=%PK_PORT%"
if "%PORT%"=="" set "PORT=8000"

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 (
  set "PYTHON=py -3"
) else (
  python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
  if errorlevel 1 (
    echo Python 3.10 or later is required: https://www.python.org/downloads/
    exit /b 1
  )
  set "PYTHON=python"
)

start "Pumpkin Killer" /B %PYTHON% -m http.server %PORT% --bind 127.0.0.1 --directory "%ROOT%"
start "" "http://127.0.0.1:%PORT%/"
echo Keep this window open while playing. Press Ctrl+C to stop the local server.
pause
