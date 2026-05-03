@echo off
chcp 65001 > nul
title BTQ Wallet — Build

echo.
echo  ==========================================
echo    BTQ Wallet — Building standalone .exe
echo  ==========================================
echo.

REM ---------- Find Python ----------
set PYTHON=
where python >nul 2>&1
if %errorlevel% equ 0 ( set PYTHON=python & goto :found_python )
where py >nul 2>&1
if %errorlevel% equ 0 ( set PYTHON=py & goto :found_python )

echo  [ERROR] Python not found. Install Python 3.9+ from https://www.python.org
pause & exit /b 1

:found_python
echo  [OK] Python found (%PYTHON%).

REM ---------- Virtual environment ----------
if not exist ".venv\Scripts\python.exe" (
    echo  Creating virtual environment...
    %PYTHON% -m venv .venv
)

REM ---------- Install dependencies ----------
echo  Installing dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip -q --disable-pip-version-check
.venv\Scripts\python.exe -m pip install -r requirements.txt -q --disable-pip-version-check
.venv\Scripts\python.exe -m pip install pyinstaller -q --disable-pip-version-check

REM ---------- Build ----------
echo  Running PyInstaller...
.venv\Scripts\pyinstaller.exe BTQWallet.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Build failed.
    pause & exit /b 1
)

echo.
echo  ==========================================
echo    Build complete!
echo    Output: dist\BTQWallet.exe
echo  ==========================================
echo.
echo  You can distribute dist\BTQWallet.exe — no Python required.
echo.
pause
