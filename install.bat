@echo off
chcp 65001 > nul
title BTQ Wallet — Install

echo.
echo  ==========================================
echo    BTQ Wallet — Windows Installation
echo  ==========================================
echo.

REM Find Python
set PYTHON=
where python >nul 2>&1 && set PYTHON=python && goto :found
where py >nul 2>&1 && set PYTHON=py && goto :found
echo  [ERROR] Python 3.9+ not found. Get it from https://www.python.org
pause & exit /b 1
:found
echo  [OK] Python found (%PYTHON%).

REM Venv
if not exist ".venv\Scripts\python.exe" (
    echo  Creating virtual environment...
    %PYTHON% -m venv .venv
    echo  [OK] Virtual environment created.
)

REM Dependencies
echo  Installing dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip -q --disable-pip-version-check
.venv\Scripts\python.exe -m pip install -r requirements.txt -q --disable-pip-version-check
echo  [OK] Dependencies installed.

REM Shortcut — run the app briefly to trigger shortcut creation, then exit
echo  Creating desktop shortcut...
.venv\Scripts\python.exe -c "import platform_utils, json, os; s={}; platform_utils.create_shortcut(os.path.abspath('simple_wallet_gui.py'), os.path.abspath('.venv/Scripts/python.exe'), os.path.abspath('btq_wallet.png'), s, lambda x: None)"
echo  [OK] Setup complete.

echo.
echo  ==========================================
echo    Installation complete!
echo    Launch with:  launch.bat
echo  ==========================================
echo.
pause
