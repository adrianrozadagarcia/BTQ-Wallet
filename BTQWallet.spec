# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for BTQ Wallet
# Build with:  pyinstaller BTQWallet.spec --clean

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

hidden = (
    collect_submodules('PyQt5')
    + collect_submodules('qrcode')
    + collect_submodules('cryptography')
    + [
        'qrcode.image.pil',
        'PIL._imaging',
        'pkg_resources.py2_compat',
    ]
)

datas = collect_data_files('qrcode') + collect_data_files('cryptography') + [('src/platform_utils.py', '.')]

a = Analysis(
    ['src/simple_wallet_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'email', 'html', 'http', 'xml',
              'pydoc', 'doctest', 'difflib', 'pickle'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BTQWallet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no terminal window on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
