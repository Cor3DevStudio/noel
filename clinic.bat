@echo off
setlocal enabledelayedexpansion
title Hospital Management System
color 0B

echo.
echo  ================================================================
echo   CLINIC MANAGEMENT SYSTEM - Starting Up...
echo  ================================================================
echo.

REM ── 1. Check Python ──────────────────────────────────────────────
echo  [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Please install Python 3.10+ from https://python.org
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%V in ('python --version 2^>^&1') do set PY_VER=%%V
echo  [OK] %PY_VER%
echo.

REM ── 2. Install / Update Dependencies ────────────────────────────
echo  [2/4] Installing dependencies...

REM -- Repair pip first (handles corrupt pip installations)
echo  Repairing pip...
curl -sSL https://bootstrap.pypa.io/get-pip.py -o "%TEMP%\get-pip.py" >nul 2>&1
if exist "%TEMP%\get-pip.py" (
    python "%TEMP%\get-pip.py" --quiet --force-reinstall >nul 2>&1
    del "%TEMP%\get-pip.py" >nul 2>&1
    echo  [OK] pip repaired.
) else (
    python -m ensurepip --upgrade >nul 2>&1
    echo  [OK] pip bootstrapped via ensurepip.
)

REM -- Now install packages
python -m pip install -r requirements.txt
if errorlevel 1 (
    color 0C
    echo.
    echo  [ERROR] Failed to install dependencies.
    echo  Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)
echo  [OK] Dependencies ready.
echo.

REM ── 3. Setup Database ─────────────────────────────────────────────
echo  [3/4] Setting up database...
python setup_db.py
if errorlevel 1 (
    color 0C
    echo.
    echo  [ERROR] Database setup failed.
    echo  Make sure MySQL / XAMPP is running, then try again.
    echo  Check config\settings.py for DB_HOST, DB_USER, DB_PASSWORD.
    echo.
    pause
    exit /b 1
)
echo  [OK] Database ready.
echo.

REM ── 4. Open Logs in a separate window ────────────────────────────
echo  [4/4] Opening log watcher...
if exist "logs\clinic.log" (
    start "Clinic Logs" powershell -NoProfile -NoExit -Command ^
        "Write-Host 'CLINIC LOGS - Press Ctrl+C to close' -ForegroundColor Cyan; Get-Content 'logs\clinic.log' -Tail 30 -Wait"
)

REM ── Launch Application ────────────────────────────────────────────
echo.
color 0A
echo  ================================================================
echo   All checks passed. Launching application...
echo   Default login:  admin / admin123
echo  ================================================================
echo.

python main.py

REM ── On crash: show error ──────────────────────────────────────────
if errorlevel 1 (
    color 0C
    echo.
    echo  ================================================================
    echo   [ERROR] Application crashed. Showing last 50 log lines:
    echo  ================================================================
    echo.
    if exist "logs\clinic.log" (
        powershell -NoProfile -Command "Get-Content 'logs\clinic.log' -Tail 50"
    )
    echo.
    pause
)

endlocal
