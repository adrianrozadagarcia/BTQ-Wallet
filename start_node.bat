@echo off
setlocal EnableExtensions
chcp 65001 > nul
title BTQ Node - Testnet

REM Resolve btqd.exe: same folder as this script, then ~/.local/bin style, then PATH.
set "SCRIPT_DIR=%~dp0"
set "BTQD="

if exist "%SCRIPT_DIR%btqd.exe" (
    set "BTQD=%SCRIPT_DIR%btqd.exe"
    goto :have_btqd
)
if exist "%USERPROFILE%\.local\bin\btqd.exe" (
    set "BTQD=%USERPROFILE%\.local\bin\btqd.exe"
    goto :have_btqd
)
for /f "delims=" %%i in ('where btqd.exe 2^>nul') do (
    set "BTQD=%%i"
    goto :have_btqd
)

:have_btqd
set "DATADIR=%APPDATA%\BTQ"

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

if not defined BTQD (
    echo  [ERROR] No se encontro btqd.exe
    echo.
    echo  Descargalo desde https://github.com/btq-ag/btq-core/releases
    echo  y colocalo junto a este script ^(btqd.exe^) o en %USERPROFILE%\.local\bin\
    echo  o anade la carpeta que contiene btqd.exe al PATH.
    echo.
    pause
    exit /b 1
)

if not exist "%BTQD%" (
    echo  [ERROR] No se encontro btqd.exe
    echo  Ruta: %BTQD%
    echo.
    pause
    exit /b 1
)

echo  Usando: %BTQD%
echo.

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
    echo      Revisa %APPDATA%\BTQ\testnet\debug.log
)

echo.
pause
