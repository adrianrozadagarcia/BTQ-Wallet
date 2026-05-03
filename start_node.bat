@echo off
chcp 65001 > nul
title BTQ Node - Testnet

set BTQD=C:\Users\Adri\Desktop\v0.3.0-testnet-win64.zip\btqd.exe
set DATADIR=%APPDATA%\BTQ

echo.
echo  =========================================
echo    BTQ Node - Testnet
echo  =========================================
echo.

tasklist /FI "IMAGENAME eq btqd.exe" 2>nul | find /I "btqd.exe" >nul
if %errorlevel% equ 0 (
    echo  [OK] El nodo BTQ ya esta en ejecucion.
    echo.
    pause
    exit /b 0
)

if not exist "%BTQD%" (
    echo  [ERROR] No se encontro btqd.exe
    echo  Ruta: %BTQD%
    echo.
    pause
    exit /b 1
)

echo  Iniciando nodo BTQ (testnet)...
echo  DataDir: %DATADIR%
echo.  Nota: ejecutando en modo no-daemon (requerido en Windows)
echo.

start "BTQ Node" /MIN "%BTQD%" -testnet -nodaemon -datadir="%DATADIR%"

echo  [OK] Nodo iniciado. Espera unos segundos...
echo.
timeout /t 6 /nobreak > nul

tasklist /FI "IMAGENAME eq btqd.exe" 2>nul | find /I "btqd.exe" >nul
if %errorlevel% equ 0 (
    echo  [OK] btqd.exe esta corriendo.
    echo.
    echo  Ahora puedes conectar la BTQ Wallet.
) else (
    echo  [!] El nodo no parece estar corriendo.
    echo      Revisa %APPDATA%\BTQ\test\debug.log
)

echo.
pause