@echo off
setlocal
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo Installing Black Git Iran dependencies...
python -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Install failed.
    pause
    exit /b 1
)
echo.
echo Done. You can close this window.
pause
