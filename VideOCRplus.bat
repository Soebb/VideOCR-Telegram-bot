@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Running install.bat first...
    call "%~dp0install.bat"
    if errorlevel 1 exit /b 1
)

set PYTHONUTF8=1
".venv\Scripts\python.exe" "%~dp0gui.py" %*
