@echo off
setlocal
cd /d "%~dp0"
echo Z-Research v0.9.4 - Windows local launcher
if not exist ".venv\Scripts\python.exe" (
  echo Creating local Python environment...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Python 3 not found. Install Python 3.11 or 3.12 with Python Launcher.
    pause
    exit /b 1
  )
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 ( echo Dependency installation failed. & pause & exit /b 1 )
echo Open http://127.0.0.1:8765 in your browser
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8765
if errorlevel 1 pause
