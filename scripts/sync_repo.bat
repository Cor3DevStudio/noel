@echo off
setlocal EnableDelayedExpansion

rem Resolve repo root (this script lives in scripts\)
set "REPO_ROOT=%~dp0.."
cd /d "%REPO_ROOT%"

git --version >nul 2>&1
if errorlevel 1 (
    echo  [SYNC] Git is not installed — skipping remote update check.
    exit /b 0
)

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    echo  [SYNC] Not a git repository — skipping remote update check.
    exit /b 0
)

echo  [SYNC] Checking for new commits...
git fetch origin --quiet 2>nul
if errorlevel 1 (
    echo  [WARN] Could not reach remote. Continuing with local copy.
    exit /b 0
)

for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "BRANCH=%%b"
for /f "delims=" %%c in ('git rev-list --count HEAD..@{u} 2^>nul') do set "BEHIND=%%c"

if not defined BEHIND set "BEHIND=0"
if not defined BRANCH (
    echo  [WARN] Could not detect current branch. Skipping pull.
    exit /b 0
)

if "!BEHIND!"=="0" (
    echo  [SYNC] Already up to date ^(!BRANCH!^).
    exit /b 0
)

echo  [SYNC] !BEHIND! new commit^(s^) on origin/!BRANCH!. Pulling...

rem Runtime log files change on every app launch and must not block pulls
if exist "logs\clinic.log" (
    git restore --worktree "logs\clinic.log" >nul 2>&1
)

git pull --ff-only origin "!BRANCH!"
if errorlevel 1 (
    echo  [WARN] Pull failed ^(local changes or merge conflict^). Using current local copy.
    exit /b 0
)

echo  [SYNC] Repository updated successfully.
exit /b 0
