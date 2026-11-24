@echo off
setlocal
set "ROOT=%~dp0"
set "SEAT=%~1"
if "%SEAT%"=="" (
  echo Usage: start_agent.bat ^<red^|white^|spectator^|referee^> [relay-url invitation-code]
  exit /b 2
)

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

if not "%~4"=="" (
  echo Usage: start_agent.bat ^<red^|white^|spectator^|referee^> [relay-url invitation-code]
  exit /b 2
)
if not "%~2"=="" if "%~3"=="" (
  echo Usage: start_agent.bat ^<red^|white^|spectator^|referee^> [relay-url invitation-code]
  exit /b 2
)
if not "%~2"=="" (
  %PYTHON% -B "%ROOT%scripts\mcp_stdio_server.py" --seat "%SEAT%" --connect "%~2" --code "%~3"
  exit /b %errorlevel%
)
%PYTHON% -B "%ROOT%scripts\mcp_stdio_server.py" --seat "%SEAT%"
