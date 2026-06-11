@echo off
setlocal enabledelayedexpansion
title Clinic CMS - First-Time Setup
color 0B

echo.
echo  ================================================================
echo   CLINIC MANAGEMENT SYSTEM - Setup
echo  ================================================================
echo.

echo  [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)
for /f "tokens=*" %%V in ('python --version 2^>^&1') do echo  [OK] %%V
echo.

echo  [2/3] Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    color 0C
    echo  [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo.> ".deps_installed"
echo  [OK] Dependencies ready.
echo.

echo  [3/3] Setting up database...
python setup_db.py
if errorlevel 1 (
    color 0C
    echo  [ERROR] Database setup failed.
    echo  Ensure MySQL / XAMPP is running and check config\settings.py
    pause
    exit /b 1
)
echo  [OK] Database ready.
echo.

color 0A
echo  ================================================================
echo   Setup complete. Use clinic.bat to launch the app.
echo   Default login: admin / admin123
echo.
echo   Optional demo data: python scripts/seed_demo.py
echo  ================================================================
echo.
pause
endlocal
