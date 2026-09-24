@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title Black Git Iran

echo.
echo  ================================
echo    BLACK GIT IRAN - Launcher
echo  ================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python was not found in PATH.
    echo  Install Python 3.10+ from https://www.python.org
    echo  and check "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

set "NEED_INSTALL=0"
python -c "import playwright" >nul 2>&1
if errorlevel 1 set "NEED_INSTALL=1"

if not exist "requirements.txt" set "NEED_INSTALL=1"
if not exist ".bgi_deps_ok" set "NEED_INSTALL=1"

REM re-run install when requirements.txt is newer than marker
if exist "requirements.txt" if exist ".bgi_deps_ok" (
    python -c "import os,pathlib,sys; r=pathlib.Path('requirements.txt'); m=pathlib.Path('.bgi_deps_ok'); sys.exit(0 if r.stat().st_mtime > m.stat().st_mtime else 1)"
    if not errorlevel 1 goto :skip_install
    set "NEED_INSTALL=1"
)

:skip_install
if "%NEED_INSTALL%"=="1" (
    echo  Installing / updating dependencies...
    python -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo  [ERROR] pip install failed. Check internet / pip.
        echo.
        pause
        exit /b 1
    )
    echo ok>".bgi_deps_ok"
    echo  Dependencies ready.
    echo.
)

echo  Starting Black Git Iran...
echo.
python main.py
set "EXITCODE=%ERRORLEVEL%"

if not "%EXITCODE%"=="0" (
    echo.
    echo  ----------------------------------------
    echo  [ERROR] App exited with code %EXITCODE%.
    echo  Read the error message above.
    echo  ----------------------------------------
    echo.
    pause
)

endlocal
exit /b %EXITCODE%
