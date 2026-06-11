@echo off
setlocal
cd /d "%~dp0"
title Hospital Management System
color 0B

echo.
echo  ================================================================
echo   CLINIC MANAGEMENT SYSTEM
echo  ================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Install Python 3.10+ from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo  [1/3] Installing Python dependencies...
echo.
python -m pip install --upgrade pip
if errorlevel 1 (
    color 0C
    echo  [ERROR] Failed to upgrade pip.
    pause
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    color 0C
    echo  [ERROR] Failed to install dependencies from requirements.txt
    pause
    exit /b 1
)

echo.
echo  [2/3] Setting up database (create if missing, seed defaults)...
echo.
python setup_clinic.py
if errorlevel 1 (
    color 0C
    echo.
    echo  [ERROR] Database setup failed.
    echo  Ensure MySQL is running and review config\settings.py
    echo.
    pause
    exit /b 1
)

echo.
echo  [3/3] Launching application...
echo.
python main.py

if errorlevel 1 (
    color 0C
    echo.
    echo  [ERROR] Application exited with an error.
    if exist "logs\clinic.log" (
        echo  Last log lines:
        powershell -NoProfile -Command "Get-Content 'logs\clinic.log' -Tail 30"
    )
    echo.
    pause
)

endlocal
