#!/usr/bin/env python3
"""
BTQ Wallet — Interfaz gráfica para Bitcoin Quantum
Requiere nodo BTQ Core en ejecución.
"""

import sys
import os
import json
import base64
import io
import subprocess
from datetime import datetime
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import hashlib
import secrets
import time
import platform

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
        QTabWidget, QMessageBox, QFileDialog, QGroupBox, QGridLayout,
        QHeaderView, QStatusBar, QComboBox, QInputDialog, QFrame,
        QSizePolicy, QAbstractItemView, QCheckBox, QSpinBox, QDoubleSpinBox,
        QDialog, QSystemTrayIcon, QMenu, QAction
    )
    from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QEvent
    from PyQt5.QtGui import QFont, QPixmap, QColor, QFontDatabase
except ImportError:
    print("PyQt5 no encontrado. Ejecuta launch.bat para instalar las dependencias.")
    sys.exit(1)

try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.padding import PKCS7
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend as _crypto_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Platform detection
# ─────────────────────────────────────────────────────────────────────────────

_SYS     = platform.system()          # 'Windows' | 'Linux' | 'Darwin'
_IS_WIN  = _SYS == 'Windows'
_BTQD_BIN = 'btqd.exe' if _IS_WIN else 'btqd'


def _default_datadir() -> str:
    if _IS_WIN:
        return os.path.join(os.environ.get('APPDATA', ''), 'BTQ')
    elif _SYS == 'Darwin':
        return os.path.expanduser('~/Library/Application Support/BTQ')
    else:
        return os.path.expanduser('~/.btq')


# ─────────────────────────────────────────────────────────────────────────────
# Colores y estilos
# ─────────────────────────────────────────────────────────────────────────────

G = {
    'bg':          '#050505',
    'surface':     '#0c110c',
    'surface2':    '#111811',
    'border':      '#1a2e1a',
    'border2':     '#0d1f0d',
    'green':       '#00e676',
    'green_hi':    '#69f0ae',
    'green_lo':    '#00a152',
    'green_dark':  '#003d1a',
    'text':        '#dcedc8',
    'text_muted':  '#4a7a4a',
    'orange':      '#ffab40',
    'red':         '#ff5252',
    'blue':        '#40c4ff',
}

