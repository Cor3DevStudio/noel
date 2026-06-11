@echo off
setlocal
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
    echo  Install Python 3.10+ from https://python.org
    echo  First-time setup: run clinic-setup.bat
    echo.
    pause
    exit /b 1
)

if not exist ".deps_installed" (
    color 0E
    echo  [!] Dependencies not installed yet.
    echo      Run clinic-setup.bat once, then use clinic.bat daily.
    echo.
    pause
    exit /b 1
)

echo  Launching application...
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
