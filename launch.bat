@echo off
chcp 65001 > nul
title BTQ Wallet

echo.
echo  ==========================================
echo    BTQ Wallet - Iniciando...
echo  ==========================================
echo.

REM ---------- Buscar Python ----------
set PYTHON=
where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
    set PYTHON=python
    goto :found_python
)
where py >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2 delims= " %%v in ('py --version 2^>^&1') do set PYVER=%%v
    set PYTHON=py
    goto :found_python
)

echo  [ERROR] Python no encontrado.
echo.
echo  Instala Python 3.8+ desde:  https://www.python.org/downloads/
echo  Marca la opcion "Add Python to PATH" durante la instalacion.
echo.
pause
exit /b 1

:found_python
echo  [OK] Python %PYVER% encontrado.

REM ---------- Crear entorno virtual si no existe ----------
if not exist ".venv\Scripts\python.exe" (
    echo  Creando entorno virtual...
    %PYTHON% -m venv .venv
    if %errorlevel% neq 0 (
        echo  [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo  [OK] Entorno virtual creado.
)

REM ---------- Instalar / actualizar dependencias ----------
echo  Verificando dependencias...
.venv\Scripts\python.exe -m pip install --upgrade pip -q --disable-pip-version-check
.venv\Scripts\python.exe -m pip install -r requirements.txt -q --disable-pip-version-check
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] No se pudieron instalar las dependencias.
    echo  Comprueba tu conexion a internet e intentalo de nuevo.
    echo.
    pause
    exit /b 1
)
echo  [OK] Dependencias listas.
echo.

REM ---------- Lanzar la wallet ----------
echo  Abriendo BTQ Wallet...
echo.
.venv\Scripts\python.exe simple_wallet_gui.py

if %errorlevel% neq 0 (
    echo.
    echo  [!] La wallet cerro con un error (codigo %errorlevel%).
    pause
)