STYLE = f"""
/* ── Base ── */
* {{
    outline: none;
}}
QMainWindow, QDialog {{
    background: {G['bg']};
}}
QWidget {{
    background: {G['bg']};
    color: {G['text']};
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}}

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1px solid {G['border']};
    background: {G['surface']};
    border-radius: 0 4px 4px 4px;
}}
QTabBar {{
    background: transparent;
}}
QTabBar::tab {{
    background: {G['surface2']};
    color: {G['text_muted']};
    border: 1px solid {G['border2']};
    border-bottom: none;
    padding: 7px 20px;
    margin-right: 1px;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QTabBar::tab:selected {{
    background: {G['surface']};
    color: {G['green']};
    border-color: {G['border']};
    border-bottom: 2px solid {G['green']};
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{
    color: {G['text']};
    background: {G['surface']};
}}

/* ── GroupBox ── */
QGroupBox {{
    border: 1px solid {G['border']};
    border-radius: 4px;
    margin-top: 14px;
    padding-top: 8px;
    background: {G['surface']};
    color: {G['text_muted']};
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: {G['green_lo']};
}}

/* ── Inputs ── */
QLineEdit, QComboBox {{
    background: {G['surface2']};
    border: 1px solid {G['border']};
    border-radius: 3px;
    padding: 7px 10px;
    color: {G['text']};
    selection-background-color: {G['green_dark']};
    selection-color: {G['green_hi']};
}}
QLineEdit:focus, QComboBox:focus {{
    border-color: {G['green']};
    background: #0a150a;
}}
QLineEdit::placeholder {{
    color: {G['text_muted']};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {G['green_lo']};
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background: {G['surface2']};
    border: 1px solid {G['border']};
    selection-background-color: {G['green_dark']};
    selection-color: {G['green']};
    padding: 4px;
}}

/* ── Buttons ── */
QPushButton {{
    background: {G['surface2']};
    color: {G['text']};
    border: 1px solid {G['border']};
    border-radius: 3px;
    padding: 7px 16px;
    font-size: 11px;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    background: {G['green_dark']};
    border-color: {G['green_lo']};
    color: {G['green_hi']};
}}
QPushButton:pressed {{
    background: {G['green_lo']};
    color: {G['bg']};
}}
QPushButton:disabled {{
    background: {G['surface2']};
    color: {G['text_muted']};
    border-color: {G['border2']};
}}
QPushButton#primary {{
    background: {G['green_dark']};
    border-color: {G['green_lo']};
    color: {G['green']};
    font-weight: bold;
    letter-spacing: 2px;
}}
QPushButton#primary:hover {{
    background: {G['green_lo']};
    color: {G['bg']};
}}
QPushButton#danger {{
    background: #1a0505;
    border-color: #4a1010;
    color: {G['red']};
}}
QPushButton#danger:hover {{
    background: #3a0a0a;
    border-color: {G['red']};
}}

/* ── Tables ── */
QTableWidget {{
    background: {G['surface']};
    alternate-background-color: {G['surface2']};
    border: 1px solid {G['border2']};
    gridline-color: {G['border2']};
    color: {G['text']};
    selection-background-color: {G['green_dark']};
    selection-color: {G['green_hi']};
}}
QTableWidget::item {{
    padding: 5px 8px;
    border: none;
}}
QTableWidget::item:selected {{
    background: {G['green_dark']};
    color: {G['green_hi']};
}}
QHeaderView::section {{
    background: {G['bg']};
    color: {G['text_muted']};
    border: none;
    border-bottom: 1px solid {G['border']};
    padding: 6px 8px;
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: {G['bg']};
    width: 6px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {G['border']};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {G['green_lo']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {G['bg']};
    height: 6px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {G['border']};
    border-radius: 3px;
}}

/* ── MessageBox ── */
QMessageBox {{
    background: {G['surface']};
}}
QMessageBox QLabel {{
    color: {G['text']};
    font-size: 13px;
}}

/* ── StatusBar ── */
QStatusBar {{
    background: {G['bg']};
    color: {G['text_muted']};
    border-top: 1px solid {G['border2']};
    font-size: 11px;
    padding: 2px 8px;
}}

/* ── InputDialog ── */
QInputDialog {{
    background: {G['surface']};
}}

/* ── CheckBox ── */
QCheckBox {{
    color: {G['text']};
    spacing: 6px;
    font-size: 12px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {G['border']};
    border-radius: 2px;
    background: {G['surface2']};
}}
QCheckBox::indicator:checked {{
    background: {G['green_dark']};
    border-color: {G['green_lo']};
}}
QCheckBox::indicator:hover {{
    border-color: {G['green']};
}}

/* ── SpinBox ── */
QSpinBox, QDoubleSpinBox {{
    background: {G['surface2']};
    border: 1px solid {G['border']};
    border-radius: 3px;
    padding: 5px 8px;
    color: {G['text']};
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {G['green']};
}}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: {G['surface']};
    border: none;
    width: 18px;
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Internationalisation
# ─────────────────────────────────────────────────────────────────────────────

__version__ = '1.2.0'

_LANG = 'en'
_LANGS = [('en', 'English'), ('es', 'Español'), ('ru', 'Русский'), ('zh', '中文')]
_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'btq_wallet_settings.json')

TRANSLATIONS: dict = {
    'en': {
        'tab_balance': 'BALANCE', 'tab_addresses': 'ADDRESSES',
        'tab_receive': 'RECEIVE', 'tab_send': 'SEND',
        'tab_transactions': 'TRANSACTIONS', 'tab_network': 'NETWORK',
        'tab_settings': 'SETTINGS',
        'btn_new_address': '+ NEW ADDRESS', 'btn_copy': 'COPY',
        'btn_refresh': 'REFRESH', 'btn_connect': 'CONNECT',
        'btn_autodetect': 'AUTO-DETECT', 'btn_disconnect': 'DISCONNECT',
        'btn_send_tx': 'SEND TRANSACTION', 'btn_max': 'MAX',
        'btn_export_keys': 'Export Keys', 'btn_backup_wallet': 'Backup wallet.dat',
        'btn_import_keys': 'Import Keys', 'btn_start_node': 'START NODE',
        'btn_stop_node': 'STOP NODE',
        'group_wallet_status': 'WALLET STATUS', 'group_backup': 'BACKUP',
        'group_receive': 'RECEIVE ADDRESS', 'group_send': 'NEW TRANSACTION',
        'group_rpc': 'BTQ NODE CONNECTION', 'group_node': 'BTQ NODE',
        'group_btqconf': 'MINIMUM btq.conf CONFIGURATION',
        'group_blockchain': 'BLOCKCHAIN', 'group_p2p': 'P2P NETWORK',
        'group_language': 'LANGUAGE', 'group_privacy': 'PRIVACY & SECURITY',
        'lbl_addresses': 'Addresses', 'lbl_network': 'Network',
        'lbl_txcount': 'Transactions', 'lbl_block': 'Current block',
        'lbl_recipient': 'Recipient', 'lbl_amount': 'Amount (BTQ)',
        'lbl_note': 'Note (optional)', 'lbl_host': 'Host', 'lbl_port': 'Port',
        'lbl_rpc_user': 'RPC User', 'lbl_rpc_pass': 'RPC Password',
        'lbl_blocks': 'Blocks', 'lbl_headers': 'Headers',
        'lbl_difficulty': 'Difficulty', 'lbl_sync': 'Synchronization',
        'lbl_last_block': 'Last block', 'lbl_connections': 'Connections',
        'lbl_node_version': 'Node version', 'lbl_hashrate': 'Network hash rate',
        'lbl_mempool': 'Mempool (txs)', 'lbl_language': 'Interface language',
        'lbl_hide_balance': 'Hide balance amounts',
        'lbl_clipboard_clear': 'Clear clipboard after copy (seconds, 0 = off)',
        'lbl_confirm_threshold': 'Confirm sends above (BTQ, 0 = always ask)',
        'ph_recipient': 'Recipient BTQ address', 'ph_amount': '0.00000000',
        'ph_note': 'Private comment on your node', 'ph_btqd': 'Path to btqd.exe',
        'col_address': 'ADDRESS', 'col_balance_btq': 'BALANCE BTQ',
        'col_received_btq': 'RECEIVED BTQ', 'col_txid': 'TXID',
        'col_type': 'TYPE', 'col_amount': 'AMOUNT', 'col_conf': 'CONF',
        'col_date': 'DATE',
        'node_running': 'Status: RUNNING', 'node_stopped': 'Status: STOPPED',
        'node_starting': 'Status: starting...', 'node_unknown': 'Status: unknown',
        'badge_no_conn': '⬤  NO CONNECTION', 'header_sub': ' QUANTUM WALLET',
        'status_config_found': 'Config detected: {path}',
        'status_no_config': 'btq.conf not found — configure in SETTINGS tab',
        'status_connected': 'Connected to BTQ node — {chain} block #{blocks}',
        'status_disconnected': 'Disconnected from node',
        'status_backup_done': 'Backup completed',
        'status_keys_imported': 'Keys imported — rescanning...',
        'dlg_no_conn': 'Connect to a BTQ node first.',
        'dlg_invalid_port': 'Invalid port.',
        'dlg_invalid_amount': 'Invalid amount. Enter a number greater than 0.',
        'dlg_insufficient': 'Insufficient balance.\nAvailable: {available:.8f} BTQ',
        'dlg_confirm_send': 'Send {amount:.8f} BTQ to:\n\n{addr}?',
        'dlg_confirm_large': 'Large transaction!\n\nSend {amount:.8f} BTQ to:\n\n{addr}?',
        'dlg_tx_sent': 'Transaction sent\n\nTXID:\n{txid}',
        'dlg_no_config': 'btq.conf not found in standard paths.\nEnter credentials manually.',
        'dlg_backup_done': 'wallet.dat copied to:\n{path}',
        'dlg_export_done': 'Keys saved to:\n{path}\n\nIMPORTANT: keep this file safe.',
        'dlg_import_confirm': 'Keys will be imported from:\n{path}\n\nThe node will rescan the blockchain (may take minutes).\nContinue?',
        'dlg_import_done': 'Keys imported. Rescanning blockchain...\nBalance will update in a few minutes.',
        'dlg_btqd_notfound': 'Enter or select the path to btqd.exe.',
        'dlg_node_blocked': 'Windows blocked btqd.exe.\n\nFix: right-click btqd.exe → Properties → "Unblock" → OK.\n\nThen try again.',
        'dlg_gen_addr': 'Label (optional):', 'dlg_label_msg': 'Label for {addr}:',
        'dlg_addr_generated': 'New address:\n\n{addr}',
        'tx_receive': 'receive', 'tx_send': 'send',
        'tx_generate': 'generate', 'tx_immature': 'immature',
        'pending': 'pending: {amount:.8f} BTQ',
        'no_pending': 'no pending transactions',
        'available_balance': 'Available balance: {amount:.8f} BTQ',
        'connected_badge': '⬤  {chain}  BLOCK #{blocks}',
        'connected_status': 'Connected  ·  network: {chain}  ·  block #{blocks}',
        'clipboard_cleared': 'Clipboard cleared',
        'copied': 'Copied: {text}',
        'btqconf_location': 'Location: {path}',
        'lock_title': 'WALLET LOCKED',
        'lock_prompt': 'Enter PIN to unlock',
        'lock_wrong_pin': 'Incorrect PIN — try again',
        'lock_set_pin': 'Set PIN',
        'lock_remove_pin': 'Remove PIN',
        'lock_enter_new_pin': 'New PIN:',
        'lock_confirm_pin': 'Confirm PIN:',
        'lock_pin_mismatch': 'PINs do not match.',
        'lock_pin_set': 'PIN set. Locks after {mins} min of inactivity.',
        'lock_pin_removed': 'PIN removed.',
        'lbl_lock_timeout': 'Auto-lock after (min, 0 = off)',
        'group_session_lock': 'SESSION LOCK',
        'export_encrypted': 'Encrypted Export (.btqenc)',
        'import_encrypted': 'Decrypt Backup (.btqenc)',
        'export_passphrase': 'Encryption passphrase:',
        'export_confirm_passphrase': 'Confirm passphrase:',
        'export_saved': 'Encrypted backup saved:\n{path}',
        'import_passphrase_prompt': 'Decryption passphrase:',
        'import_ok': 'Wallet restored from encrypted backup.',
        'export_mismatch': 'Passphrases do not match.',
        'crypto_unavailable': 'cryptography package not installed.\nRun: pip install cryptography',
        'node_hash_none': 'No hash stored — recorded on first launch.',
        'node_hash_stored': 'Expected SHA-256: {hash}',
        'node_hash_mismatch': 'btqd.exe hash changed!\n\nExpected:\n{expected}\n\nFound:\n{found}\n\nLaunch anyway?',
        'node_hash_reset': 'Reset Expected Hash',
        'node_hash_reset_done': 'Hash reset — new hash recorded on next launch.',
        'group_node_integrity': 'NODE INTEGRITY',
        'addr_reuse_warning': 'This address was used before. Ask for a fresh address.',
        'group_tor': 'PRIVACY NETWORK',
        'lbl_use_tor': 'Route traffic through Tor (SOCKS5)',
        'lbl_tor_proxy': 'Tor SOCKS5 proxy (host:port)',
        'tor_reachable': '⬤  Tor reachable',
        'tor_unreachable': '⬤  Tor not reachable at {proxy}',
        'tor_checking': 'Checking Tor…',
        'lbl_use_i2p': 'Route traffic through I2P (SAM bridge)',
        'lbl_i2p_sam': 'I2P SAM bridge (host:port)',
        'i2p_reachable': '⬤  I2P reachable',
        'i2p_unreachable': '⬤  I2P not reachable at {sam}',
        'i2p_checking': 'Checking I2P…',
        'lbl_warn_no_privacy': 'Warn before sending without Tor or I2P',
        'dlg_no_privacy': 'No anonymization active.\n\nYour IP address may be visible to the network.\n\nSend anyway?',
        'privacy_badge_direct': 'DIRECT',
        'privacy_badge_tor': 'TOR',
        'privacy_badge_i2p': 'I2P',
        'privacy_update_via_tor': 'Update check routed through Tor.',
        'privacy_update_direct': 'Update check uses direct connection (Tor/I2P inactive).',
        'group_coin_control': 'COIN CONTROL',
        'coin_control_hint': 'Select UTXOs to spend. Leave all unchecked to let the node choose automatically.',
        'btn_load_utxos': 'Refresh UTXOs',
        'btn_select_all': 'Select All',
        'btn_deselect_all': 'Deselect',
        'lbl_selected_utxos': 'Selected: {amount:.8f} BTQ  ({count} UTXO)',
        'lbl_no_utxos': 'No UTXOs — connect and refresh',
        'coin_control_insufficient': 'Selected UTXOs insufficient.\nSelected: {selected:.8f}\nNeeded: ~{needed:.8f} BTQ',
        'dlg_coin_control_send': 'Send {amount:.8f} BTQ to:\n{addr}\n\nInputs:  {selected:.8f} BTQ\nFee:     {fee:.8f} BTQ\nChange:  {change:.8f} BTQ',
        'settings_saved': 'Settings saved',
        # Wallet encryption
        'group_wallet_enc': 'WALLET ENCRYPTION',
        'wallet_enc_unencrypted': 'Not encrypted — wallet.dat is stored in plaintext on disk.',
        'wallet_enc_locked': 'Encrypted · locked',
        'wallet_enc_unlocked': 'Encrypted · unlocked',
        'btn_encrypt_wallet': 'Encrypt Wallet',
        'btn_unlock_wallet': 'Unlock',
        'btn_lock_wallet': 'Lock',
        'btn_change_passphrase': 'Change Passphrase',
        'dlg_enc_passphrase': 'Wallet passphrase:',
        'dlg_enc_confirm': 'Confirm passphrase:',
        'dlg_enc_mismatch': 'Passphrases do not match.',
        'dlg_enc_done': 'Wallet encrypted.\n\nThe node will restart — reconnect in a few seconds.',
        'dlg_enc_unlock_timeout': 'Unlock for how many seconds?',
        'dlg_enc_locked_send': 'Wallet is locked. Enter passphrase to unlock for sending:',
        'dlg_enc_unlocked': 'Wallet unlocked.',
        'dlg_enc_locked_ok': 'Wallet locked.',
        'dlg_enc_changed': 'Passphrase changed.',
        'dlg_enc_old_pass': 'Current passphrase:',
        'dlg_enc_new_pass': 'New passphrase:',
        # Fee selector
        'group_fee': 'TRANSACTION FEE',
        'fee_slow': 'Slow  (~24 blocks)',
        'fee_normal': 'Normal  (~6 blocks)',
        'fee_fast': 'Fast  (~2 blocks)',
        'fee_custom': 'Custom',
        'lbl_fee_estimate': 'Estimated fee: {fee:.8f} BTQ',
        'lbl_fee_rate': 'Fee rate (BTQ/kB):',
        # System tray
        'tray_tooltip': 'BTQ Wallet',
        'tray_open': 'Open Wallet',
        'tray_lock': 'Lock Wallet',
        'tray_quit': 'Quit',
        'tray_hidden': 'BTQ Wallet is running in the background.',
        'tray_new_tx': 'New transaction',
        'tray_received': 'Received {amount:.8f} BTQ',
        # Update check
        'update_available': 'New version available: {version}  —  ',
        'update_download': 'Download',
        'update_checking': 'Checking for updates…',
    },
    'es': {
        'tab_balance': 'BALANCE', 'tab_addresses': 'DIRECCIONES',
        'tab_receive': 'RECIBIR', 'tab_send': 'ENVIAR',
        'tab_transactions': 'TRANSACCIONES', 'tab_network': 'RED',
        'tab_settings': 'CONFIGURACIÓN',
        'btn_new_address': '+ NUEVA DIRECCIÓN', 'btn_copy': 'COPIAR',
        'btn_refresh': 'ACTUALIZAR', 'btn_connect': 'CONECTAR',
        'btn_autodetect': 'AUTO-DETECTAR', 'btn_disconnect': 'DESCONECTAR',
        'btn_send_tx': 'ENVIAR TRANSACCIÓN', 'btn_max': 'MÁX',
        'btn_export_keys': 'Exportar Claves', 'btn_backup_wallet': 'Backup wallet.dat',
        'btn_import_keys': 'Importar Claves', 'btn_start_node': 'INICIAR NODO',
        'btn_stop_node': 'DETENER NODO',
        'group_wallet_status': 'ESTADO DE LA WALLET', 'group_backup': 'COPIA DE SEGURIDAD',
        'group_receive': 'DIRECCIÓN DE RECEPCIÓN', 'group_send': 'NUEVA TRANSACCIÓN',
        'group_rpc': 'CONEXIÓN AL NODO BTQ', 'group_node': 'NODO BTQ',
        'group_btqconf': 'CONFIGURACIÓN MÍNIMA DE btq.conf',
        'group_blockchain': 'BLOCKCHAIN', 'group_p2p': 'RED P2P',
        'group_language': 'IDIOMA', 'group_privacy': 'PRIVACIDAD Y SEGURIDAD',
        'lbl_addresses': 'Direcciones', 'lbl_network': 'Red',
        'lbl_txcount': 'Transacciones', 'lbl_block': 'Bloque actual',
        'lbl_recipient': 'Destinatario', 'lbl_amount': 'Cantidad (BTQ)',
        'lbl_note': 'Nota (opcional)', 'lbl_host': 'Host', 'lbl_port': 'Puerto',
        'lbl_rpc_user': 'Usuario RPC', 'lbl_rpc_pass': 'Contraseña RPC',
        'lbl_blocks': 'Bloques', 'lbl_headers': 'Cabeceras',
        'lbl_difficulty': 'Dificultad', 'lbl_sync': 'Sincronización',
        'lbl_last_block': 'Último bloque', 'lbl_connections': 'Conexiones',
        'lbl_node_version': 'Versión nodo', 'lbl_hashrate': 'Hash rate red',
        'lbl_mempool': 'Mempool (txs)', 'lbl_language': 'Idioma de la interfaz',
        'lbl_hide_balance': 'Ocultar cantidades de balance',
        'lbl_clipboard_clear': 'Limpiar portapapeles tras copiar (segundos, 0=desactivado)',
        'lbl_confirm_threshold': 'Confirmar envíos superiores a (BTQ, 0=siempre)',
        'ph_recipient': 'Dirección BTQ del destinatario', 'ph_amount': '0.00000000',
        'ph_note': 'Comentario privado en tu nodo', 'ph_btqd': 'Ruta a btqd.exe',
        'col_address': 'DIRECCIÓN', 'col_balance_btq': 'BALANCE BTQ',
        'col_received_btq': 'RECIBIDO BTQ', 'col_txid': 'TXID',
        'col_type': 'TIPO', 'col_amount': 'CANTIDAD', 'col_conf': 'CONF',
        'col_date': 'FECHA',
        'node_running': 'Estado: CORRIENDO', 'node_stopped': 'Estado: DETENIDO',
        'node_starting': 'Estado: iniciando...', 'node_unknown': 'Estado: desconocido',
        'badge_no_conn': '⬤  SIN CONEXIÓN', 'header_sub': ' QUANTUM WALLET',
        'status_config_found': 'Config detectada: {path}',
        'status_no_config': 'No se encontró btq.conf — configura en la pestaña CONFIGURACIÓN',
        'status_connected': 'Conectado al nodo BTQ — {chain} bloque #{blocks}',
        'status_disconnected': 'Desconectado del nodo',
        'status_backup_done': 'Backup realizado',
        'status_keys_imported': 'Claves importadas — re-escaneando...',
        'dlg_no_conn': 'Conecta al nodo BTQ primero.',
        'dlg_invalid_port': 'Puerto inválido.',
        'dlg_invalid_amount': 'Cantidad inválida. Introduce un número mayor que 0.',
        'dlg_insufficient': 'Balance insuficiente.\nDisponible: {available:.8f} BTQ',
        'dlg_confirm_send': '¿Enviar {amount:.8f} BTQ a:\n\n{addr}?',
        'dlg_confirm_large': '¡Transacción grande!\n\n¿Enviar {amount:.8f} BTQ a:\n\n{addr}?',
        'dlg_tx_sent': 'Transacción enviada\n\nTXID:\n{txid}',
        'dlg_no_config': 'No se encontró btq.conf en las rutas estándar.\nIntroduce los datos manualmente.',
        'dlg_backup_done': 'wallet.dat copiado a:\n{path}',
        'dlg_export_done': 'Claves guardadas en:\n{path}\n\nIMPORTANTE: guarda este archivo en un lugar seguro.',
        'dlg_import_confirm': 'Se importarán las claves de:\n{path}\n\nEl nodo re-escaneará la blockchain (puede tardar minutos).\n¿Continuar?',
        'dlg_import_done': 'Claves importadas. Re-escaneando blockchain...\nEl balance se actualizará en unos minutos.',
        'dlg_btqd_notfound': 'Introduce o selecciona la ruta a btqd.exe.',
        'dlg_node_blocked': 'Windows bloqueó el inicio de btqd.exe.\n\nSolución: clic derecho en btqd.exe → Propiedades → "Desbloquear" → Aceptar.\n\nLuego vuelve a intentarlo.',
        'dlg_gen_addr': 'Etiqueta (opcional):', 'dlg_label_msg': 'Etiqueta para {addr}:',
        'dlg_addr_generated': 'Nueva dirección:\n\n{addr}',
        'tx_receive': 'recibir', 'tx_send': 'enviar',
        'tx_generate': 'generar', 'tx_immature': 'inmaduro',
        'pending': 'pendiente: {amount:.8f} BTQ',
        'no_pending': 'sin transacciones pendientes',
        'available_balance': 'Balance disponible: {amount:.8f} BTQ',
        'connected_badge': '⬤  {chain}  BLOQUE #{blocks}',
        'connected_status': 'Conectado  ·  red: {chain}  ·  bloque #{blocks}',
        'clipboard_cleared': 'Portapapeles limpiado',
        'copied': 'Copiado: {text}',
        'btqconf_location': 'Ubicación: {path}',
        'lock_title': 'WALLET BLOQUEADA',
        'lock_prompt': 'Introduce el PIN para desbloquear',
        'lock_wrong_pin': 'PIN incorrecto — inténtalo de nuevo',
        'lock_set_pin': 'Establecer PIN',
        'lock_remove_pin': 'Eliminar PIN',
        'lock_enter_new_pin': 'Nuevo PIN:',
        'lock_confirm_pin': 'Confirmar PIN:',
        'lock_pin_mismatch': 'Los PINs no coinciden.',
        'lock_pin_set': 'PIN establecido. Bloqueo tras {mins} min de inactividad.',
        'lock_pin_removed': 'PIN eliminado.',
        'lbl_lock_timeout': 'Bloqueo automático (min, 0 = desactivado)',
        'group_session_lock': 'BLOQUEO DE SESIÓN',
        'export_encrypted': 'Exportar cifrado (.btqenc)',
        'import_encrypted': 'Descifrar copia (.btqenc)',
        'export_passphrase': 'Frase de cifrado:',
        'export_confirm_passphrase': 'Confirmar frase:',
        'export_saved': 'Copia cifrada guardada:\n{path}',
        'import_passphrase_prompt': 'Frase de descifrado:',
        'import_ok': 'Wallet restaurada desde copia cifrada.',
        'export_mismatch': 'Las frases no coinciden.',
        'crypto_unavailable': 'Paquete cryptography no instalado.\nEjecuta: pip install cryptography',
        'node_hash_none': 'Sin hash almacenado — se registrará en el primer inicio.',
        'node_hash_stored': 'SHA-256 esperado: {hash}',
        'node_hash_mismatch': '¡Hash de btqd.exe cambiado!\n\nEsperado:\n{expected}\n\nEncontrado:\n{found}\n\n¿Continuar?',
        'node_hash_reset': 'Restablecer hash esperado',
        'node_hash_reset_done': 'Hash restablecido — se registrará en el próximo inicio.',
        'group_node_integrity': 'INTEGRIDAD DEL NODO',
        'addr_reuse_warning': 'Esta dirección ya fue usada. Solicita una dirección nueva.',
        'group_tor': 'RED DE PRIVACIDAD',
        'lbl_use_tor': 'Enrutar tráfico por Tor (SOCKS5)',
        'lbl_tor_proxy': 'Proxy SOCKS5 Tor (host:puerto)',
        'tor_reachable': '⬤  Tor accesible',
        'tor_unreachable': '⬤  Tor no accesible en {proxy}',
        'lbl_use_i2p': 'Enrutar tráfico por I2P (SAM bridge)',
        'lbl_i2p_sam': 'SAM bridge I2P (host:puerto)',
        'i2p_reachable': '⬤  I2P accesible',
        'i2p_unreachable': '⬤  I2P no accesible en {sam}',
        'lbl_warn_no_privacy': 'Avisar al enviar sin Tor o I2P activos',
        'dlg_no_privacy': 'Sin anonimización activa.\n\nTu IP puede ser visible en la red.\n\n¿Enviar de todas formas?',
        'privacy_badge_direct': 'DIRECTO',
        'privacy_badge_tor': 'TOR',
        'privacy_badge_i2p': 'I2P',
        'tor_checking': 'Verificando Tor...',
        'group_coin_control': 'COIN CONTROL',
        'coin_control_hint': 'Selecciona UTXOs a gastar. Sin selección, el nodo elige automáticamente.',
        'btn_load_utxos': 'Actualizar UTXOs',
        'btn_select_all': 'Seleccionar todo',
        'btn_deselect_all': 'Deseleccionar',
        'lbl_selected_utxos': 'Seleccionado: {amount:.8f} BTQ  ({count} UTXO)',
        'lbl_no_utxos': 'Sin UTXOs — conecta y actualiza',
        'coin_control_insufficient': 'UTXOs insuficientes.\nSeleccionado: {selected:.8f}\nNecesario: ~{needed:.8f} BTQ',
        'dlg_coin_control_send': 'Enviar {amount:.8f} BTQ a:\n{addr}\n\nEntradas: {selected:.8f} BTQ\nComisión: {fee:.8f} BTQ\nCambio:   {change:.8f} BTQ',
        'settings_saved': 'Configuración guardada',
        'group_wallet_enc': 'CIFRADO DE WALLET',
        'wallet_enc_unencrypted': 'Sin cifrar — wallet.dat se guarda en texto plano en disco.',
        'wallet_enc_locked': 'Cifrada · bloqueada',
        'wallet_enc_unlocked': 'Cifrada · desbloqueada',
        'btn_encrypt_wallet': 'Cifrar Wallet',
        'btn_unlock_wallet': 'Desbloquear',
        'btn_lock_wallet': 'Bloquear',
        'btn_change_passphrase': 'Cambiar Contraseña',
        'dlg_enc_passphrase': 'Contraseña de la wallet:',
        'dlg_enc_confirm': 'Confirmar contraseña:',
        'dlg_enc_mismatch': 'Las contraseñas no coinciden.',
        'dlg_enc_done': 'Wallet cifrada.\n\nEl nodo se reiniciará — reconecta en unos segundos.',
        'dlg_enc_unlock_timeout': '¿Desbloquear durante cuántos segundos?',
        'dlg_enc_locked_send': 'La wallet está bloqueada. Introduce la contraseña para desbloquear:',
        'dlg_enc_unlocked': 'Wallet desbloqueada.',
        'dlg_enc_locked_ok': 'Wallet bloqueada.',
        'dlg_enc_changed': 'Contraseña cambiada.',
        'dlg_enc_old_pass': 'Contraseña actual:',
        'dlg_enc_new_pass': 'Nueva contraseña:',
        'group_fee': 'COMISIÓN DE TRANSACCIÓN',
        'fee_slow': 'Lento  (~24 bloques)',
        'fee_normal': 'Normal  (~6 bloques)',
        'fee_fast': 'Rápido  (~2 bloques)',
        'fee_custom': 'Personalizado',
        'lbl_fee_estimate': 'Comisión estimada: {fee:.8f} BTQ',
        'lbl_fee_rate': 'Tasa de comisión (BTQ/kB):',
        'tray_tooltip': 'BTQ Wallet',
        'tray_open': 'Abrir Wallet',
        'tray_lock': 'Bloquear Wallet',
        'tray_quit': 'Salir',
        'tray_hidden': 'BTQ Wallet está ejecutándose en segundo plano.',
        'tray_new_tx': 'Nueva transacción',
        'tray_received': 'Recibido {amount:.8f} BTQ',
        'update_available': 'Nueva versión disponible: {version}  —  ',
        'update_download': 'Descargar',
        'update_checking': 'Buscando actualizaciones…',
    },
    'ru': {
        'tab_balance': 'БАЛАНС', 'tab_addresses': 'АДРЕСА',
        'tab_receive': 'ПОЛУЧИТЬ', 'tab_send': 'ОТПРАВИТЬ',
        'tab_transactions': 'ТРАНЗАКЦИИ', 'tab_network': 'СЕТЬ',
        'tab_settings': 'НАСТРОЙКИ',
        'btn_new_address': '+ НОВЫЙ АДРЕС', 'btn_copy': 'КОПИРОВАТЬ',
        'btn_refresh': 'ОБНОВИТЬ', 'btn_connect': 'ПОДКЛЮЧИТЬ',
        'btn_autodetect': 'АВТО-ОПРЕДЕЛЕНИЕ', 'btn_disconnect': 'ОТКЛЮЧИТЬ',
        'btn_send_tx': 'ОТПРАВИТЬ', 'btn_max': 'МАКС',
        'btn_export_keys': 'Экспорт ключей', 'btn_backup_wallet': 'Бэкап wallet.dat',
        'btn_import_keys': 'Импорт ключей', 'btn_start_node': 'ЗАПУСТИТЬ УЗЕЛ',
        'btn_stop_node': 'ОСТАНОВИТЬ УЗЕЛ',
        'group_wallet_status': 'СОСТОЯНИЕ КОШЕЛЬКА', 'group_backup': 'РЕЗЕРВНАЯ КОПИЯ',
        'group_receive': 'АДРЕС ДЛЯ ПОЛУЧЕНИЯ', 'group_send': 'НОВАЯ ТРАНЗАКЦИЯ',
        'group_rpc': 'ПОДКЛЮЧЕНИЕ К УЗЛУ BTQ', 'group_node': 'УЗЕЛ BTQ',
        'group_btqconf': 'МИНИМАЛЬНАЯ НАСТРОЙКА btq.conf',
        'group_blockchain': 'БЛОКЧЕЙН', 'group_p2p': 'P2P СЕТЬ',
        'group_language': 'ЯЗЫК', 'group_privacy': 'КОНФИДЕНЦИАЛЬНОСТЬ',
        'lbl_addresses': 'Адреса', 'lbl_network': 'Сеть',
        'lbl_txcount': 'Транзакции', 'lbl_block': 'Текущий блок',
        'lbl_recipient': 'Получатель', 'lbl_amount': 'Сумма (BTQ)',
        'lbl_note': 'Заметка (необязательно)', 'lbl_host': 'Хост', 'lbl_port': 'Порт',
        'lbl_rpc_user': 'Пользователь RPC', 'lbl_rpc_pass': 'Пароль RPC',
        'lbl_blocks': 'Блоки', 'lbl_headers': 'Заголовки',
        'lbl_difficulty': 'Сложность', 'lbl_sync': 'Синхронизация',
        'lbl_last_block': 'Последний блок', 'lbl_connections': 'Подключения',
        'lbl_node_version': 'Версия узла', 'lbl_hashrate': 'Хешрейт сети',
        'lbl_mempool': 'Мемпул (тх)', 'lbl_language': 'Язык интерфейса',
        'lbl_hide_balance': 'Скрыть суммы баланса',
        'lbl_clipboard_clear': 'Очищать буфер обмена (секунды, 0=выкл)',
        'lbl_confirm_threshold': 'Подтверждать отправку свыше (BTQ, 0=всегда)',
        'ph_recipient': 'BTQ адрес получателя', 'ph_amount': '0.00000000',
        'ph_note': 'Личный комментарий на узле', 'ph_btqd': 'Путь к btqd.exe',
        'col_address': 'АДРЕС', 'col_balance_btq': 'БАЛАНС BTQ',
        'col_received_btq': 'ПОЛУЧЕНО BTQ', 'col_txid': 'TXID',
        'col_type': 'ТИП', 'col_amount': 'СУММА', 'col_conf': 'ПОДТ',
        'col_date': 'ДАТА',
        'node_running': 'Статус: РАБОТАЕТ', 'node_stopped': 'Статус: ОСТАНОВЛЕН',
        'node_starting': 'Статус: запуск...', 'node_unknown': 'Статус: неизвестно',
        'badge_no_conn': '⬤  НЕТ СВЯЗИ', 'header_sub': ' QUANTUM WALLET',
        'status_config_found': 'Конфигурация найдена: {path}',
        'status_no_config': 'btq.conf не найден — настройте во вкладке НАСТРОЙКИ',
        'status_connected': 'Подключено к узлу BTQ — {chain} блок #{blocks}',
        'status_disconnected': 'Отключено от узла',
        'status_backup_done': 'Резервная копия создана',
        'status_keys_imported': 'Ключи импортированы — повторное сканирование...',
        'dlg_no_conn': 'Сначала подключитесь к узлу BTQ.',
        'dlg_invalid_port': 'Неверный порт.',
        'dlg_invalid_amount': 'Неверная сумма. Введите число больше 0.',
        'dlg_insufficient': 'Недостаточно средств.\nДоступно: {available:.8f} BTQ',
        'dlg_confirm_send': 'Отправить {amount:.8f} BTQ на:\n\n{addr}?',
        'dlg_confirm_large': 'Крупная транзакция!\n\nОтправить {amount:.8f} BTQ на:\n\n{addr}?',
        'dlg_tx_sent': 'Транзакция отправлена\n\nTXID:\n{txid}',
        'dlg_no_config': 'btq.conf не найден в стандартных путях.\nВведите данные вручную.',
        'dlg_backup_done': 'wallet.dat скопирован в:\n{path}',
        'dlg_export_done': 'Ключи сохранены в:\n{path}\n\nВАЖНО: храните этот файл в безопасном месте.',
        'dlg_import_confirm': 'Ключи будут импортированы из:\n{path}\n\nУзел выполнит повторное сканирование (может занять минуты).\nПродолжить?',
        'dlg_import_done': 'Ключи импортированы. Повторное сканирование блокчейна...\nБаланс обновится через несколько минут.',
        'dlg_btqd_notfound': 'Введите или выберите путь к btqd.exe.',
        'dlg_node_blocked': 'Windows заблокировал btqd.exe.\n\nРешение: правая кнопка на btqd.exe → Свойства → "Разблокировать" → ОК.\n\nПовторите попытку.',
        'dlg_gen_addr': 'Метка (необязательно):', 'dlg_label_msg': 'Метка для {addr}:',
        'dlg_addr_generated': 'Новый адрес:\n\n{addr}',
        'tx_receive': 'получение', 'tx_send': 'отправка',
        'tx_generate': 'добыча', 'tx_immature': 'незрелый',
        'pending': 'ожидание: {amount:.8f} BTQ',
        'no_pending': 'нет ожидающих транзакций',
        'available_balance': 'Доступный баланс: {amount:.8f} BTQ',
        'connected_badge': '⬤  {chain}  БЛОК #{blocks}',
        'connected_status': 'Подключено  ·  сеть: {chain}  ·  блок #{blocks}',
        'clipboard_cleared': 'Буфер очищен',
        'copied': 'Скопировано: {text}',
        'btqconf_location': 'Расположение: {path}',
        'lock_title': 'КОШЕЛЁК ЗАБЛОКИРОВАН',
        'lock_prompt': 'Введите PIN для разблокировки',
        'lock_wrong_pin': 'Неверный PIN — попробуйте снова',
        'lock_set_pin': 'Установить PIN',
        'lock_remove_pin': 'Удалить PIN',
        'lock_enter_new_pin': 'Новый PIN:',
        'lock_confirm_pin': 'Подтвердите PIN:',
        'lock_pin_mismatch': 'PIN-коды не совпадают.',
        'lock_pin_set': 'PIN установлен. Блокировка через {mins} мин неактивности.',
        'lock_pin_removed': 'PIN удалён.',
        'lbl_lock_timeout': 'Авто-блокировка (мин, 0 = выкл)',
        'group_session_lock': 'БЛОКИРОВКА СЕССИИ',
        'export_encrypted': 'Шифрованный экспорт (.btqenc)',
        'import_encrypted': 'Расшифровать копию (.btqenc)',
        'export_passphrase': 'Пароль шифрования:',
        'export_confirm_passphrase': 'Подтвердите пароль:',
        'export_saved': 'Шифрованная копия сохранена:\n{path}',
        'import_passphrase_prompt': 'Пароль расшифровки:',
        'import_ok': 'Кошелёк восстановлен из шифрованной копии.',
        'export_mismatch': 'Пароли не совпадают.',
        'crypto_unavailable': 'Пакет cryptography не установлен.\nВыполните: pip install cryptography',
        'node_hash_none': 'Хеш не сохранён — будет записан при первом запуске.',
        'node_hash_stored': 'Ожидаемый SHA-256: {hash}',
        'node_hash_mismatch': 'Хеш btqd.exe изменился!\n\nОжидаемый:\n{expected}\n\nНайденный:\n{found}\n\nЗапустить всё равно?',
        'node_hash_reset': 'Сбросить ожидаемый хеш',
        'node_hash_reset_done': 'Хеш сброшен — новый будет записан при следующем запуске.',
        'group_node_integrity': 'ЦЕЛОСТНОСТЬ УЗЛА',
        'addr_reuse_warning': 'Этот адрес уже использовался. Запросите новый адрес.',
        'group_tor': 'СЕТЬ ПРИВАТНОСТИ',
        'lbl_use_tor': 'Направить трафик через Tor (SOCKS5)',
        'lbl_tor_proxy': 'Прокси SOCKS5 Tor (хост:порт)',
        'tor_reachable': '⬤  Tor доступен',
        'tor_unreachable': '⬤  Tor недоступен по {proxy}',
        'lbl_use_i2p': 'Направить трафик через I2P (SAM bridge)',
        'lbl_i2p_sam': 'SAM bridge I2P (хост:порт)',
        'i2p_reachable': '⬤  I2P доступен',
        'i2p_unreachable': '⬤  I2P недоступен по {sam}',
        'lbl_warn_no_privacy': 'Предупреждать при отправке без Tor/I2P',
        'dlg_no_privacy': 'Анонимизация не активна.\n\nВаш IP может быть виден сети.\n\nОтправить?',
        'privacy_badge_direct': 'ПРЯМОЙ',
        'privacy_badge_tor': 'TOR',
        'privacy_badge_i2p': 'I2P',
        'tor_checking': 'Проверка Tor...',
        'group_coin_control': 'COIN CONTROL',
        'coin_control_hint': 'Выберите UTXOs для трат. Без выбора — узел определит автоматически.',
        'btn_load_utxos': 'Обновить UTXOs',
        'btn_select_all': 'Выбрать все',
        'btn_deselect_all': 'Снять выбор',
        'lbl_selected_utxos': 'Выбрано: {amount:.8f} BTQ  ({count} UTXO)',
        'lbl_no_utxos': 'Нет UTXOs — подключитесь и обновите',
        'coin_control_insufficient': 'Недостаточно UTXOs.\nВыбрано: {selected:.8f}\nНужно: ~{needed:.8f} BTQ',
        'dlg_coin_control_send': 'Отправить {amount:.8f} BTQ на:\n{addr}\n\nВходы:    {selected:.8f} BTQ\nКомиссия: {fee:.8f} BTQ\nСдача:    {change:.8f} BTQ',
        'settings_saved': 'Настройки сохранены',
        'group_wallet_enc': 'ШИФРОВАНИЕ КОШЕЛЬКА',
        'wallet_enc_unencrypted': 'Не зашифрован — wallet.dat хранится в открытом виде.',
        'wallet_enc_locked': 'Зашифрован · заблокирован',
        'wallet_enc_unlocked': 'Зашифрован · разблокирован',
        'btn_encrypt_wallet': 'Зашифровать',
        'btn_unlock_wallet': 'Разблокировать',
        'btn_lock_wallet': 'Заблокировать',
        'btn_change_passphrase': 'Сменить пароль',
        'dlg_enc_passphrase': 'Пароль кошелька:',
        'dlg_enc_confirm': 'Подтвердите пароль:',
        'dlg_enc_mismatch': 'Пароли не совпадают.',
        'dlg_enc_done': 'Кошелёк зашифрован.\n\nУзел перезапустится — переподключитесь через несколько секунд.',
        'dlg_enc_unlock_timeout': 'Разблокировать на сколько секунд?',
        'dlg_enc_locked_send': 'Кошелёк заблокирован. Введите пароль для разблокировки:',
        'dlg_enc_unlocked': 'Кошелёк разблокирован.',
        'dlg_enc_locked_ok': 'Кошелёк заблокирован.',
        'dlg_enc_changed': 'Пароль изменён.',
        'dlg_enc_old_pass': 'Текущий пароль:',
        'dlg_enc_new_pass': 'Новый пароль:',
        'group_fee': 'КОМИССИЯ ТРАНЗАКЦИИ',
        'fee_slow': 'Медленно  (~24 блока)',
        'fee_normal': 'Нормально  (~6 блоков)',
        'fee_fast': 'Быстро  (~2 блока)',
        'fee_custom': 'Вручную',
        'lbl_fee_estimate': 'Примерная комиссия: {fee:.8f} BTQ',
        'lbl_fee_rate': 'Ставка комиссии (BTQ/кБ):',
        'tray_tooltip': 'BTQ Wallet',
        'tray_open': 'Открыть',
        'tray_lock': 'Заблокировать',
        'tray_quit': 'Выход',
        'tray_hidden': 'BTQ Wallet работает в фоновом режиме.',
        'tray_new_tx': 'Новая транзакция',
        'tray_received': 'Получено {amount:.8f} BTQ',
        'update_available': 'Доступна новая версия: {version}  —  ',
        'update_download': 'Скачать',
        'update_checking': 'Проверка обновлений…',
    },
    'zh': {
        'tab_balance': '余额', 'tab_addresses': '地址',
        'tab_receive': '接收', 'tab_send': '发送',
        'tab_transactions': '交易', 'tab_network': '网络',
        'tab_settings': '设置',
        'btn_new_address': '+ 新建地址', 'btn_copy': '复制',
        'btn_refresh': '刷新', 'btn_connect': '连接',
        'btn_autodetect': '自动检测', 'btn_disconnect': '断开',
        'btn_send_tx': '发送交易', 'btn_max': '最大',
        'btn_export_keys': '导出密钥', 'btn_backup_wallet': '备份 wallet.dat',
        'btn_import_keys': '导入密钥', 'btn_start_node': '启动节点',
        'btn_stop_node': '停止节点',
        'group_wallet_status': '钱包状态', 'group_backup': '备份',
        'group_receive': '接收地址', 'group_send': '新建交易',
        'group_rpc': 'BTQ节点连接', 'group_node': 'BTQ节点',
        'group_btqconf': 'btq.conf 最小配置',
        'group_blockchain': '区块链', 'group_p2p': 'P2P网络',
        'group_language': '语言', 'group_privacy': '隐私与安全',
        'lbl_addresses': '地址', 'lbl_network': '网络',
        'lbl_txcount': '交易', 'lbl_block': '当前区块',
        'lbl_recipient': '收款方', 'lbl_amount': '金额 (BTQ)',
        'lbl_note': '备注（可选）', 'lbl_host': '主机', 'lbl_port': '端口',
        'lbl_rpc_user': 'RPC用户', 'lbl_rpc_pass': 'RPC密码',
        'lbl_blocks': '区块', 'lbl_headers': '区块头',
        'lbl_difficulty': '难度', 'lbl_sync': '同步进度',
        'lbl_last_block': '最新区块', 'lbl_connections': '连接数',
        'lbl_node_version': '节点版本', 'lbl_hashrate': '网络算力',
        'lbl_mempool': '内存池(笔)', 'lbl_language': '界面语言',
        'lbl_hide_balance': '隐藏余额',
        'lbl_clipboard_clear': '复制后清空剪贴板（秒，0=关闭）',
        'lbl_confirm_threshold': '确认大额发送（BTQ，0=始终）',
        'ph_recipient': 'BTQ收款地址', 'ph_amount': '0.00000000',
        'ph_note': '节点上的私人备注', 'ph_btqd': 'btqd.exe路径',
        'col_address': '地址', 'col_balance_btq': '余额 BTQ',
        'col_received_btq': '收入 BTQ', 'col_txid': '交易ID',
        'col_type': '类型', 'col_amount': '金额', 'col_conf': '确认',
        'col_date': '日期',
        'node_running': '状态: 运行中', 'node_stopped': '状态: 已停止',
        'node_starting': '状态: 启动中...', 'node_unknown': '状态: 未知',
        'badge_no_conn': '⬤  未连接', 'header_sub': ' 量子钱包',
        'status_config_found': '已检测到配置: {path}',
        'status_no_config': '未找到 btq.conf — 请在设置标签页中配置',
        'status_connected': '已连接到BTQ节点 — {chain} 区块 #{blocks}',
        'status_disconnected': '已断开节点连接',
        'status_backup_done': '备份完成',
        'status_keys_imported': '密钥已导入 — 重新扫描中...',
        'dlg_no_conn': '请先连接到BTQ节点。',
        'dlg_invalid_port': '无效端口。',
        'dlg_invalid_amount': '无效金额。请输入大于0的数字。',
        'dlg_insufficient': '余额不足。\n可用: {available:.8f} BTQ',
        'dlg_confirm_send': '发送 {amount:.8f} BTQ 到:\n\n{addr}?',
        'dlg_confirm_large': '大额交易!\n\n发送 {amount:.8f} BTQ 到:\n\n{addr}?',
        'dlg_tx_sent': '交易已发送\n\n交易ID:\n{txid}',
        'dlg_no_config': '未找到标准路径中的 btq.conf。\n请手动输入凭据。',
        'dlg_backup_done': 'wallet.dat 已复制到:\n{path}',
        'dlg_export_done': '密钥已保存到:\n{path}\n\n重要：请妥善保管此文件。',
        'dlg_import_confirm': '将从以下路径导入密钥:\n{path}\n\n节点将重新扫描区块链（可能需要几分钟）。\n继续?',
        'dlg_import_done': '密钥已导入。正在重新扫描区块链...\n余额将在几分钟内更新。',
        'dlg_btqd_notfound': '请输入或选择 btqd.exe 的路径。',
        'dlg_node_blocked': 'Windows阻止了btqd.exe。\n\n解决方法: 右键点击btqd.exe → 属性 → 解除锁定 → 确定。\n\n然后重试。',
        'dlg_gen_addr': '标签（可选）:', 'dlg_label_msg': '{addr} 的标签:',
        'dlg_addr_generated': '新建地址:\n\n{addr}',
        'tx_receive': '接收', 'tx_send': '发送',
        'tx_generate': '挖矿', 'tx_immature': '未成熟',
        'pending': '待确认: {amount:.8f} BTQ',
        'no_pending': '无待处理交易',
        'available_balance': '可用余额: {amount:.8f} BTQ',
        'connected_badge': '⬤  {chain}  区块 #{blocks}',
        'connected_status': '已连接  ·  网络: {chain}  ·  区块 #{blocks}',
        'clipboard_cleared': '剪贴板已清空',
        'copied': '已复制: {text}',
        'btqconf_location': '位置: {path}',
        'lock_title': '钱包已锁定',
        'lock_prompt': '输入PIN码解锁',
        'lock_wrong_pin': 'PIN码错误 — 请重试',
        'lock_set_pin': '设置PIN码',
        'lock_remove_pin': '删除PIN码',
        'lock_enter_new_pin': '新PIN码：',
        'lock_confirm_pin': '确认PIN码：',
        'lock_pin_mismatch': 'PIN码不匹配。',
        'lock_pin_set': 'PIN码已设置。{mins}分钟不活动后锁定。',
        'lock_pin_removed': 'PIN码已删除。',
        'lbl_lock_timeout': '自动锁定（分钟，0=关闭）',
        'group_session_lock': '会话锁定',
        'export_encrypted': '加密导出 (.btqenc)',
        'import_encrypted': '解密备份 (.btqenc)',
        'export_passphrase': '加密口令：',
        'export_confirm_passphrase': '确认口令：',
        'export_saved': '加密备份已保存：\n{path}',
        'import_passphrase_prompt': '解密口令：',
        'import_ok': '钱包已从加密备份恢复。',
        'export_mismatch': '口令不匹配。',
        'crypto_unavailable': 'cryptography包未安装。\n运行：pip install cryptography',
        'node_hash_none': '未存储哈希 — 首次启动时记录。',
        'node_hash_stored': '预期 SHA-256: {hash}',
        'node_hash_mismatch': 'btqd.exe哈希已更改！\n\n预期：\n{expected}\n\n发现：\n{found}\n\n仍要启动？',
        'node_hash_reset': '重置预期哈希',
        'node_hash_reset_done': '哈希已重置 — 下次启动时记录新哈希。',
        'group_node_integrity': '节点完整性',
        'addr_reuse_warning': '此地址之前已使用过。建议请求新地址。',
        'group_tor': '隐私网络',
        'lbl_use_tor': '通过Tor路由流量（SOCKS5）',
        'lbl_tor_proxy': 'Tor SOCKS5代理（主机:端口）',
        'tor_reachable': '⬤  Tor可连接',
        'tor_unreachable': '⬤  {proxy} 处Tor不可连接',
        'lbl_use_i2p': '通过I2P路由流量（SAM网桥）',
        'lbl_i2p_sam': 'I2P SAM网桥（主机:端口）',
        'i2p_reachable': '⬤  I2P可连接',
        'i2p_unreachable': '⬤  {sam} 处I2P不可连接',
        'lbl_warn_no_privacy': '发送前若无Tor/I2P则警告',
        'dlg_no_privacy': '未启用匿名化。\n\n您的IP地址可能对网络可见。\n\n仍然发送？',
        'privacy_badge_direct': '直连',
        'privacy_badge_tor': 'TOR',
        'privacy_badge_i2p': 'I2P',
        'tor_checking': '检查Tor中...',
        'group_coin_control': 'COIN CONTROL',
        'coin_control_hint': '选择要使用的UTXO。不选则由节点自动选择。',
        'btn_load_utxos': '刷新UTXO',
        'btn_select_all': '全选',
        'btn_deselect_all': '取消选择',
        'lbl_selected_utxos': '已选: {amount:.8f} BTQ  ({count} UTXO)',
        'lbl_no_utxos': '无UTXO — 请连接并刷新',
        'coin_control_insufficient': 'UTXO不足。\n已选: {selected:.8f}\n需要: ~{needed:.8f} BTQ',
        'dlg_coin_control_send': '发送 {amount:.8f} BTQ 到:\n{addr}\n\n输入:  {selected:.8f} BTQ\n手续费: {fee:.8f} BTQ\n找零:  {change:.8f} BTQ',
        'settings_saved': '设置已保存',
        'group_wallet_enc': '钱包加密',
        'wallet_enc_unencrypted': '未加密 — wallet.dat 以明文存储在磁盘上。',
        'wallet_enc_locked': '已加密 · 已锁定',
        'wallet_enc_unlocked': '已加密 · 已解锁',
        'btn_encrypt_wallet': '加密钱包',
        'btn_unlock_wallet': '解锁',
        'btn_lock_wallet': '锁定',
        'btn_change_passphrase': '更改密码',
        'dlg_enc_passphrase': '钱包密码:',
        'dlg_enc_confirm': '确认密码:',
        'dlg_enc_mismatch': '密码不匹配。',
        'dlg_enc_done': '钱包已加密。\n\n节点将重启 — 请几秒后重新连接。',
        'dlg_enc_unlock_timeout': '解锁多少秒?',
        'dlg_enc_locked_send': '钱包已锁定。请输入密码以解锁:',
        'dlg_enc_unlocked': '钱包已解锁。',
        'dlg_enc_locked_ok': '钱包已锁定。',
        'dlg_enc_changed': '密码已更改。',
        'dlg_enc_old_pass': '当前密码:',
        'dlg_enc_new_pass': '新密码:',
        'group_fee': '交易手续费',
        'fee_slow': '慢速  (~24区块)',
        'fee_normal': '普通  (~6区块)',
        'fee_fast': '快速  (~2区块)',
        'fee_custom': '自定义',
        'lbl_fee_estimate': '预估手续费: {fee:.8f} BTQ',
        'lbl_fee_rate': '手续费率 (BTQ/kB):',
        'tray_tooltip': 'BTQ Wallet',
        'tray_open': '打开钱包',
        'tray_lock': '锁定钱包',
        'tray_quit': '退出',
        'tray_hidden': 'BTQ Wallet 正在后台运行。',
        'tray_new_tx': '新交易',
        'tray_received': '收到 {amount:.8f} BTQ',
        'update_available': '有新版本: {version}  —  ',
        'update_download': '下载',
        'update_checking': '检查更新中…',
    },
}


def t(key: str, **kw) -> str:
    text = TRANSLATIONS.get(_LANG, TRANSLATIONS['en']).get(key)
    if text is None:
        text = TRANSLATIONS['en'].get(key, key)
    return text.format(**kw) if kw else text


def _load_app_settings() -> dict:
    defaults = {
        'language': 'en', 'hide_balance': False,
        'clipboard_clear_seconds': 30, 'confirm_threshold_btq': 0.0,
        'pin_hash': '', 'lock_timeout_minutes': 5, 'btqd_sha256': '',
        'use_tor': False, 'tor_proxy': '127.0.0.1:9050',
        'use_i2p': False, 'i2p_sam': '127.0.0.1:7656',
        'warn_no_privacy': True,
    }
    try:
        with open(_SETTINGS_PATH, encoding='utf-8') as f:
            data = json.load(f)
            defaults.update({k: data[k] for k in defaults if k in data})
    except (OSError, json.JSONDecodeError):
        pass
    return defaults


def _save_app_settings(settings: dict):
    try:
        with open(_SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        # Restrict file to current user only
        try:
            if _IS_WIN:
                import getpass
                user = getpass.getuser()
                subprocess.run(
                    ['icacls', _SETTINGS_PATH, '/inheritance:r', '/grant:r', f'{user}:RW'],
                    capture_output=True, creationflags=0x08000000, timeout=5
                )
            else:
                os.chmod(_SETTINGS_PATH, 0o600)
        except Exception:
            pass
    except OSError:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Detección de configuración BTQ
# ─────────────────────────────────────────────────────────────────────────────

def find_btq_configs() -> list:
    appdata = os.environ.get('APPDATA', '')
    home = os.path.expanduser('~')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(appdata, 'BTQ', 'btq.conf'),
        os.path.join(appdata, 'BTQ', 'test', 'btq.conf'),
        os.path.join(home, '.btq', 'btq.conf'),
        os.path.join(home, 'btq-data', 'btq.conf'),
        os.path.join(script_dir, 'btq.conf'),
    ]
    return [p for p in candidates if os.path.exists(p)]


def parse_btq_config(path: str) -> dict:
    cfg = {}
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, _, v = line.partition('=')
                    cfg[k.strip().lower()] = v.strip()
    except OSError:
        pass
    return cfg


def rpc_settings_from_config(cfg: dict) -> dict:
    is_test = cfg.get('testnet', '0') == '1'
    return {
        'host': '127.0.0.1',
        'port': int(cfg.get('rpcport', 18332 if is_test else 8332)),
        'user': cfg.get('rpcuser', ''),
        'password': cfg.get('rpcpassword', ''),
    }


def auto_detect_rpc() -> tuple:
    for path in find_btq_configs():
        cfg = parse_btq_config(path)
        if cfg.get('rpcuser') and cfg.get('rpcpassword'):
            return rpc_settings_from_config(cfg), path
    return None, None


# ─────────────────────────────────────────────────────────────────────────────
# Cliente RPC
# ─────────────────────────────────────────────────────────────────────────────

class BTQRPCError(Exception):
    pass


class BTQRPCClient:

    def __init__(self, host='127.0.0.1', port=8332, user='', password=''):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self._id = 0

    def _url(self):
        return f'http://{self.host}:{self.port}/'

    def _auth(self):
        token = base64.b64encode(f'{self.user}:{self.password}'.encode()).decode()
        return f'Basic {token}'

    def call(self, method: str, *params):
        self._id += 1
        payload = json.dumps({
            'jsonrpc': '1.0', 'id': self._id,
            'method': method, 'params': list(params),
        }).encode()
        req = Request(self._url(), data=payload,
                      headers={'Content-Type': 'application/json',
                                'Authorization': self._auth()})
        try:
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
        except HTTPError as e:
            body = e.read()
            try:
                err = json.loads(body).get('error', {})
                raise BTQRPCError(f"{err.get('code','')}: {err.get('message', str(e))}")
            except (json.JSONDecodeError, AttributeError):
                raise BTQRPCError(f'HTTP {e.code}: {e.reason}')
        except URLError as e:
            raise ConnectionError(
                f'Cannot connect to BTQ node ({self.host}:{self.port})\n{e.reason}')
        if data.get('error'):
            raise BTQRPCError(
                f"{data['error'].get('code','')}: {data['error'].get('message','RPC error')}")
        return data['result']

    def ensure_wallet_loaded(self):
        """Load 'default' wallet if no wallet is currently loaded."""
        try:
            loaded = self.call('listwallets')
            if loaded:
                return
        except BTQRPCError:
            pass
        try:
            wallets = self.call('listwalletdir')
            names = [w.get('name', '') for w in wallets.get('wallets', [])]
            target = names[0] if names else 'default'
            self.call('loadwallet', target)
        except BTQRPCError:
            try:
                self.call('createwallet', 'default')
            except BTQRPCError:
                pass

    # Info
    def get_blockchain_info(self):   return self.call('getblockchaininfo')
    def get_network_info(self):      return self.call('getnetworkinfo')
    def get_mining_info(self):       return self.call('getmininginfo')
    def get_wallet_info(self):       return self.call('getwalletinfo')

    # Balance
    def get_balance(self):           return float(self.call('getbalance'))
    def get_unconfirmed_balance(self): return float(self.call('getunconfirmedbalance'))

    # Direcciones
    def get_new_address(self, label=''):  return self.call('getnewaddress', label)
    def validate_address(self, addr):     return self.call('validateaddress', addr)

    def get_all_addresses(self) -> dict:
        """address -> {balance, received, label}"""
        addresses = {}
        try:
            for item in self.call('listreceivedbyaddress', 0, True, False):
                addresses[item['address']] = {
                    'balance': 0.0,
                    'received': float(item.get('amount', 0)),
                    'label': item.get('label', ''),
                }
        except BTQRPCError:
            pass
        try:
            for utxo in self.call('listunspent', 0):
                a = utxo['address']
                if a not in addresses:
                    addresses[a] = {'balance': 0.0, 'received': 0.0, 'label': ''}
                addresses[a]['balance'] += float(utxo['amount'])
        except BTQRPCError:
            pass
        return addresses

    # Transacciones
    def list_transactions(self, count=100):
        return self.call('listtransactions', '*', count, 0, True)

    def send_to_address(self, address: str, amount: float, comment='', conf_target: int = 6) -> str:
        return self.call('sendtoaddress', address, round(float(amount), 8),
                         comment, '', False, False, conf_target)

    def get_transaction(self, txid: str):
        return self.call('gettransaction', txid)

    # Backup
    def backup_wallet(self, path: str):   self.call('backupwallet', path)
    def dump_wallet(self, path: str):     self.call('dumpwallet', path)
    def import_wallet(self, path: str):   self.call('importwallet', path)

    # Coin control
    def list_unspent(self, min_conf=0):
        return self.call('listunspent', min_conf)

    def get_raw_change_address(self) -> str:
        return self.call('getrawchangeaddress')

    def create_raw_transaction(self, inputs: list, outputs: dict) -> str:
        return self.call('createrawtransaction', inputs, outputs)

    def sign_raw_transaction(self, hex_tx: str) -> dict:
        return self.call('signrawtransactionwithwallet', hex_tx)

    def send_raw_transaction(self, hex_tx: str) -> str:
        return self.call('sendrawtransaction', hex_tx)

    def estimate_smart_fee(self, conf_target: int = 6) -> float:
        try:
            result = self.call('estimatesmartfee', conf_target)
            rate = result.get('feerate', 0.0)
            return float(rate) if rate and rate > 0 else 0.0001
        except BTQRPCError:
            return 0.0001

    # Wallet encryption
    def get_wallet_info(self) -> dict:
        return self.call('getwalletinfo')

    def encrypt_wallet(self, passphrase: str):
        return self.call('encryptwallet', passphrase)

    def wallet_passphrase(self, passphrase: str, timeout: int = 300):
        return self.call('walletpassphrase', passphrase, timeout)

    def wallet_lock(self):
        return self.call('walletlock')

    def wallet_passphrase_change(self, old: str, new: str):
        return self.call('walletpassphrasechange', old, new)


# ─────────────────────────────────────────────────────────────────────────────
# Worker RPC (hilo separado para no bloquear la GUI)
# ─────────────────────────────────────────────────────────────────────────────

class _UpdateWorker(QThread):
    result = pyqtSignal(str)

    def __init__(self, socks5_proxy: str = ''):
        super().__init__()
        self._proxy = socks5_proxy  # 'host:port' or ''

    def run(self):
        import socket as _socket
        _orig_socket = _socket.socket
        try:
            if self._proxy:
                try:
                    import socks
                    host, port = self._proxy.rsplit(':', 1)
                    socks.set_default_proxy(socks.SOCKS5, host, int(port))
                    _socket.socket = socks.socksocket
                except ImportError:
                    pass  # PySocks not installed — fall through to direct

            url = 'https://api.github.com/repos/adrianrozadagarcia/BTQ-Wallet/releases/latest'
            req = Request(url, headers={'User-Agent': f'BTQWallet/{__version__}'})
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            self.result.emit(data.get('tag_name', ''))
        except Exception:
            self.result.emit('')
        finally:
            _socket.socket = _orig_socket


class RPCWorker(QThread):
    data_ready  = pyqtSignal(dict)
    rpc_error   = pyqtSignal(str)

    def __init__(self, rpc: BTQRPCClient, tasks: list):
        super().__init__()
        self.rpc = rpc
        self.tasks = tasks

    def run(self):
        result = {}
        try:
            if 'balance' in self.tasks:
                result['balance']      = self.rpc.get_balance()
                result['unconfirmed']  = self.rpc.get_unconfirmed_balance()
                result['walletinfo']   = self.rpc.get_wallet_info()
                result['chaininfo']    = self.rpc.get_blockchain_info()
            if 'addresses' in self.tasks:
                result['addresses']    = self.rpc.get_all_addresses()
            if 'transactions' in self.tasks:
                result['transactions'] = self.rpc.list_transactions(100)
            if 'network' in self.tasks:
                result['networkinfo']  = self.rpc.get_network_info()
                result['mininginfo']   = self.rpc.get_mining_info()
            if 'utxos' in self.tasks:
                result['utxos'] = self.rpc.list_unspent()
            self.data_ready.emit(result)
        except (BTQRPCError, ConnectionError) as e:
            self.rpc_error.emit(str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Caché local de etiquetas (NO guarda claves ni saldos)
# ─────────────────────────────────────────────────────────────────────────────

class WalletCache:
    def __init__(self, path='wallet_cache.json'):
        self.path = path
        self.labels: dict = {}
        self._load()

    def set_label(self, address: str, label: str):
        self.labels[address] = label
        self._save()

    def get_label(self, address: str) -> str:
        return self.labels.get(address, '')

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path) as f:
                    self.labels = json.load(f).get('labels', {})
            except (json.JSONDecodeError, KeyError, OSError):
                pass

    def _save(self):
        try:
            with open(self.path, 'w') as f:
                json.dump({'labels': self.labels}, f, indent=2)
        except OSError:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Widgets de UI reutilizables
# ─────────────────────────────────────────────────────────────────────────────

def _sep():
    """Línea separadora horizontal."""
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f'border: none; border-top: 1px solid {G["border2"]};')
    return line


def _lbl(text, color=None, size=12, bold=False, mono=False):
    """Label con estilo rápido."""
    w = QLabel(text)
    font = QFont('Consolas' if mono else 'Segoe UI', size)
    font.setBold(bold)
    w.setFont(font)
    if color:
        w.setStyleSheet(f'color: {color};')
    return w


def _btn(text, obj_name='', icon_char=''):
    b = QPushButton(f'{icon_char}  {text}' if icon_char else text)
    if obj_name:
        b.setObjectName(obj_name)
    return b


def _stat_row(layout, row, label_text, value_text='—', value_color=None):
    """Fila de stat en un grid layout."""
    lbl = _lbl(label_text, color=G['text_muted'], size=11)
    val = _lbl(value_text, color=value_color or G['text'], size=11, mono=True)
    val.setTextInteractionFlags(Qt.TextSelectableByMouse)
    layout.addWidget(lbl, row, 0)
    layout.addWidget(val, row, 1)
    return val


# ─────────────────────────────────────────────────────────────────────────────
# Ventana principal
# ─────────────────────────────────────────────────────────────────────────────

class WalletGUI(QMainWindow):

    def __init__(self):
        super().__init__()
        global _LANG
        self._app_settings = _load_app_settings()
        _LANG = self._app_settings.get('language', 'en')
        self._hide_balance = self._app_settings.get('hide_balance', False)
        self._clipboard_clear_secs = int(self._app_settings.get('clipboard_clear_seconds', 30))
        self._confirm_threshold = float(self._app_settings.get('confirm_threshold_btq', 0.0))
        self._clipboard_timer: Optional[QTimer] = None
        self._last_balance_data: dict = {}
        self.rpc: Optional[BTQRPCClient] = None
        self.cache   = WalletCache()
        self._connected  = False
        self._addresses  = {}
        self._worker: Optional[RPCWorker] = None
        self._locked = False
        self._used_addresses: set = set()
        self._last_activity = time.monotonic()
        self._last_tx_ids: set = set()
        self._wallet_enc_status: str = 'unencrypted'  # 'unencrypted'|'locked'|'unlocked'
        self._build_ui()
        self._setup_timer()
        self._setup_tray()
        QTimer.singleShot(3000, self._check_for_update)
        # Install event filter on the application to track user activity for idle lock
        QApplication.instance().installEventFilter(self)
        self._try_auto_connect()
        # Lock on startup if a PIN is configured
        if self._app_settings.get('pin_hash'):
            QTimer.singleShot(500, self._lock)

    # ──────────────────────────── Construcción UI ─────────────────────────

    def _build_ui(self):
        self.setWindowTitle(f'BTQ Wallet  v{__version__}')
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(STYLE)

        root = QWidget()
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self._build_header())
        vbox.addWidget(_sep())

        # Update banner — hidden until a new version is found
        self._update_banner = QWidget()
        self._update_banner.setStyleSheet(
            f'background: {G["orange"]}; padding: 0px;')
        banner_h = QHBoxLayout(self._update_banner)
        banner_h.setContentsMargins(12, 4, 12, 4)
        self._update_lbl = QLabel('')
        self._update_lbl.setStyleSheet('color: #000; font-size: 12px; font-weight: bold; background: transparent;')
        self._update_link = QPushButton(t('update_download'))
        self._update_link.setStyleSheet(
            'color: #000; background: transparent; border: 1px solid #000; '
            'border-radius: 3px; padding: 2px 10px; font-weight: bold; font-size: 12px;')
        self._update_link.setCursor(Qt.PointingHandCursor)
        self._update_link.clicked.connect(self._open_releases_page)
        banner_h.addWidget(self._update_lbl)
        banner_h.addWidget(self._update_link)
        banner_h.addStretch()
        self._update_banner.hide()
        vbox.addWidget(self._update_banner)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        vbox.addWidget(self.tabs)

        self._tab_balance()
        self._tab_addresses()
        self._tab_receive()
        self._tab_send()
        self._tab_transactions()
        self._tab_network()
        self._tab_settings()

        sb = QStatusBar()
        sb.setSizeGripEnabled(False)
        self.setStatusBar(sb)
        self._status_bar = sb
        self._set_status('Iniciando...')

        # Lock overlay — child of root, not part of any layout
        self._lock_overlay = self._build_lock_overlay(root)

        # Idle lock timer — checks every 15 seconds
        self._idle_timer = QTimer(self)
        self._idle_timer.timeout.connect(self._check_idle)
        self._idle_timer.start(15_000)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_lock_overlay') and self._lock_overlay:
            cw = self.centralWidget()
            if cw:
                self._lock_overlay.setGeometry(cw.rect())

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseMove, QEvent.KeyPress,
                            QEvent.MouseButtonPress, QEvent.Wheel):
            self._last_activity = time.monotonic()
        return False

    # ──────────────────────────── Lock overlay ────────────────────────────

    def _build_lock_overlay(self, parent: QWidget) -> QWidget:
        overlay = QWidget(parent)
        overlay.setGeometry(parent.rect())
        overlay.setStyleSheet(f'background: {G["bg"]};')

        v = QVBoxLayout(overlay)
        v.setAlignment(Qt.AlignCenter)
        v.setSpacing(14)

        title = _lbl(t('lock_title'), color=G['green'], size=20, bold=True, mono=True)
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)

        prompt = _lbl(t('lock_prompt'), color=G['text_muted'], size=12)
        prompt.setAlignment(Qt.AlignCenter)
        v.addWidget(prompt)

        self._lock_pin_input = QLineEdit()
        self._lock_pin_input.setEchoMode(QLineEdit.Password)
        self._lock_pin_input.setFixedWidth(280)
        self._lock_pin_input.setAlignment(Qt.AlignCenter)
        self._lock_pin_input.setPlaceholderText('● ● ● ●')
        self._lock_pin_input.returnPressed.connect(self._unlock_attempt)
        v.addWidget(self._lock_pin_input, 0, Qt.AlignHCenter)

        self._lock_error_lbl = _lbl('', color=G['red'], size=11)
        self._lock_error_lbl.setAlignment(Qt.AlignCenter)
        v.addWidget(self._lock_error_lbl)

        btn = _btn(t('lock_prompt'), obj_name='primary')
        btn.setFixedWidth(280)
        btn.clicked.connect(self._unlock_attempt)
        v.addWidget(btn, 0, Qt.AlignHCenter)

        overlay.hide()
        return overlay

    def _lock(self):
        if not self._app_settings.get('pin_hash'):
            return
        self._locked = True
        self._lock_pin_input.clear()
        self._lock_error_lbl.setText('')
        cw = self.centralWidget()
        if cw:
            self._lock_overlay.setGeometry(cw.rect())
        self._lock_overlay.show()
        self._lock_overlay.raise_()
        self._lock_pin_input.setFocus()

    def _unlock_attempt(self):
        pin = self._lock_pin_input.text()
        expected = self._app_settings.get('pin_hash', '')
        if hashlib.sha256(pin.encode()).hexdigest() == expected:
            self._locked = False
            self._lock_overlay.hide()
            self._lock_pin_input.clear()
            self._lock_error_lbl.setText('')
            self._last_activity = time.monotonic()
        else:
            self._lock_pin_input.clear()
            self._lock_error_lbl.setText(t('lock_wrong_pin'))
            QTimer.singleShot(2500, lambda: self._lock_error_lbl.setText(''))

    def _check_idle(self):
        if self._locked or not self._app_settings.get('pin_hash'):
            return
        timeout_mins = self._app_settings.get('lock_timeout_minutes', 5)
        if timeout_mins <= 0:
            return
        elapsed_mins = (time.monotonic() - self._last_activity) / 60.0
        if elapsed_mins >= timeout_mins:
            self._lock()

    def _set_pin(self):
        pin1, ok1 = QInputDialog.getText(
            self, t('lock_set_pin'), t('lock_enter_new_pin'), QLineEdit.Password)
        if not ok1 or not pin1:
            return
        pin2, ok2 = QInputDialog.getText(
            self, t('lock_set_pin'), t('lock_confirm_pin'), QLineEdit.Password)
        if not ok2:
            return
        if pin1 != pin2:
            QMessageBox.warning(self, t('lock_set_pin'), t('lock_pin_mismatch'))
            return
        self._app_settings['pin_hash'] = hashlib.sha256(pin1.encode()).hexdigest()
        timeout = getattr(self, '_spin_lock_timeout', None)
        mins = int(timeout.value()) if timeout else 5
        self._app_settings['lock_timeout_minutes'] = mins
        _save_app_settings(self._app_settings)
        self._set_status(t('lock_pin_set', mins=mins))
        self._update_lock_ui()

    def _remove_pin(self):
        self._app_settings['pin_hash'] = ''
        _save_app_settings(self._app_settings)
        self._set_status(t('lock_pin_removed'))
        self._update_lock_ui()

    def _update_lock_ui(self):
        has_pin = bool(self._app_settings.get('pin_hash'))
        if hasattr(self, '_btn_remove_pin'):
            self._btn_remove_pin.setEnabled(has_pin)

    def _build_header(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(52)
        w.setStyleSheet(f'background: {G["surface"]}; border-bottom: 1px solid {G["border2"]};')
        h = QHBoxLayout(w)
        h.setContentsMargins(16, 0, 16, 0)

        logo = _lbl('BTQ', color=G['green'], size=20, bold=True, mono=True)
        sub  = _lbl(t('header_sub'), color=G['text_muted'], size=11)
        h.addWidget(logo)
        h.addWidget(sub)
        h.addStretch()

        self._privacy_badge = QLabel(t('privacy_badge_direct'))
        self._privacy_badge.setStyleSheet(
            f'color: {G["text_muted"]}; font-size: 10px; letter-spacing: 2px;'
            f'padding: 4px 10px; background: {G["surface2"]}; border: 1px solid {G["border2"]}; border-radius: 3px;')
        h.addWidget(self._privacy_badge)
        h.addSpacing(8)

        self._badge = QLabel(t('badge_no_conn'))
        self._badge.setStyleSheet(
            f'color: {G["red"]}; font-size: 10px; letter-spacing: 2px;'
            f'padding: 4px 12px; background: #1a0505; border: 1px solid #3a0a0a; border-radius: 3px;')
        h.addWidget(self._badge)

        return w

    # ──────────────────────────── Tab: Balance ────────────────────────────

    def _tab_balance(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(12)

        # Hero balance
        hero = QWidget()
        hero.setStyleSheet(
            f'background: {G["surface2"]}; border: 1px solid {G["border"]}; border-radius: 4px;')
        hv = QVBoxLayout(hero)
        hv.setContentsMargins(24, 20, 24, 20)

        self._bal_main = _lbl('-.-------- BTQ', color=G['green'], size=32, bold=True, mono=True)
        self._bal_main.setAlignment(Qt.AlignCenter)
        self._bal_pending = _lbl('pendiente: -.-------- BTQ', color=G['orange'], size=11)
        self._bal_pending.setAlignment(Qt.AlignCenter)
        hv.addWidget(self._bal_main)
        hv.addWidget(self._bal_pending)
        v.addWidget(hero)

        # Stats grid
        stats = QGroupBox(t('group_wallet_status'))
        sg = QGridLayout(stats)
        sg.setColumnStretch(1, 1)
        sg.setColumnStretch(3, 1)

        sg.addWidget(_lbl(t('lbl_addresses'),  color=G['text_muted'], size=11), 0, 0)
        sg.addWidget(_lbl(t('lbl_network'),    color=G['text_muted'], size=11), 0, 2)
        sg.addWidget(_lbl(t('lbl_txcount'),    color=G['text_muted'], size=11), 1, 0)
        sg.addWidget(_lbl(t('lbl_block'),      color=G['text_muted'], size=11), 1, 2)
        self._s_addresses  = _lbl('—', color=G['text'], size=11, mono=True)
        self._s_txcount    = _lbl('—', color=G['text'], size=11, mono=True)
        self._s_chain      = _lbl('—', color=G['green'], size=11, mono=True)
        self._s_block      = _lbl('—', color=G['text'], size=11, mono=True)
        for lbl in (self._s_addresses, self._s_txcount, self._s_chain, self._s_block):
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        sg.addWidget(self._s_addresses, 0, 1)
        sg.addWidget(self._s_chain,     0, 3)
        sg.addWidget(self._s_txcount,   1, 1)
        sg.addWidget(self._s_block,     1, 3)
        v.addWidget(stats)

        # Backup
        backup = QGroupBox(t('group_backup'))
        bh = QHBoxLayout(backup)

        btn_dump   = _btn(t('btn_export_keys'),   obj_name='primary')
        btn_bk     = _btn(t('btn_backup_wallet'))
        btn_import = _btn(t('btn_import_keys'),   obj_name='danger')
        btn_enc    = _btn(t('export_encrypted'))
        btn_dec    = _btn(t('import_encrypted'))
        btn_dump.clicked.connect(self._export_wallet)
        btn_bk.clicked.connect(self._backup_wallet)
        btn_import.clicked.connect(self._import_wallet)
        btn_enc.clicked.connect(self._export_encrypted)
        btn_dec.clicked.connect(self._import_encrypted)
        bh.addWidget(btn_dump)
        bh.addWidget(btn_bk)
        bh.addWidget(btn_import)
        bh.addWidget(btn_enc)
        bh.addWidget(btn_dec)

        v.addWidget(backup)
        v.addStretch()
        self.tabs.addTab(w, t('tab_balance'))

    # ──────────────────────────── Tab: Direcciones ────────────────────────

    def _tab_addresses(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 16, 20, 16)

        toolbar = QHBoxLayout()
        btn_new = _btn(t('btn_new_address'), obj_name='primary')
        btn_new.clicked.connect(self._gen_address)
        toolbar.addWidget(btn_new)
        toolbar.addStretch()
        v.addLayout(toolbar)
        v.addSpacing(8)

        self._addr_table = QTableWidget()
        self._addr_table.setColumnCount(4)
        self._addr_table.setHorizontalHeaderLabels([t('col_address'), t('col_balance_btq'), t('col_received_btq'), ''])
        self._addr_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._addr_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._addr_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._addr_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self._addr_table.setColumnWidth(3, 72)
        self._addr_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._addr_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._addr_table.setAlternatingRowColors(True)
        self._addr_table.verticalHeader().setVisible(False)
        v.addWidget(self._addr_table)
        self.tabs.addTab(w, t('tab_addresses'))

    # ──────────────────────────── Tab: Recibir ────────────────────────────

    def _tab_receive(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 16, 20, 16)
        v.setAlignment(Qt.AlignTop)

        # Selector
        sel = QGroupBox(t('group_receive'))
        sh = QHBoxLayout(sel)
        self._recv_combo = QComboBox()
        self._recv_combo.setMinimumWidth(500)
        self._recv_combo.currentTextChanged.connect(self._refresh_qr)
        sh.addWidget(self._recv_combo)
        btn_copy = _btn(t('btn_copy'), obj_name='primary')
        btn_copy.setFixedWidth(90)
        btn_copy.clicked.connect(self._copy_recv_addr)
        sh.addWidget(btn_copy)
        v.addWidget(sel)
        v.addSpacing(8)

        # Dirección en texto
        self._recv_lbl = QLabel('—')
        self._recv_lbl.setFont(QFont('Consolas', 11))
        self._recv_lbl.setAlignment(Qt.AlignCenter)
        self._recv_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._recv_lbl.setWordWrap(True)
        self._recv_lbl.setStyleSheet(
            f'color: {G["green"]}; background: {G["surface2"]}; '
            f'border: 1px solid {G["border"]}; border-radius: 4px; padding: 12px 16px;')
        self._recv_lbl.setMinimumHeight(48)
        v.addWidget(self._recv_lbl)
        v.addSpacing(12)

        # QR
        self._qr_lbl = QLabel()
        self._qr_lbl.setAlignment(Qt.AlignCenter)
        self._qr_lbl.setMinimumSize(260, 260)
        if not QR_AVAILABLE:
            self._qr_lbl.setText('[ instala qrcode[pil] para ver el QR ]')
            self._qr_lbl.setStyleSheet(f'color: {G["text_muted"]}; font-style: italic;')
        v.addWidget(self._qr_lbl, alignment=Qt.AlignHCenter)
        v.addStretch()
        self.tabs.addTab(w, t('tab_receive'))

    # ──────────────────────────── Tab: Enviar ─────────────────────────────

    def _tab_send(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 16, 20, 16)

        form = QGroupBox(t('group_send'))
        fg = QGridLayout(form)
        fg.setSpacing(10)
        fg.setColumnStretch(1, 1)

        fg.addWidget(_lbl(t('lbl_recipient'), color=G['text_muted'], size=11), 0, 0)
        self._to_addr = QLineEdit()
        self._to_addr.setPlaceholderText(t('ph_recipient'))
        self._to_addr.textChanged.connect(self._check_address_reuse)
        fg.addWidget(self._to_addr, 0, 1)

        self._addr_reuse_lbl = QLabel('')
        self._addr_reuse_lbl.setWordWrap(True)
        self._addr_reuse_lbl.setStyleSheet(
            f'color: {G["orange"]}; background: #1a1200; '
            f'border: 1px solid #4a3000; border-radius: 3px; padding: 6px 10px; font-size: 11px;')
        self._addr_reuse_lbl.hide()
        fg.addWidget(self._addr_reuse_lbl, 1, 0, 1, 2)

        fg.addWidget(_lbl(t('lbl_amount'), color=G['text_muted'], size=11), 2, 0)
        amt_w = QWidget()
        amt_h = QHBoxLayout(amt_w)
        amt_h.setContentsMargins(0, 0, 0, 0)
        self._amount = QLineEdit()
        self._amount.setPlaceholderText('0.00000000')
        amt_h.addWidget(self._amount)
        btn_max = QPushButton(t('btn_max'))
        btn_max.setFixedWidth(52)
        btn_max.clicked.connect(self._set_max)
        amt_h.addWidget(btn_max)
        fg.addWidget(amt_w, 2, 1)

        fg.addWidget(_lbl(t('lbl_note'), color=G['text_muted'], size=11), 3, 0)
        self._send_note = QLineEdit()
        self._send_note.setPlaceholderText(t('ph_note'))
        fg.addWidget(self._send_note, 3, 1)

        v.addWidget(form)
        v.addSpacing(8)

        self._send_bal_lbl = _lbl(t('available_balance', amount=0.0), color=G['text_muted'], size=11)
        v.addWidget(self._send_bal_lbl)
        v.addSpacing(8)

        # ── Fee selector ──────────────────────────────────────────────────
        fee_box = QGroupBox(t('group_fee'))
        fee_grid = QGridLayout(fee_box)
        fee_grid.setSpacing(8)
        fee_grid.setColumnStretch(1, 1)

        self._fee_combo = QComboBox()
        for key in ('fee_slow', 'fee_normal', 'fee_fast', 'fee_custom'):
            self._fee_combo.addItem(t(key), key)
        self._fee_combo.setCurrentIndex(1)  # Normal by default
        self._fee_combo.currentIndexChanged.connect(self._on_fee_speed_changed)
        fee_grid.addWidget(_lbl(t('lbl_fee_rate') if False else '', color=G['text_muted'], size=11), 0, 0)
        fee_grid.addWidget(self._fee_combo, 0, 1, Qt.AlignLeft)

        self._fee_custom_spin = QDoubleSpinBox()
        self._fee_custom_spin.setDecimals(8)
        self._fee_custom_spin.setRange(0.00000001, 1.0)
        self._fee_custom_spin.setValue(0.0001)
        self._fee_custom_spin.setSingleStep(0.00001)
        self._fee_custom_spin.setFixedWidth(160)
        self._fee_custom_spin.hide()
        self._fee_custom_spin.valueChanged.connect(self._update_fee_estimate)
        fee_grid.addWidget(_lbl(t('lbl_fee_rate'), color=G['text_muted'], size=11), 1, 0)
        fee_grid.addWidget(self._fee_custom_spin, 1, 1, Qt.AlignLeft)

        self._fee_estimate_lbl = _lbl(t('lbl_fee_estimate', fee=0.0), color=G['green_lo'], size=11, mono=True)
        fee_grid.addWidget(self._fee_estimate_lbl, 2, 0, 1, 2)

        v.addWidget(fee_box)
        v.addSpacing(8)

        # ── Coin control ──────────────────────────────────────────────────
        cc_box = QGroupBox(t('group_coin_control'))
        ccv = QVBoxLayout(cc_box)
        ccv.setSpacing(6)

        cc_hint = _lbl(t('coin_control_hint'), color=G['text_muted'], size=10)
        cc_hint.setWordWrap(True)
        ccv.addWidget(cc_hint)

        self._utxo_table = QTableWidget()
        self._utxo_table.setColumnCount(4)
        self._utxo_table.setHorizontalHeaderLabels([
            '', t('col_address'), t('col_amount'), t('col_conf')])
        self._utxo_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self._utxo_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._utxo_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._utxo_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._utxo_table.setColumnWidth(0, 28)
        self._utxo_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._utxo_table.setSelectionMode(QAbstractItemView.NoSelection)
        self._utxo_table.setAlternatingRowColors(True)
        self._utxo_table.verticalHeader().setVisible(False)
        self._utxo_table.setMaximumHeight(160)
        ccv.addWidget(self._utxo_table)

        cc_toolbar = QHBoxLayout()
        btn_load_utxos  = _btn(t('btn_load_utxos'))
        btn_select_all  = _btn(t('btn_select_all'))
        btn_deselect    = _btn(t('btn_deselect_all'))
        btn_load_utxos.clicked.connect(lambda: self._start_worker(['utxos']))
        btn_select_all.clicked.connect(self._utxo_select_all)
        btn_deselect.clicked.connect(self._utxo_deselect_all)
        cc_toolbar.addWidget(btn_load_utxos)
        cc_toolbar.addWidget(btn_select_all)
        cc_toolbar.addWidget(btn_deselect)
        cc_toolbar.addStretch()
        self._utxo_selected_lbl = _lbl(
            t('lbl_selected_utxos', amount=0.0, count=0),
            color=G['green_lo'], size=11, mono=True)
        cc_toolbar.addWidget(self._utxo_selected_lbl)
        ccv.addLayout(cc_toolbar)

        v.addWidget(cc_box)
        v.addSpacing(8)

        btn_send = _btn(t('btn_send_tx'), obj_name='primary')
        btn_send.setMinimumHeight(42)
        btn_send.clicked.connect(self._send_tx)
        v.addWidget(btn_send)
        v.addStretch()
        self.tabs.addTab(w, t('tab_send'))

    # ──────────────────────────── Tab: Transacciones ──────────────────────

    def _tab_transactions(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 16, 20, 16)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        btn_refresh = _btn(t('btn_refresh'))
        btn_refresh.setFixedWidth(110)
        btn_refresh.clicked.connect(lambda: self._start_worker(['transactions']))
        toolbar.addWidget(btn_refresh)
        v.addLayout(toolbar)
        v.addSpacing(6)

        self._tx_table = QTableWidget()
        self._tx_table.setColumnCount(6)
        self._tx_table.setHorizontalHeaderLabels([
            t('col_txid'), t('col_type'), t('col_address'),
            t('col_amount'), t('col_conf'), t('col_date')])
        hh = self._tx_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self._tx_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tx_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tx_table.setAlternatingRowColors(True)
        self._tx_table.verticalHeader().setVisible(False)
        v.addWidget(self._tx_table)
        self.tabs.addTab(w, t('tab_transactions'))

    # ──────────────────────────── Tab: Red ───────────────────────────────

    def _tab_network(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 16, 20, 16)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        btn_r = _btn(t('btn_refresh'))
        btn_r.setFixedWidth(110)
        btn_r.clicked.connect(lambda: self._start_worker(['network']))
        toolbar.addWidget(btn_r)
        v.addLayout(toolbar)
        v.addSpacing(6)

        row_layout = QHBoxLayout()
        left = QVBoxLayout()

        chain_box = QGroupBox(t('group_blockchain'))
        cg = QGridLayout(chain_box)
        self._n = {}
        for i, (k, lkey) in enumerate([
            ('chain',       'lbl_network'),
            ('blocks',      'lbl_blocks'),
            ('headers',     'lbl_headers'),
            ('difficulty',  'lbl_difficulty'),
            ('sync',        'lbl_sync'),
            ('hash',        'lbl_last_block'),
        ]):
            cg.addWidget(_lbl(t(lkey), color=G['text_muted'], size=11), i, 0)
            val = _lbl('—', color=G['text'], size=11, mono=True)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            cg.addWidget(val, i, 1)
            self._n[k] = val
        left.addWidget(chain_box)
        left.addStretch()

        right = QVBoxLayout()
        net_box = QGroupBox(t('group_p2p'))
        ng = QGridLayout(net_box)
        for i, (k, lkey) in enumerate([
            ('connections', 'lbl_connections'),
            ('version',     'lbl_node_version'),
            ('hashrate',    'lbl_hashrate'),
            ('mempool',     'lbl_mempool'),
        ]):
            ng.addWidget(_lbl(t(lkey), color=G['text_muted'], size=11), i, 0)
            val = _lbl('—', color=G['text'], size=11, mono=True)
            ng.addWidget(val, i, 1)
            self._n[k] = val
        right.addWidget(net_box)
        right.addStretch()

        row_layout.addLayout(left)
        row_layout.addSpacing(12)
        row_layout.addLayout(right)
        v.addLayout(row_layout)
        self.tabs.addTab(w, t('tab_network'))

    # ──────────────────────────── Tab: Configuración ──────────────────────

    def _tab_settings(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(20, 16, 20, 16)

        # ── RPC connection ────────────────────────────────────────────────
        rpc_box = QGroupBox(t('group_rpc'))
        rg = QGridLayout(rpc_box)
        rg.setColumnStretch(1, 1)
        rg.setSpacing(10)

        for i, (lkey, attr, default, echo) in enumerate([
            ('lbl_host',     'rpc_host', '127.0.0.1', False),
            ('lbl_port',     'rpc_port', '8332',       False),
            ('lbl_rpc_user', 'rpc_user', '',           False),
            ('lbl_rpc_pass', 'rpc_pass', '',           True),
        ]):
            rg.addWidget(_lbl(t(lkey), color=G['text_muted'], size=11), i, 0)
            field = QLineEdit(default)
            if echo:
                field.setEchoMode(QLineEdit.Password)
            rg.addWidget(field, i, 1)
            setattr(self, attr, field)

        btn_row = QHBoxLayout()
        btn_connect    = _btn(t('btn_connect'),    obj_name='primary')
        btn_autodetect = _btn(t('btn_autodetect'))
        btn_disconnect = _btn(t('btn_disconnect'), obj_name='danger')
        btn_connect.clicked.connect(lambda: self._connect())
        btn_autodetect.clicked.connect(self._autodetect)
        btn_disconnect.clicked.connect(self._disconnect)
        btn_row.addWidget(btn_connect)
        btn_row.addWidget(btn_autodetect)
        btn_row.addWidget(btn_disconnect)
        btn_row.addStretch()
        rg.addLayout(btn_row, 4, 0, 1, 2)

        self._rpc_status = QLabel('')
        self._rpc_status.setWordWrap(True)
        self._rpc_status.setStyleSheet(
            f'color: {G["text_muted"]}; background: {G["surface2"]}; '
            f'border: 1px solid {G["border2"]}; border-radius: 3px; padding: 8px;')
        rg.addWidget(self._rpc_status, 5, 0, 1, 2)
        v.addWidget(rpc_box)

        # ── Node control ──────────────────────────────────────────────────
        node_box = QGroupBox(t('group_node'))
        ndg = QGridLayout(node_box)
        ndg.setColumnStretch(1, 1)
        ndg.setSpacing(10)

        ndg.addWidget(_lbl('btqd.exe', color=G['text_muted'], size=11), 0, 0)
        self._btqd_path = QLineEdit()
        self._btqd_path.setPlaceholderText(t('ph_btqd'))
        self._btqd_path.setText(self._find_btqd())
        ndg.addWidget(self._btqd_path, 0, 1)

        btn_browse = _btn('...')
        btn_browse.setFixedWidth(36)
        btn_browse.clicked.connect(self._browse_btqd)
        ndg.addWidget(btn_browse, 0, 2)

        node_btn_row = QHBoxLayout()
        btn_start_node = _btn(t('btn_start_node'), obj_name='primary')
        btn_stop_node  = _btn(t('btn_stop_node'),  obj_name='danger')
        btn_start_node.clicked.connect(self._start_node)
        btn_stop_node.clicked.connect(self._stop_node)
        node_btn_row.addWidget(btn_start_node)
        node_btn_row.addWidget(btn_stop_node)
        node_btn_row.addStretch()
        ndg.addLayout(node_btn_row, 1, 0, 1, 3)

        self._node_status = QLabel(t('node_unknown'))
        self._node_status.setStyleSheet(
            f'color: {G["text_muted"]}; background: {G["surface2"]}; '
            f'border: 1px solid {G["border2"]}; border-radius: 3px; padding: 8px;')
        ndg.addWidget(self._node_status, 2, 0, 1, 3)
        v.addWidget(node_box)

        # ── Node integrity ────────────────────────────────────────────────
        integrity_box = QGroupBox(t('group_node_integrity'))
        ig = QGridLayout(integrity_box)
        ig.setColumnStretch(0, 1)
        ig.setSpacing(8)

        stored_hash = self._app_settings.get('btqd_sha256', '')
        if stored_hash:
            hash_text = t('node_hash_stored', hash=stored_hash[:32] + '…')
        else:
            hash_text = t('node_hash_none')
        self._node_hash_lbl = QLabel(hash_text)
        self._node_hash_lbl.setFont(QFont('Consolas', 10))
        self._node_hash_lbl.setWordWrap(True)
        self._node_hash_lbl.setStyleSheet(
            f'color: {G["text_muted"]}; background: {G["surface2"]}; '
            f'border: 1px solid {G["border2"]}; border-radius: 3px; padding: 8px;')
        ig.addWidget(self._node_hash_lbl, 0, 0, 1, 2)

        btn_reset_hash = _btn(t('node_hash_reset'))
        btn_reset_hash.clicked.connect(self._reset_node_hash)
        ig.addWidget(btn_reset_hash, 1, 0, Qt.AlignLeft)

        v.addWidget(integrity_box)

        # ── Wallet encryption ─────────────────────────────────────────────
        enc_box = QGroupBox(t('group_wallet_enc'))
        eg = QGridLayout(enc_box)
        eg.setColumnStretch(0, 1)
        eg.setSpacing(8)

        self._enc_status_lbl = QLabel(t('wallet_enc_unencrypted'))
        self._enc_status_lbl.setWordWrap(True)
        self._enc_status_lbl.setStyleSheet(
            f'color: {G["orange"]}; background: {G["surface2"]}; '
            f'border: 1px solid {G["border2"]}; border-radius: 3px; padding: 8px; font-size: 11px;')
        eg.addWidget(self._enc_status_lbl, 0, 0, 1, 3)

        self._btn_encrypt    = _btn(t('btn_encrypt_wallet'))
        self._btn_unlock_enc = _btn(t('btn_unlock_wallet'))
        self._btn_lock_enc   = _btn(t('btn_lock_wallet'), obj_name='danger')
        self._btn_chg_pass   = _btn(t('btn_change_passphrase'))
        self._btn_encrypt.clicked.connect(self._encrypt_wallet)
        self._btn_unlock_enc.clicked.connect(self._unlock_wallet_dlg)
        self._btn_lock_enc.clicked.connect(self._lock_wallet_enc)
        self._btn_chg_pass.clicked.connect(self._change_passphrase)
        btn_enc_row = QHBoxLayout()
        btn_enc_row.addWidget(self._btn_encrypt)
        btn_enc_row.addWidget(self._btn_unlock_enc)
        btn_enc_row.addWidget(self._btn_lock_enc)
        btn_enc_row.addWidget(self._btn_chg_pass)
        btn_enc_row.addStretch()
        eg.addLayout(btn_enc_row, 1, 0, 1, 3)
        v.addWidget(enc_box)
        QTimer.singleShot(800, self._refresh_wallet_enc_ui)

        if hasattr(self, '_node_check_timer'):
            self._node_check_timer.stop()
        self._node_check_timer = QTimer(self)
        self._node_check_timer.timeout.connect(self._check_node_running)
        self._node_check_timer.start(5000)
        QTimer.singleShot(500, self._check_node_running)

        # ── Language ──────────────────────────────────────────────────────
        lang_box = QGroupBox(t('group_language'))
        lg = QHBoxLayout(lang_box)
        lg.addWidget(_lbl(t('lbl_language'), color=G['text_muted'], size=11))
        self._lang_combo = QComboBox()
        for code, name in _LANGS:
            self._lang_combo.addItem(name, code)
        cur_idx = next((i for i, (c, _) in enumerate(_LANGS) if c == _LANG), 0)
        self._lang_combo.blockSignals(True)
        self._lang_combo.setCurrentIndex(cur_idx)
        self._lang_combo.blockSignals(False)
        self._lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        lg.addWidget(self._lang_combo)
        lg.addStretch()
        v.addWidget(lang_box)

        # ── Privacy & Security ────────────────────────────────────────────
        priv_box = QGroupBox(t('group_privacy'))
        pg = QGridLayout(priv_box)
        pg.setColumnStretch(1, 1)
        pg.setSpacing(10)

        self._chk_hide_balance = QCheckBox(t('lbl_hide_balance'))
        self._chk_hide_balance.setChecked(self._hide_balance)
        self._chk_hide_balance.stateChanged.connect(self._on_hide_balance_changed)
        pg.addWidget(self._chk_hide_balance, 0, 0, 1, 2)

        pg.addWidget(_lbl(t('lbl_clipboard_clear'), color=G['text_muted'], size=11), 1, 0)
        self._spin_clipboard = QSpinBox()
        self._spin_clipboard.setRange(0, 300)
        self._spin_clipboard.setValue(self._clipboard_clear_secs)
        self._spin_clipboard.setFixedWidth(80)
        self._spin_clipboard.editingFinished.connect(self._save_privacy_settings)
        pg.addWidget(self._spin_clipboard, 1, 1, Qt.AlignLeft)

        pg.addWidget(_lbl(t('lbl_confirm_threshold'), color=G['text_muted'], size=11), 2, 0)
        self._spin_threshold = QDoubleSpinBox()
        self._spin_threshold.setRange(0.0, 21_000_000.0)
        self._spin_threshold.setDecimals(4)
        self._spin_threshold.setValue(self._confirm_threshold)
        self._spin_threshold.setFixedWidth(120)
        self._spin_threshold.editingFinished.connect(self._save_privacy_settings)
        pg.addWidget(self._spin_threshold, 2, 1, Qt.AlignLeft)

        v.addWidget(priv_box)

        # ── Session lock ──────────────────────────────────────────────────
        lock_box = QGroupBox(t('group_session_lock'))
        lg2 = QGridLayout(lock_box)
        lg2.setColumnStretch(1, 1)
        lg2.setSpacing(10)

        pin_btn_row = QHBoxLayout()
        btn_set_pin = _btn(t('lock_set_pin'), obj_name='primary')
        btn_set_pin.clicked.connect(self._set_pin)
        self._btn_remove_pin = _btn(t('lock_remove_pin'), obj_name='danger')
        self._btn_remove_pin.clicked.connect(self._remove_pin)
        self._btn_remove_pin.setEnabled(bool(self._app_settings.get('pin_hash')))
        pin_btn_row.addWidget(btn_set_pin)
        pin_btn_row.addWidget(self._btn_remove_pin)
        pin_btn_row.addStretch()
        lg2.addLayout(pin_btn_row, 0, 0, 1, 2)

        lg2.addWidget(_lbl(t('lbl_lock_timeout'), color=G['text_muted'], size=11), 1, 0)
        self._spin_lock_timeout = QSpinBox()
        self._spin_lock_timeout.setRange(0, 120)
        self._spin_lock_timeout.setValue(int(self._app_settings.get('lock_timeout_minutes', 5)))
        self._spin_lock_timeout.setFixedWidth(80)
        self._spin_lock_timeout.editingFinished.connect(self._save_lock_settings)
        lg2.addWidget(self._spin_lock_timeout, 1, 1, Qt.AlignLeft)

        v.addWidget(lock_box)

        # ── Privacy network (Tor + I2P) ───────────────────────────────────
        tor_box = QGroupBox(t('group_tor'))
        tg = QGridLayout(tor_box)
        tg.setColumnStretch(1, 1)
        tg.setSpacing(8)

        # Tor
        self._chk_tor = QCheckBox(t('lbl_use_tor'))
        self._chk_tor.setChecked(self._app_settings.get('use_tor', False))
        self._chk_tor.stateChanged.connect(self._on_tor_changed)
        tg.addWidget(self._chk_tor, 0, 0, 1, 2)

        tg.addWidget(_lbl(t('lbl_tor_proxy'), color=G['text_muted'], size=11), 1, 0)
        self._tor_proxy_field = QLineEdit()
        self._tor_proxy_field.setText(self._app_settings.get('tor_proxy', '127.0.0.1:9050'))
        self._tor_proxy_field.setFixedWidth(200)
        self._tor_proxy_field.editingFinished.connect(self._save_tor_settings)
        tg.addWidget(self._tor_proxy_field, 1, 1, Qt.AlignLeft)

        self._tor_status_lbl = QLabel('')
        self._tor_status_lbl.setStyleSheet(f'color: {G["text_muted"]}; font-size: 11px;')
        tg.addWidget(self._tor_status_lbl, 2, 0, 1, 2)

        # Separator
        sep_line = QFrame(); sep_line.setFrameShape(QFrame.HLine)
        sep_line.setStyleSheet(f'color: {G["border2"]};')
        tg.addWidget(sep_line, 3, 0, 1, 2)

        # I2P
        self._chk_i2p = QCheckBox(t('lbl_use_i2p'))
        self._chk_i2p.setChecked(self._app_settings.get('use_i2p', False))
        self._chk_i2p.stateChanged.connect(self._on_i2p_changed)
        tg.addWidget(self._chk_i2p, 4, 0, 1, 2)

        tg.addWidget(_lbl(t('lbl_i2p_sam'), color=G['text_muted'], size=11), 5, 0)
        self._i2p_sam_field = QLineEdit()
        self._i2p_sam_field.setText(self._app_settings.get('i2p_sam', '127.0.0.1:7656'))
        self._i2p_sam_field.setFixedWidth(200)
        self._i2p_sam_field.editingFinished.connect(self._save_i2p_settings)
        tg.addWidget(self._i2p_sam_field, 5, 1, Qt.AlignLeft)

        self._i2p_status_lbl = QLabel('')
        self._i2p_status_lbl.setStyleSheet(f'color: {G["text_muted"]}; font-size: 11px;')
        tg.addWidget(self._i2p_status_lbl, 6, 0, 1, 2)

        # Separator
        sep_line2 = QFrame(); sep_line2.setFrameShape(QFrame.HLine)
        sep_line2.setStyleSheet(f'color: {G["border2"]};')
        tg.addWidget(sep_line2, 7, 0, 1, 2)

        # Send-without-privacy warning
        self._chk_warn_privacy = QCheckBox(t('lbl_warn_no_privacy'))
        self._chk_warn_privacy.setChecked(self._app_settings.get('warn_no_privacy', True))
        self._chk_warn_privacy.stateChanged.connect(self._save_privacy_network_settings)
        tg.addWidget(self._chk_warn_privacy, 8, 0, 1, 2)

        v.addWidget(tor_box)
        QTimer.singleShot(600, self._update_privacy_badge)

        # ── btq.conf help ─────────────────────────────────────────────────
        help_box = QGroupBox(t('group_btqconf'))
        hv = QVBoxLayout(help_box)
        cfg_path = os.path.join(os.environ.get('APPDATA', '~'), 'BTQ', 'btq.conf')
        help_txt = QLabel(
            f'server=1\nrpcuser=youruser\nrpcpassword=yourpassword\nrpcallowip=127.0.0.1\n\n'
            f'{t("btqconf_location", path=cfg_path)}')
        help_txt.setFont(QFont('Consolas', 10))
        help_txt.setStyleSheet(
            f'color: {G["text_muted"]}; background: {G["surface2"]}; '
            f'border: 1px solid {G["border2"]}; border-radius: 3px; padding: 12px;')
        help_txt.setTextInteractionFlags(Qt.TextSelectableByMouse)
        hv.addWidget(help_txt)
        v.addWidget(help_box)
        v.addStretch()
        self.tabs.addTab(w, t('tab_settings'))

    # ──────────────────────────── Timer ───────────────────────────────────

    def _setup_timer(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._auto_refresh)
        self._timer.start(20_000)

    # ──────────────────────────── Auto-conexión ───────────────────────────

    def _try_auto_connect(self):
        settings, path = auto_detect_rpc()
        if settings:
            self.rpc_host.setText(settings['host'])
            self.rpc_port.setText(str(settings['port']))
            self.rpc_user.setText(settings['user'])
            self.rpc_pass.setText(settings['password'])
            self._set_status(t('status_config_found', path=path))
            self._connect(silent=True)
        else:
            self._set_status(t('status_no_config'))
            self.tabs.setCurrentIndex(6)

    def _autodetect(self):
        settings, path = auto_detect_rpc()
        if settings:
            self.rpc_host.setText(settings['host'])
            self.rpc_port.setText(str(settings['port']))
            self.rpc_user.setText(settings['user'])
            self.rpc_pass.setText(settings['password'])
            self._rpc_status.setText(t('status_config_found', path=path))
        else:
            QMessageBox.information(self, t('group_btqconf'), t('dlg_no_config'))

    # ──────────────────────────── Conexión ────────────────────────────────

    def _connect(self, silent=False):
        try:
            port = int(self.rpc_port.text())
        except ValueError:
            if not silent:
                QMessageBox.warning(self, 'BTQ', t('dlg_invalid_port'))
            return

        new_host = self.rpc_host.text().strip()
        new_user = self.rpc_user.text().strip()

        # Already connected to the same node — skip reconnect, just refresh data
        if (self._connected and self.rpc and
                self.rpc.host == new_host and self.rpc.port == port and
                self.rpc.user == new_user):
            self._start_worker(['balance', 'addresses', 'transactions', 'network'])
            return

        self.rpc = BTQRPCClient(
            host=new_host,
            port=port,
            user=new_user,
            password=self.rpc_pass.text().strip(),
        )
        try:
            info = self.rpc.get_blockchain_info()
            self.rpc.ensure_wallet_loaded()
            self._connected = True
            chain = info.get('chain', '?').upper()
            blocks = info.get('blocks', '?')
            self._set_badge(True, t('connected_badge', chain=chain, blocks=blocks))
            self._rpc_status.setText(t('connected_status', chain=chain, blocks=blocks))
            self._rpc_status.setStyleSheet(
                f'color: {G["green"]}; background: {G["green_dark"]}; '
                f'border: 1px solid {G["green_lo"]}; border-radius: 3px; padding: 8px;')
            self._set_status(t('status_connected', chain=chain, blocks=blocks))
            self._start_worker(['balance', 'addresses', 'transactions', 'network', 'utxos'])
        except (ConnectionError, BTQRPCError) as e:
            self._connected = False
            self.rpc = None
            self._set_badge(False)
            self._rpc_status.setText(f'Error: {e}')
            self._rpc_status.setStyleSheet(
                f'color: {G["red"]}; background: #1a0505; '
                f'border: 1px solid #3a0a0a; border-radius: 3px; padding: 8px;')
            if not silent:
                QMessageBox.critical(self, 'BTQ', str(e))
            self._set_status(t('status_disconnected'))

    def _disconnect(self):
        self.rpc = None
        self._connected = False
        self._addresses = {}
        self._set_badge(False)
        self._rpc_status.setText(t('status_disconnected'))
        self._rpc_status.setStyleSheet(
            f'color: {G["text_muted"]}; background: {G["surface2"]}; '
            f'border: 1px solid {G["border2"]}; border-radius: 3px; padding: 8px;')
        self._bal_main.setText('-.-------- BTQ')
        self._set_status(t('status_disconnected'))

    # ──────────────────────────── Node management ─────────────────────────

    @staticmethod
    def _find_btqd() -> str:
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        try:
            for entry in os.listdir(desktop):
                full = os.path.join(desktop, entry)
                if os.path.isdir(full):
                    candidate = os.path.join(full, _BTQD_BIN)
                    if os.path.exists(candidate):
                        return candidate
        except OSError:
            pass
        if not _IS_WIN:
            for path in ['/usr/local/bin/btqd', '/usr/bin/btqd',
                         os.path.expanduser('~/btqd'),
                         os.path.expanduser('~/.local/bin/btqd')]:
                if os.path.exists(path):
                    return path
        return ''

    def _browse_btqd(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Seleccionar btqd.exe', '', 'Ejecutables (*.exe)')
        if path:
            self._btqd_path.setText(path)

    def _check_node_running(self):
        try:
            if _IS_WIN:
                out = subprocess.check_output(
                    ['tasklist', '/FI', f'IMAGENAME eq {_BTQD_BIN}', '/NH'],
                    stderr=subprocess.DEVNULL, creationflags=0x08000000
                ).decode(errors='replace')
                running = _BTQD_BIN in out
            else:
                result = subprocess.run(['pgrep', '-x', 'btqd'], capture_output=True)
                running = result.returncode == 0
        except Exception:
            running = False

        if running:
            self._node_status.setText(t('node_running'))
            self._node_status.setStyleSheet(
                f'color: {G["green"]}; background: {G["green_dark"]}; '
                f'border: 1px solid {G["green_lo"]}; border-radius: 3px; padding: 8px;')
        else:
            self._node_status.setText(t('node_stopped'))
            self._node_status.setStyleSheet(
                f'color: {G["text_muted"]}; background: {G["surface2"]}; '
                f'border: 1px solid {G["border2"]}; border-radius: 3px; padding: 8px;')

    @staticmethod
    def _unblock_file(path: str):
        if not _IS_WIN:
            return
        zone_id = path + ':Zone.Identifier'
        try:
            if os.path.exists(zone_id):
                os.remove(zone_id)
        except OSError:
            try:
                subprocess.run(
                    ['powershell', '-NoProfile', '-Command',
                     f'Unblock-File -Path "{path}"'],
                    capture_output=True, creationflags=0x08000000, timeout=10
                )
            except Exception:
                pass

    def _start_node(self):
        btqd = self._btqd_path.text().strip()
        if not btqd or not os.path.exists(btqd):
            QMessageBox.warning(self, t('group_node'), t('dlg_btqd_notfound'))
            return
        # Integrity check
        try:
            current_hash = self._hash_file(btqd)
            stored_hash  = self._app_settings.get('btqd_sha256', '')
            if stored_hash and current_hash != stored_hash:
                reply = QMessageBox.warning(
                    self, t('group_node'),
                    t('node_hash_mismatch', expected=stored_hash[:32] + '…',
                      found=current_hash[:32] + '…'),
                    QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
            elif not stored_hash:
                self._app_settings['btqd_sha256'] = current_hash
                _save_app_settings(self._app_settings)
                if hasattr(self, '_node_hash_lbl'):
                    self._node_hash_lbl.setText(
                        t('node_hash_stored', hash=current_hash[:32] + '…'))
        except OSError:
            pass
        self._unblock_file(btqd)
        datadir = _default_datadir()
        use_tor = self._app_settings.get('use_tor', False)
        use_i2p = self._app_settings.get('use_i2p', False)
        tor_proxy = self._app_settings.get('tor_proxy', '127.0.0.1:9050') if use_tor else None
        i2p_sam   = self._app_settings.get('i2p_sam',   '127.0.0.1:7656') if use_i2p else None
        args = [btqd, '-testnet', f'-datadir={datadir}']
        if _IS_WIN:
            args.append('-nodaemon')
        if tor_proxy:
            args.append(f'-proxy={tor_proxy}')
            args.append('-onlynet=onion')
        if i2p_sam:
            args.append(f'-i2psam={i2p_sam}')
            args.append('-i2pacceptincoming')
            if not tor_proxy:
                args.append('-onlynet=i2p')
        popen_kwargs = {}
        if _IS_WIN:
            popen_kwargs['creationflags'] = 0x08000008
        else:
            popen_kwargs['start_new_session'] = True
        try:
            subprocess.Popen(args, **popen_kwargs)
            self._node_status.setText(t('node_starting'))
            self._node_status.setStyleSheet(
                f'color: {G["orange"]}; background: {G["surface2"]}; '
                f'border: 1px solid {G["border2"]}; border-radius: 3px; padding: 8px;')
            QTimer.singleShot(6000, self._check_node_running)
            QTimer.singleShot(8000, lambda: self._connect(silent=True))
        except Exception as e:
            msg = str(e)
            if 'cancelado' in msg.lower() or 'cancel' in msg.lower() or '1223' in msg:
                msg = t('dlg_node_blocked')
            QMessageBox.critical(self, t('group_node'), msg)

    def _stop_node(self):
        try:
            if _IS_WIN:
                subprocess.run(['taskkill', '/F', '/IM', _BTQD_BIN],
                               capture_output=True, creationflags=0x08000000)
            else:
                subprocess.run(['pkill', '-x', 'btqd'], capture_output=True)
            QTimer.singleShot(1500, self._check_node_running)
            self._disconnect()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

    def _set_badge(self, connected: bool, text: str = ''):
        if connected:
            self._badge.setText(text)
            self._badge.setStyleSheet(
                f'color: {G["green"]}; font-size: 10px; letter-spacing: 2px; '
                f'padding: 4px 12px; background: {G["green_dark"]}; '
                f'border: 1px solid {G["green_lo"]}; border-radius: 3px;')
        else:
            self._badge.setText(t('badge_no_conn'))
            self._badge.setStyleSheet(
                f'color: {G["red"]}; font-size: 10px; letter-spacing: 2px; '
                f'padding: 4px 12px; background: #1a0505; '
                f'border: 1px solid #3a0a0a; border-radius: 3px;')

    # ──────────────────────────── Worker ──────────────────────────────────

    def _start_worker(self, tasks: list):
        if not self._connected or not self.rpc:
            return
        if self._worker and self._worker.isRunning():
            return
        self._worker = RPCWorker(self.rpc, tasks)
        self._worker.data_ready.connect(self._on_data)
        self._worker.rpc_error.connect(self._on_rpc_error)
        self._worker.start()

    def _on_data(self, data: dict):
        if 'balance' in data:
            self._update_balance(data)
        if 'addresses' in data:
            self._update_addresses(data['addresses'])
        if 'transactions' in data:
            self._update_transactions(data['transactions'])
            self._check_new_incoming_tx(data['transactions'])
        if 'networkinfo' in data:
            self._update_network(data)
        if 'utxos' in data:
            self._update_utxos(data['utxos'])

    def _check_new_incoming_tx(self, txs: list):
        if not hasattr(self, '_tray'):
            return
        for tx in txs:
            if tx.get('category') != 'receive':
                continue
            txid = tx.get('txid', '')
            if not txid or txid in self._last_tx_ids:
                continue
            if self._last_tx_ids:  # don't notify on first load
                amount = float(tx.get('amount', 0))
                self._tray.showMessage(
                    t('tray_new_tx'),
                    t('tray_received', amount=amount),
                    QSystemTrayIcon.Information, 5000)
        self._last_tx_ids = {tx.get('txid', '') for tx in txs}

    def _on_rpc_error(self, msg: str):
        if 'connection' in msg.lower() or 'connect' in msg.lower():
            self._set_badge(False)
            self._connected = False
        self._set_status(f'RPC: {msg}')

    def _auto_refresh(self):
        if self._connected:
            self._start_worker(['balance', 'addresses', 'transactions', 'network', 'utxos'])

    # ──────────────────────────── Actualización datos ─────────────────────

    def _update_balance(self, data: dict):
        self._last_balance_data = data
        bal = data.get('balance', 0.0)
        unc = data.get('unconfirmed', 0.0)
        wi  = data.get('walletinfo', {})
        ci  = data.get('chaininfo', {})

        if self._hide_balance:
            self._bal_main.setText('*.**** BTQ')
            self._bal_pending.setText('*****')
            self._send_bal_lbl.setText(t('available_balance', amount=0.0).replace('0.00000000', '*****'))
        else:
            self._bal_main.setText(f'{bal:.8f} BTQ')
            self._bal_pending.setText(
                t('pending', amount=unc) if unc > 0 else t('no_pending'))
            self._send_bal_lbl.setText(t('available_balance', amount=bal))
        self._bal_pending.setStyleSheet(
            f'color: {G["orange"]};' if unc > 0 else f'color: {G["text_muted"]};')
        self._s_txcount.setText(str(wi.get('txcount', '—')))
        self._s_chain.setText(ci.get('chain', '—').upper())
        self._s_block.setText(f"{ci.get('blocks', '—'):,}" if isinstance(ci.get('blocks'), int) else '—')

        if self._connected:
            chain = ci.get('chain', '?').upper()
            blocks = ci.get('blocks', '?')
            self._set_badge(True, t('connected_badge', chain=chain, blocks=blocks))

    def _update_addresses(self, addrs: dict):
        self._addresses = addrs
        self._s_addresses.setText(str(len(addrs)))

        self._addr_table.setRowCount(len(addrs))
        for row, (addr, info) in enumerate(addrs.items()):
            self._addr_table.setItem(row, 0, QTableWidgetItem(addr))

            bal_item = QTableWidgetItem(f"{info['balance']:.8f}")
            bal_item.setForeground(QColor(G['green']) if info['balance'] > 0 else QColor(G['text_muted']))
            self._addr_table.setItem(row, 1, bal_item)

            rec_item = QTableWidgetItem(f"{info['received']:.8f}")
            rec_item.setForeground(QColor(G['text_muted']))
            self._addr_table.setItem(row, 2, rec_item)

            btn = QPushButton(t('btn_copy'))
            btn.setFixedSize(68, 24)
            btn.setStyleSheet(
                f'font-size:10px; padding:2px 4px; letter-spacing:1px;'
                f'background:{G["surface2"]}; border:1px solid {G["border"]}; color:{G["text_muted"]};'
                f'border-radius:2px;')
            btn.clicked.connect(lambda _, a=addr: self._copy(a))
            self._addr_table.setCellWidget(row, 3, btn)

        # Actualizar combo de recibir
        keys = list(addrs.keys())
        cur = self._recv_combo.currentText()
        self._recv_combo.blockSignals(True)
        self._recv_combo.clear()
        if keys:
            self._recv_combo.addItems(keys)
            if cur in keys:
                self._recv_combo.setCurrentText(cur)
        self._recv_combo.blockSignals(False)
        if self._recv_combo.currentText():
            self._refresh_qr(self._recv_combo.currentText())

    def _update_transactions(self, txs: list):
        # Collect all addresses ever used in transactions for reuse detection
        for tx in txs:
            addr = tx.get('address', '')
            if addr:
                self._used_addresses.add(addr)
        txs = sorted(txs, key=lambda t: t.get('time', 0), reverse=True)
        self._tx_table.setRowCount(len(txs))
        for row, tx in enumerate(txs):
            txid     = tx.get('txid', '—')
            cat      = tx.get('category', '—')
            address  = tx.get('address', '—')
            amount   = float(tx.get('amount', 0))
            confs    = tx.get('confirmations', 0)
            ts       = tx.get('time', 0)
            date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d  %H:%M') if ts else '—'

            self._tx_table.setItem(row, 0, QTableWidgetItem(txid[:20] + '…'))

            cat_label = t(f'tx_{cat}', **{}) if f'tx_{cat}' in TRANSLATIONS['en'] else cat
            cat_item = QTableWidgetItem(cat_label.upper())
            cat_item.setForeground(QColor(G['green']) if cat == 'receive'
                                   else QColor(G['red']) if cat == 'send'
                                   else QColor(G['orange']))
            self._tx_table.setItem(row, 1, cat_item)
            self._tx_table.setItem(row, 2, QTableWidgetItem(address))

            amt_item = QTableWidgetItem(f'{amount:+.8f}')
            amt_item.setForeground(QColor(G['green']) if amount > 0 else QColor(G['red']))
            self._tx_table.setItem(row, 3, amt_item)

            conf_item = QTableWidgetItem(str(confs))
            conf_item.setForeground(
                QColor(G['green']) if confs >= 6 else QColor(G['orange']))
            self._tx_table.setItem(row, 4, conf_item)
            self._tx_table.setItem(row, 5, QTableWidgetItem(date_str))

    def _update_network(self, data: dict):
        ci = data.get('chaininfo', {})
        ni = data.get('networkinfo', {})
        mi = data.get('mininginfo', {})

        def fmt(v, fmt_str=None):
            if v is None or v == '':
                return '—'
            return fmt_str.format(v) if fmt_str else str(v)

        blocks  = ci.get('blocks', None)
        headers = ci.get('headers', None)
        diff    = ci.get('difficulty', None)
        prog    = ci.get('verificationprogress', None)
        besthash = ci.get('bestblockhash', '')

        self._n['chain'].setText(ci.get('chain', '—').upper())
        self._n['blocks'].setText(f'{blocks:,}' if isinstance(blocks, int) else '—')
        self._n['headers'].setText(f'{headers:,}' if isinstance(headers, int) else '—')
        self._n['difficulty'].setText(f'{diff:,.4f}' if isinstance(diff, (int, float)) else '—')
        self._n['sync'].setText(f'{prog*100:.3f}%' if isinstance(prog, float) else '—')
        self._n['hash'].setText((besthash[:28] + '…') if besthash else '—')
        self._n['connections'].setText(str(ni.get('connections', '—')))
        self._n['version'].setText(ni.get('subversion', '—'))

        hashps = mi.get('networkhashps', 0)
        if isinstance(hashps, (int, float)) and hashps > 0:
            if hashps > 1e12:
                hr = f'{hashps/1e12:.2f} TH/s'
            elif hashps > 1e9:
                hr = f'{hashps/1e9:.2f} GH/s'
            elif hashps > 1e6:
                hr = f'{hashps/1e6:.2f} MH/s'
            else:
                hr = f'{hashps:.0f} H/s'
        else:
            hr = '—'
        self._n['hashrate'].setText(hr)
        self._n['mempool'].setText(str(mi.get('pooledtx', '—')))

    # ──────────────────────────── Acciones usuario ────────────────────────

    def _require_conn(self) -> bool:
        if not self._connected:
            QMessageBox.warning(self, 'BTQ', t('dlg_no_conn'))
            self.tabs.setCurrentIndex(6)
            return False
        return True

    def _gen_address(self):
        if not self._require_conn():
            return
        label, ok = QInputDialog.getText(self, t('tab_addresses'), t('dlg_gen_addr'))
        if not ok:
            return
        try:
            addr = self.rpc.get_new_address(label or '')
            self.cache.set_label(addr, label or '')
            QMessageBox.information(self, t('tab_addresses'), t('dlg_addr_generated', addr=addr))
            self._start_worker(['addresses'])
        except (BTQRPCError, ConnectionError) as e:
            QMessageBox.critical(self, 'BTQ', str(e))

    def _copy(self, text: str):
        QApplication.clipboard().setText(text)
        short = (text[:36] + '…') if len(text) > 36 else text
        self._set_status(t('copied', text=short))
        if self._clipboard_clear_secs > 0:
            if self._clipboard_timer and self._clipboard_timer.isActive():
                self._clipboard_timer.stop()
            self._clipboard_timer = QTimer(self)
            self._clipboard_timer.setSingleShot(True)
            _captured = text
            def _clear():
                if QApplication.clipboard().text() == _captured:
                    QApplication.clipboard().clear()
                    self._set_status(t('clipboard_cleared'))
            self._clipboard_timer.timeout.connect(_clear)
            self._clipboard_timer.start(self._clipboard_clear_secs * 1000)

    def _copy_recv_addr(self):
        addr = self._recv_combo.currentText()
        if addr:
            self._copy(addr)

    def _refresh_qr(self, address: str):
        self._recv_lbl.setText(address or '—')
        if not address or not QR_AVAILABLE:
            return
        try:
            qr = qrcode.QRCode(version=1, box_size=8, border=4,
                               error_correction=qrcode.constants.ERROR_CORRECT_M)
            qr.add_data(address)
            qr.make(fit=True)
            img = qr.make_image(fill_color=G['green'], back_color=G['bg'])
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            px = QPixmap()
            px.loadFromData(buf.getvalue())
            self._qr_lbl.setPixmap(
                px.scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            self._qr_lbl.setText(f'Error QR: {e}')

    def _set_max(self):
        if not self._require_conn():
            return
        try:
            bal = self.rpc.get_balance()
            self._amount.setText(f'{bal:.8f}')
        except (BTQRPCError, ConnectionError):
            pass

    def _send_tx(self):
        if not self._require_conn():
            return
        to   = self._to_addr.text().strip()
        amt  = self._amount.text().strip()
        note = self._send_note.text().strip()

        if not to or not amt:
            QMessageBox.warning(self, 'BTQ', t('dlg_invalid_amount'))
            return
        try:
            amount = float(amt)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, 'BTQ', t('dlg_invalid_amount'))
            return

        try:
            v = self.rpc.validate_address(to)
            if not v.get('isvalid', False):
                QMessageBox.warning(self, 'BTQ', f'"{to}" is not a valid BTQ address.')
                return
        except (BTQRPCError, ConnectionError):
            pass

        # Choose confirm message: large threshold or standard
        threshold = self._confirm_threshold
        msg_key = 'dlg_confirm_large' if (threshold > 0 and amount >= threshold) else 'dlg_confirm_send'
        if QMessageBox.question(
            self, t('tab_send'), t(msg_key, amount=amount, addr=to),
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return

        if not self._auto_unlock_for_send():
            return

        if self._app_settings.get('warn_no_privacy', True):
            no_tor = not self._app_settings.get('use_tor', False)
            no_i2p = not self._app_settings.get('use_i2p', False)
            if no_tor and no_i2p:
                if QMessageBox.question(
                    self, t('tab_send'), t('dlg_no_privacy'),
                    QMessageBox.Yes | QMessageBox.No
                ) != QMessageBox.Yes:
                    return

        selected = self._get_selected_utxos() if hasattr(self, '_utxo_table') else []
        if selected:
            self._send_with_coin_control(to, amount, note, selected)
            return

        try:
            conf_target = self._get_fee_conf_target()
            txid = self.rpc.send_to_address(to, amount, note, conf_target)
            QMessageBox.information(self, t('tab_send'), t('dlg_tx_sent', txid=txid))
            self._to_addr.clear()
            self._amount.clear()
            self._send_note.clear()
            self._start_worker(['balance', 'transactions'])
            self._set_status(f'TX: {txid[:20]}…')
        except (BTQRPCError, ConnectionError) as e:
            QMessageBox.critical(self, 'BTQ', str(e))

    def _export_wallet(self):
        if not self._require_conn():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, t('btn_export_keys'),
            f'btq_keys_{datetime.now().strftime("%Y%m%d_%H%M")}.txt', 'Text (*.txt)')
        if not path:
            return
        abs_path = os.path.abspath(path).replace('\\', '/')
        try:
            self.rpc.dump_wallet(abs_path)
            QMessageBox.information(self, t('btn_export_keys'), t('dlg_export_done', path=abs_path))
            self._set_status(t('btn_export_keys'))
        except (BTQRPCError, ConnectionError) as e:
            QMessageBox.critical(self, 'BTQ', str(e))

    def _backup_wallet(self):
        if not self._require_conn():
            return
        path, _ = QFileDialog.getSaveFileName(
            self, t('btn_backup_wallet'),
            f'wallet_backup_{datetime.now().strftime("%Y%m%d_%H%M")}.dat', 'Wallet (*.dat)')
        if not path:
            return
        abs_path = os.path.abspath(path).replace('\\', '/')
        try:
            self.rpc.backup_wallet(abs_path)
            QMessageBox.information(self, t('btn_backup_wallet'), t('dlg_backup_done', path=abs_path))
            self._set_status(t('status_backup_done'))
        except (BTQRPCError, ConnectionError) as e:
            QMessageBox.critical(self, 'BTQ', str(e))

    def _import_wallet(self):
        if not self._require_conn():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, t('btn_import_keys'), '', 'Text (*.txt);;All (*.*)')
        if not path:
            return
        if QMessageBox.question(
            self, t('btn_import_keys'), t('dlg_import_confirm', path=path),
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        abs_path = os.path.abspath(path).replace('\\', '/')
        try:
            self.rpc.import_wallet(abs_path)
            QMessageBox.information(self, t('btn_import_keys'), t('dlg_import_done'))
            self._set_status(t('status_keys_imported'))
        except (BTQRPCError, ConnectionError) as e:
            QMessageBox.critical(self, 'BTQ', str(e))

    # ──────────────────────────── Coin control ────────────────────────────

    def _update_utxos(self, utxos: list):
        if not hasattr(self, '_utxo_table'):
            return
        self._utxo_table.setRowCount(len(utxos))
        for row, u in enumerate(utxos):
            chk = QCheckBox()
            chk.stateChanged.connect(self._on_coin_control_changed)
            cell = QWidget()
            cell_lay = QHBoxLayout(cell)
            cell_lay.setContentsMargins(4, 0, 0, 0)
            cell_lay.addWidget(chk)
            self._utxo_table.setCellWidget(row, 0, cell)

            addr = u.get('address', '—')
            self._utxo_table.setItem(row, 1, QTableWidgetItem(addr))

            amt = float(u.get('amount', 0))
            amt_item = QTableWidgetItem(f'{amt:.8f}')
            amt_item.setForeground(QColor(G['green']))
            self._utxo_table.setItem(row, 2, amt_item)

            confs = u.get('confirmations', 0)
            conf_item = QTableWidgetItem(str(confs))
            conf_item.setForeground(
                QColor(G['green']) if confs >= 6 else QColor(G['orange']))
            self._utxo_table.setItem(row, 3, conf_item)

            # store full utxo data in the row
            self._utxo_table.item(row, 1).setData(Qt.UserRole, u)
        self._on_coin_control_changed()

    def _on_coin_control_changed(self):
        if not hasattr(self, '_utxo_table'):
            return
        total, count = 0.0, 0
        for row in range(self._utxo_table.rowCount()):
            cell = self._utxo_table.cellWidget(row, 0)
            if cell and cell.findChild(QCheckBox).isChecked():
                amt_item = self._utxo_table.item(row, 2)
                if amt_item:
                    total += float(amt_item.text())
                    count += 1
        if hasattr(self, '_utxo_selected_lbl'):
            self._utxo_selected_lbl.setText(
                t('lbl_selected_utxos', amount=total, count=count))

    def _utxo_select_all(self):
        for row in range(self._utxo_table.rowCount()):
            cell = self._utxo_table.cellWidget(row, 0)
            if cell:
                cell.findChild(QCheckBox).setChecked(True)

    def _utxo_deselect_all(self):
        for row in range(self._utxo_table.rowCount()):
            cell = self._utxo_table.cellWidget(row, 0)
            if cell:
                cell.findChild(QCheckBox).setChecked(False)

    def _get_selected_utxos(self) -> list:
        selected = []
        for row in range(self._utxo_table.rowCount()):
            cell = self._utxo_table.cellWidget(row, 0)
            if cell and cell.findChild(QCheckBox).isChecked():
                item = self._utxo_table.item(row, 1)
                if item:
                    utxo = item.data(Qt.UserRole)
                    if utxo:
                        selected.append(utxo)
        return selected

    def _send_with_coin_control(self, to: str, amount: float, note: str,
                                 selected_utxos: list):
        try:
            fee_rate = self._get_fee_rate()
            fee = max(round(fee_rate * 250 / 1000, 8), 0.0001)
            selected_total = sum(float(u['amount']) for u in selected_utxos)
            change = round(selected_total - amount - fee, 8)

            if change < 0:
                QMessageBox.warning(self, 'BTQ',
                    t('coin_control_insufficient',
                      selected=selected_total, needed=amount + fee))
                return

            if QMessageBox.question(
                self, t('tab_send'),
                t('dlg_coin_control_send', amount=amount, addr=to,
                  selected=selected_total, fee=fee,
                  change=change if change > 0 else 0.0),
                QMessageBox.Yes | QMessageBox.No
            ) != QMessageBox.Yes:
                return

            inputs = [{'txid': u['txid'], 'vout': u['vout']}
                      for u in selected_utxos]
            outputs = {to: round(amount, 8)}
            if change >= 0.00001:
                change_addr = self.rpc.get_raw_change_address()
                outputs[change_addr] = change

            raw = self.rpc.create_raw_transaction(inputs, outputs)
            signed = self.rpc.sign_raw_transaction(raw)
            if not signed.get('complete', False):
                QMessageBox.critical(self, 'BTQ', 'Transaction signing incomplete.')
                return
            txid = self.rpc.send_raw_transaction(signed['hex'])
            QMessageBox.information(self, t('tab_send'), t('dlg_tx_sent', txid=txid))
            self._to_addr.clear()
            self._amount.clear()
            self._send_note.clear()
            self._utxo_deselect_all()
            self._start_worker(['balance', 'transactions', 'utxos'])
            self._set_status(f'TX: {txid[:20]}…')
        except (BTQRPCError, ConnectionError) as e:
            QMessageBox.critical(self, 'BTQ', str(e))

    # ──────────────────────────── Tor ─────────────────────────────────────

    def _on_tor_changed(self, state: int):
        self._app_settings['use_tor'] = bool(state)
        _save_app_settings(self._app_settings)
        if state:
            self._check_tor()
        else:
            if hasattr(self, '_tor_status_lbl'):
                self._tor_status_lbl.setText('')
        self._update_privacy_badge()

    def _save_tor_settings(self):
        proxy = self._tor_proxy_field.text().strip() or '127.0.0.1:9050'
        self._app_settings['tor_proxy'] = proxy
        _save_app_settings(self._app_settings)
        if self._app_settings.get('use_tor'):
            self._check_tor()

    def _check_tor(self):
        import socket
        proxy = self._app_settings.get('tor_proxy', '127.0.0.1:9050')
        if hasattr(self, '_tor_status_lbl'):
            self._tor_status_lbl.setText(t('tor_checking'))
        try:
            host, port_str = proxy.rsplit(':', 1)
            sock = socket.create_connection((host, int(port_str)), timeout=3)
            sock.close()
            if hasattr(self, '_tor_status_lbl'):
                self._tor_status_lbl.setText(t('tor_reachable'))
                self._tor_status_lbl.setStyleSheet(
                    f'color: {G["green"]}; font-size: 11px;')
            self._update_privacy_badge()
        except Exception:
            if hasattr(self, '_tor_status_lbl'):
                self._tor_status_lbl.setText(t('tor_unreachable', proxy=proxy))
                self._tor_status_lbl.setStyleSheet(
                    f'color: {G["red"]}; font-size: 11px;')

    def _on_i2p_changed(self, state: int):
        self._app_settings['use_i2p'] = bool(state)
        _save_app_settings(self._app_settings)
        if state:
            self._check_i2p()
        else:
            if hasattr(self, '_i2p_status_lbl'):
                self._i2p_status_lbl.setText('')
        self._update_privacy_badge()

    def _save_i2p_settings(self):
        sam = self._i2p_sam_field.text().strip() or '127.0.0.1:7656'
        self._app_settings['i2p_sam'] = sam
        _save_app_settings(self._app_settings)
        if self._app_settings.get('use_i2p'):
            self._check_i2p()

    def _check_i2p(self):
        import socket
        sam = self._app_settings.get('i2p_sam', '127.0.0.1:7656')
        if hasattr(self, '_i2p_status_lbl'):
            self._i2p_status_lbl.setText(t('i2p_checking'))
        try:
            host, port_str = sam.rsplit(':', 1)
            sock = socket.create_connection((host, int(port_str)), timeout=3)
            sock.close()
            if hasattr(self, '_i2p_status_lbl'):
                self._i2p_status_lbl.setText(t('i2p_reachable'))
                self._i2p_status_lbl.setStyleSheet(
                    f'color: {G["green"]}; font-size: 11px;')
            self._update_privacy_badge()
        except Exception:
            if hasattr(self, '_i2p_status_lbl'):
                self._i2p_status_lbl.setText(t('i2p_unreachable', sam=sam))
                self._i2p_status_lbl.setStyleSheet(
                    f'color: {G["red"]}; font-size: 11px;')

    def _save_privacy_network_settings(self):
        self._app_settings['warn_no_privacy'] = self._chk_warn_privacy.isChecked()
        _save_app_settings(self._app_settings)

    def _update_privacy_badge(self):
        if not hasattr(self, '_privacy_badge'):
            return
        use_tor = self._app_settings.get('use_tor', False)
        use_i2p = self._app_settings.get('use_i2p', False)
        if use_tor and use_i2p:
            label = f'{t("privacy_badge_tor")} + {t("privacy_badge_i2p")}'
            color, bg, border = G['green'], G['green_dark'], G['green_lo']
        elif use_tor:
            label = t('privacy_badge_tor')
            color, bg, border = G['green'], G['green_dark'], G['green_lo']
        elif use_i2p:
            label = t('privacy_badge_i2p')
            color, bg, border = '#a78bfa', '#1a0a2e', '#4a2a7e'
        else:
            label = t('privacy_badge_direct')
            color, bg, border = G['text_muted'], G['surface2'], G['border2']
        self._privacy_badge.setText(label)
        self._privacy_badge.setStyleSheet(
            f'color: {color}; font-size: 10px; letter-spacing: 2px;'
            f'padding: 4px 10px; background: {bg}; border: 1px solid {border}; border-radius: 3px;')

    # ──────────────────────────── Encrypted backup ────────────────────────

    def _export_encrypted(self):
        if not self._require_conn():
            return
        if not CRYPTO_AVAILABLE:
            QMessageBox.warning(self, t('export_encrypted'), t('crypto_unavailable'))
            return
        passphrase, ok1 = QInputDialog.getText(
            self, t('export_encrypted'), t('export_passphrase'), QLineEdit.Password)
        if not ok1 or not passphrase:
            return
        confirm, ok2 = QInputDialog.getText(
            self, t('export_encrypted'), t('export_confirm_passphrase'), QLineEdit.Password)
        if not ok2 or passphrase != confirm:
            QMessageBox.warning(self, t('export_encrypted'), t('export_mismatch'))
            return
        path, _ = QFileDialog.getSaveFileName(
            self, t('export_encrypted'),
            f'btq_backup_{datetime.now().strftime("%Y%m%d_%H%M")}.btqenc',
            'Encrypted Wallet (*.btqenc)')
        if not path:
            return
        import tempfile
        tmp = os.path.join(tempfile.gettempdir(), f'btq_tmp_{secrets.token_hex(8)}.txt')
        try:
            self.rpc.dump_wallet(os.path.abspath(tmp).replace('\\', '/'))
            with open(tmp, 'rb') as f:
                plaintext = f.read()
            salt = secrets.token_bytes(16)
            iv   = secrets.token_bytes(16)
            kdf  = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                               iterations=100_000, backend=_crypto_backend())
            key  = kdf.derive(passphrase.encode('utf-8'))
            padder = PKCS7(128).padder()
            padded = padder.update(plaintext) + padder.finalize()
            enc = Cipher(algorithms.AES(key), modes.CBC(iv),
                         backend=_crypto_backend()).encryptor()
            ct  = enc.update(padded) + enc.finalize()
            with open(path, 'wb') as f:
                f.write(b'BTQE' + salt + iv + ct)
            QMessageBox.information(self, t('export_encrypted'), t('export_saved', path=path))
            self._set_status(t('export_encrypted'))
        except Exception as e:
            QMessageBox.critical(self, t('export_encrypted'), str(e))
        finally:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass

    def _import_encrypted(self):
        if not self._require_conn():
            return
        if not CRYPTO_AVAILABLE:
            QMessageBox.warning(self, t('import_encrypted'), t('crypto_unavailable'))
            return
        path, _ = QFileDialog.getOpenFileName(
            self, t('import_encrypted'), '',
            'Encrypted Wallet (*.btqenc);;All Files (*.*)')
        if not path:
            return
        passphrase, ok = QInputDialog.getText(
            self, t('import_encrypted'), t('import_passphrase_prompt'), QLineEdit.Password)
        if not ok:
            return
        import tempfile
        tmp = os.path.join(tempfile.gettempdir(), f'btq_tmp_{secrets.token_hex(8)}.txt')
        try:
            with open(path, 'rb') as f:
                data = f.read()
            if data[:4] != b'BTQE' or len(data) < 36:
                QMessageBox.critical(self, t('import_encrypted'), 'Invalid or corrupted file.')
                return
            salt, iv, ct = data[4:20], data[20:36], data[36:]
            kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt,
                              iterations=100_000, backend=_crypto_backend())
            key = kdf.derive(passphrase.encode('utf-8'))
            dec = Cipher(algorithms.AES(key), modes.CBC(iv),
                         backend=_crypto_backend()).decryptor()
            padded = dec.update(ct) + dec.finalize()
            unpadder = PKCS7(128).unpadder()
            plaintext = unpadder.update(padded) + unpadder.finalize()
            with open(tmp, 'wb') as f:
                f.write(plaintext)
            self.rpc.import_wallet(os.path.abspath(tmp).replace('\\', '/'))
            QMessageBox.information(self, t('import_encrypted'), t('import_ok'))
            self._set_status(t('import_encrypted'))
            self._start_worker(['balance', 'transactions'])
        except Exception as e:
            QMessageBox.critical(self, t('import_encrypted'), f'Decryption failed: {e}')
        finally:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass

    # ──────────────────────────── Node integrity ──────────────────────────

    @staticmethod
    def _hash_file(path: str) -> str:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()

    def _reset_node_hash(self):
        self._app_settings['btqd_sha256'] = ''
        _save_app_settings(self._app_settings)
        if hasattr(self, '_node_hash_lbl'):
            self._node_hash_lbl.setText(t('node_hash_none'))
        self._set_status(t('node_hash_reset_done'))

    # ──────────────────────────── Address reuse ───────────────────────────

    def _check_address_reuse(self, addr: str):
        addr = addr.strip()
        if not addr or not hasattr(self, '_addr_reuse_lbl'):
            return
        if addr in self._used_addresses:
            self._addr_reuse_lbl.setText(t('addr_reuse_warning'))
            self._addr_reuse_lbl.show()
        else:
            self._addr_reuse_lbl.hide()

    # ──────────────────────────── Privacy settings ────────────────────────

    def _save_lock_settings(self):
        mins = int(self._spin_lock_timeout.value())
        self._app_settings['lock_timeout_minutes'] = mins
        _save_app_settings(self._app_settings)
        self._set_status(t('settings_saved'))

    # ──────────────────────────── System tray ─────────────────────────────

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray = QSystemTrayIcon(self)
        icon = QApplication.style().standardIcon(
            QApplication.style().SP_ComputerIcon)
        self._tray.setIcon(icon)
        self._tray.setToolTip(t('tray_tooltip'))

        menu = QMenu()
        act_open = QAction(t('tray_open'), self)
        act_open.triggered.connect(self._show_and_raise)
        menu.addAction(act_open)
        menu.addSeparator()
        act_lock = QAction(t('tray_lock'), self)
        act_lock.triggered.connect(self._lock)
        menu.addAction(act_lock)
        menu.addSeparator()
        act_quit = QAction(t('tray_quit'), self)
        act_quit.triggered.connect(self._quit_app)
        menu.addAction(act_quit)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    # ──────────────────────────── Auto-update ─────────────────────────────

    def _check_for_update(self):
        proxy = ''
        if self._app_settings.get('use_tor'):
            proxy = self._app_settings.get('tor_proxy', '127.0.0.1:9050')
        worker = _UpdateWorker(socks5_proxy=proxy)
        worker.result.connect(self._on_update_result)
        worker.setParent(self)
        worker.start()

    def _on_update_result(self, latest: str):
        if not latest:
            return
        try:
            def _parse(v): return tuple(int(x) for x in v.lstrip('v').split('.')[:3])
            if _parse(latest) > _parse(__version__):
                self._update_lbl.setText(t('update_available', version=latest))
                self._update_banner.show()
        except ValueError:
            pass

    def _open_releases_page(self):
        import webbrowser
        webbrowser.open('https://github.com/adrianrozadagarcia/BTQ-Wallet/releases')

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_and_raise()

    def _show_and_raise(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit_app(self):
        self._do_cleanup()
        QApplication.quit()

    # ──────────────────────────── Wallet encryption ───────────────────────

    def _refresh_wallet_enc_ui(self):
        if not self._connected or not self.rpc:
            return
        if not hasattr(self, '_enc_status_lbl'):
            return
        try:
            info = self.rpc.get_wallet_info()
            status = info.get('encryption_status', '')
            unlocked_until = info.get('unlocked_until', None)
            if not status:
                if unlocked_until is None:
                    status = 'unencrypted'
                elif unlocked_until == 0:
                    status = 'locked'
                else:
                    status = 'unlocked'
            self._wallet_enc_status = status
        except (BTQRPCError, ConnectionError):
            return

        if self._wallet_enc_status == 'unencrypted':
            self._enc_status_lbl.setText(t('wallet_enc_unencrypted'))
            self._enc_status_lbl.setStyleSheet(
                f'color: {G["orange"]}; background: {G["surface2"]}; '
                f'border: 1px solid {G["border2"]}; border-radius: 3px; padding: 8px; font-size: 11px;')
            self._btn_encrypt.show()
            self._btn_unlock_enc.hide()
            self._btn_lock_enc.hide()
            self._btn_chg_pass.hide()
        elif self._wallet_enc_status == 'locked':
            self._enc_status_lbl.setText(t('wallet_enc_locked'))
            self._enc_status_lbl.setStyleSheet(
                f'color: {G["text_muted"]}; background: {G["surface2"]}; '
                f'border: 1px solid {G["border2"]}; border-radius: 3px; padding: 8px; font-size: 11px;')
            self._btn_encrypt.hide()
            self._btn_unlock_enc.show()
            self._btn_lock_enc.hide()
            self._btn_chg_pass.show()
        else:  # unlocked
            self._enc_status_lbl.setText(t('wallet_enc_unlocked'))
            self._enc_status_lbl.setStyleSheet(
                f'color: {G["green"]}; background: {G["green_dark"]}; '
                f'border: 1px solid {G["green_lo"]}; border-radius: 3px; padding: 8px; font-size: 11px;')
            self._btn_encrypt.hide()
            self._btn_unlock_enc.hide()
            self._btn_lock_enc.show()
            self._btn_chg_pass.show()

    def _encrypt_wallet(self):
        if not self._require_conn():
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(t('btn_encrypt_wallet'))
        dlg.setMinimumWidth(340)
        lay = QVBoxLayout(dlg)
        lay.setSpacing(10)
        lay.addWidget(_lbl(t('dlg_enc_passphrase'), color=G['text_muted'], size=11))
        inp1 = QLineEdit(); inp1.setEchoMode(QLineEdit.Password)
        lay.addWidget(inp1)
        lay.addWidget(_lbl(t('dlg_enc_confirm'), color=G['text_muted'], size=11))
        inp2 = QLineEdit(); inp2.setEchoMode(QLineEdit.Password)
        lay.addWidget(inp2)
        btns = QHBoxLayout()
        ok = QPushButton('OK'); cancel = QPushButton(t('tray_quit').replace('Quit', 'Cancel') if False else 'Cancel')
        ok.clicked.connect(dlg.accept); cancel.clicked.connect(dlg.reject)
        btns.addStretch(); btns.addWidget(ok); btns.addWidget(cancel)
        lay.addLayout(btns)
        if dlg.exec_() != QDialog.Accepted:
            return
        p1, p2 = inp1.text(), inp2.text()
        if not p1:
            return
        if p1 != p2:
            QMessageBox.warning(self, t('btn_encrypt_wallet'), t('dlg_enc_mismatch'))
            return
        try:
            self.rpc.encrypt_wallet(p1)
            QMessageBox.information(self, t('btn_encrypt_wallet'), t('dlg_enc_done'))
            self._wallet_enc_status = 'locked'
            self._refresh_wallet_enc_ui()
        except (BTQRPCError, ConnectionError) as e:
            QMessageBox.critical(self, 'BTQ', str(e))

    def _unlock_wallet_dlg(self, timeout: int = 0):
        if not self._require_conn():
            return
        passphrase, ok = QInputDialog.getText(
            self, t('btn_unlock_wallet'), t('dlg_enc_passphrase'),
            QLineEdit.Password)
        if not ok or not passphrase:
            return
        if timeout == 0:
            timeout, ok2 = QInputDialog.getInt(
                self, t('btn_unlock_wallet'), t('dlg_enc_unlock_timeout'),
                300, 1, 86400)
            if not ok2:
                return
        try:
            self.rpc.wallet_passphrase(passphrase, timeout)
            self._wallet_enc_status = 'unlocked'
            self._refresh_wallet_enc_ui()
            self._set_status(t('dlg_enc_unlocked'))
        except (BTQRPCError, ConnectionError) as e:
            QMessageBox.critical(self, 'BTQ', str(e))
        return True

    def _lock_wallet_enc(self):
        if not self._require_conn():
            return
        try:
            self.rpc.wallet_lock()
            self._wallet_enc_status = 'locked'
            self._refresh_wallet_enc_ui()
            self._set_status(t('dlg_enc_locked_ok'))
        except (BTQRPCError, ConnectionError) as e:
            QMessageBox.critical(self, 'BTQ', str(e))

    def _change_passphrase(self):
        if not self._require_conn():
            return
        old, ok1 = QInputDialog.getText(
            self, t('btn_change_passphrase'), t('dlg_enc_old_pass'),
            QLineEdit.Password)
        if not ok1 or not old:
            return
        new1, ok2 = QInputDialog.getText(
            self, t('btn_change_passphrase'), t('dlg_enc_new_pass'),
            QLineEdit.Password)
        if not ok2 or not new1:
            return
        new2, ok3 = QInputDialog.getText(
            self, t('btn_change_passphrase'), t('dlg_enc_confirm'),
            QLineEdit.Password)
        if not ok3:
            return
        if new1 != new2:
            QMessageBox.warning(self, t('btn_change_passphrase'), t('dlg_enc_mismatch'))
            return
        try:
            self.rpc.wallet_passphrase_change(old, new1)
            QMessageBox.information(self, t('btn_change_passphrase'), t('dlg_enc_changed'))
        except (BTQRPCError, ConnectionError) as e:
            QMessageBox.critical(self, 'BTQ', str(e))

    def _auto_unlock_for_send(self) -> bool:
        if self._wallet_enc_status != 'locked':
            return True
        passphrase, ok = QInputDialog.getText(
            self, t('btn_unlock_wallet'), t('dlg_enc_locked_send'),
            QLineEdit.Password)
        if not ok or not passphrase:
            return False
        try:
            self.rpc.wallet_passphrase(passphrase, 60)
            self._wallet_enc_status = 'unlocked'
            return True
        except (BTQRPCError, ConnectionError) as e:
            QMessageBox.critical(self, 'BTQ', str(e))
            return False

    # ──────────────────────────── Fee selector ────────────────────────────

    def _on_fee_speed_changed(self, index: int):
        is_custom = (index == 3)
        if hasattr(self, '_fee_custom_spin'):
            if is_custom:
                self._fee_custom_spin.show()
            else:
                self._fee_custom_spin.hide()
        self._update_fee_estimate()

    def _update_fee_estimate(self):
        if not hasattr(self, '_fee_estimate_lbl'):
            return
        try:
            amount_text = self._amount.text().strip() if hasattr(self, '_amount') else '0'
            amount = float(amount_text) if amount_text else 0.0
        except ValueError:
            amount = 0.0

        conf_target = self._get_fee_conf_target()
        if self._connected and self.rpc:
            try:
                rate = self.rpc.estimate_smart_fee(conf_target)
                fee = max(round(rate * 250 / 1000, 8), 0.0001)
                self._fee_estimate_lbl.setText(t('lbl_fee_estimate', fee=fee))
                return
            except (BTQRPCError, ConnectionError):
                pass
        self._fee_estimate_lbl.setText(t('lbl_fee_estimate', fee=0.0))

    def _get_fee_conf_target(self) -> int:
        if not hasattr(self, '_fee_combo'):
            return 6
        idx = self._fee_combo.currentIndex()
        return [24, 6, 2, 6][idx]

    def _get_fee_rate(self) -> float:
        if not hasattr(self, '_fee_combo'):
            return 0.0001
        if self._fee_combo.currentIndex() == 3 and hasattr(self, '_fee_custom_spin'):
            return self._fee_custom_spin.value()
        if self._connected and self.rpc:
            try:
                return self.rpc.estimate_smart_fee(self._get_fee_conf_target())
            except (BTQRPCError, ConnectionError):
                pass
        return 0.0001

    # ──────────────────────────── Language & Privacy ──────────────────────

    def _on_lang_changed(self, index: int):
        lang = self._lang_combo.itemData(index)
        if lang and lang != _LANG:
            self._rebuild_ui(lang)

    def _rebuild_ui(self, lang: str):
        global _LANG
        _LANG = lang
        self._app_settings['language'] = lang
        _save_app_settings(self._app_settings)

        # Capture current state before rebuilding
        rpc_h = self.rpc_host.text()
        rpc_p = self.rpc_port.text()
        rpc_u = self.rpc_user.text()
        rpc_pw = self.rpc_pass.text()
        btqd = getattr(self, '_btqd_path', None)
        btqd_val = btqd.text() if btqd else ''
        lock_mins = getattr(self, '_spin_lock_timeout', None)
        lock_mins_val = int(lock_mins.value()) if lock_mins else None
        fee_idx = self._fee_combo.currentIndex() if hasattr(self, '_fee_combo') else 1
        fee_custom_val = self._fee_custom_spin.value() if hasattr(self, '_fee_custom_spin') else 0.0001
        cur_tab = self.tabs.currentIndex()

        if hasattr(self, '_node_check_timer'):
            self._node_check_timer.stop()

        while self.tabs.count():
            self.tabs.removeTab(0)

        self._tab_balance()
        self._tab_addresses()
        self._tab_receive()
        self._tab_send()
        self._tab_transactions()
        self._tab_network()
        self._tab_settings()

        # Restore fields
        self.rpc_host.setText(rpc_h)
        self.rpc_port.setText(rpc_p)
        self.rpc_user.setText(rpc_u)
        self.rpc_pass.setText(rpc_pw)
        if btqd_val:
            self._btqd_path.setText(btqd_val)
        if lock_mins_val is not None and hasattr(self, '_spin_lock_timeout'):
            self._spin_lock_timeout.setValue(lock_mins_val)
        if hasattr(self, '_fee_combo'):
            self._fee_combo.setCurrentIndex(fee_idx)
        if hasattr(self, '_fee_custom_spin'):
            self._fee_custom_spin.setValue(fee_custom_val)
        self.tabs.setCurrentIndex(min(cur_tab, self.tabs.count() - 1))

        # Restore connection status display
        if self._connected and self.rpc:
            self._set_badge(True, t('connected_badge', chain='?', blocks='?'))
            self._rpc_status.setStyleSheet(
                f'color: {G["green"]}; background: {G["green_dark"]}; '
                f'border: 1px solid {G["green_lo"]}; border-radius: 3px; padding: 8px;')
            self._start_worker(['balance', 'addresses', 'transactions', 'network'])
        else:
            self._set_badge(False)

        self._set_status(t('settings_saved'))

    def _on_hide_balance_changed(self, state: int):
        self._hide_balance = bool(state)
        self._app_settings['hide_balance'] = self._hide_balance
        _save_app_settings(self._app_settings)
        if self._last_balance_data:
            self._update_balance(self._last_balance_data)

    def _save_privacy_settings(self):
        self._clipboard_clear_secs = self._spin_clipboard.value()
        self._confirm_threshold    = self._spin_threshold.value()
        self._app_settings['clipboard_clear_seconds'] = self._clipboard_clear_secs
        self._app_settings['confirm_threshold_btq']   = self._confirm_threshold
        _save_app_settings(self._app_settings)
        self._set_status(t('settings_saved'))

    # ──────────────────────────── Helpers ─────────────────────────────────

    def _set_status(self, msg: str):
        self._status_bar.showMessage(
            f'{datetime.now().strftime("%H:%M:%S")}   {msg}')

    def closeEvent(self, event):
        # Minimize to tray instead of quitting, if tray is available
        if hasattr(self, '_tray') and self._tray.isVisible():
            self.hide()
            self._tray.showMessage(
                'BTQ Wallet', t('tray_hidden'),
                QSystemTrayIcon.Information, 3000)
            event.ignore()
            return
        self._do_cleanup()
        event.accept()

    def _do_cleanup(self):
        if self._worker and self._worker.isRunning():
            self._worker.wait(2000)
        QApplication.clipboard().clear()
        if self.rpc:
            self.rpc.user = ''
            self.rpc.password = ''
        if hasattr(self, '_lock_pin_input'):
            self._lock_pin_input.clear()


# ─────────────────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    gui = WalletGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
