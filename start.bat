@echo off
setlocal

cd /d "%~dp0"

REM Find a usable Python 3 command.
where python >nul 2>nul
if not errorlevel 1 (
    set "PYTHON=python"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON=py -3"
    ) else (
        echo ERROR: Python 3 was not found. Install Python and add it to PATH.
        pause
        exit /b 1
    )
)

echo [setup] Installing Python requirements...
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python requirements.
    pause
    exit /b 1
)

echo [start] Launching Telegram bot...
%PYTHON% bot.py

set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo The bot exited with code %EXIT_CODE%.
)
pause
exit /b %EXIT_CODE%
