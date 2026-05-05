"""
platform_utils.py — BTQ Wallet platform-specific helpers
All Windows / Linux / macOS branching lives here so simple_wallet_gui.py
stays platform-agnostic.

Public API imported by simple_wallet_gui.py:
    IS_WIN, IS_LINUX, IS_MAC
    get_settings_path()
    get_btqd_exe_name()
    find_btqd()
    find_btq_configs()
    get_btqconf_default_path()
    create_shortcut(script_path, python_path, icon_path, settings, save_settings_fn)
    secure_settings_file(path)
    get_subprocess_kwargs()
"""
from __future__ import annotations  # Python 3.8 compatibility for type hints

import os
import sys
import shlex
import subprocess

# ══════════════════════════════════════════════
#  PATH CONSTANTS
# ══════════════════════════════════════════════

_HERE   = os.path.dirname(os.path.abspath(__file__))   # src/
_ASSETS = os.path.join(_HERE, '..', 'assets')          # assets/ (one level up)

# ══════════════════════════════════════════════
#  PLATFORM DETECTION
# ══════════════════════════════════════════════

IS_WIN   = sys.platform == 'win32'
IS_LINUX = sys.platform.startswith('linux')
IS_MAC   = sys.platform == 'darwin'

# ══════════════════════════════════════════════
#  WINDOWS
# ══════════════════════════════════════════════

def _find_btqd_windows() -> str:
    """Search Desktop sub-folders for btqd.exe on Windows."""
    btqd_bin = 'btqd.exe'
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    try:
        for entry in os.listdir(desktop):
            full = os.path.join(desktop, entry)
            if os.path.isdir(full):
                candidate = os.path.join(full, btqd_bin)
                if os.path.exists(candidate):
                    return candidate
    except OSError:
        pass
    return ''


def _secure_settings_windows(path: str):
    """Restrict settings file to the current user only using icacls."""
    try:
        import getpass
        user = getpass.getuser()
        subprocess.run(
            ['icacls', path, '/inheritance:r', '/grant:r', f'{user}:RW'],
            capture_output=True, creationflags=0x08000000, timeout=5
        )
    except Exception:
        pass


def _create_shortcut_windows(script_path: str, python_path: str,
                              icon_path: str, settings: dict,
                              save_settings_fn) -> bool:
    """
    Create a .lnk desktop shortcut on Windows via VBScript.
    Returns True on success.
    """
    import tempfile

    _dir = os.path.dirname(os.path.abspath(script_path))
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    lnk_path = os.path.join(desktop, 'BTQ Wallet.lnk')

    # Already exists — mark as done and return
    if os.path.exists(lnk_path):
        settings['shortcut_created'] = True
        save_settings_fn(settings)
        return True

    # Prefer .ico; fall back to python executable icon
    ico_path = icon_path
    if not ico_path.endswith('.ico'):
        # look for a .ico next to the supplied icon, then in assets/
        candidate_ico = os.path.splitext(icon_path)[0] + '.ico'
        assets_ico = os.path.normpath(os.path.join(_ASSETS, 'btq_wallet.ico'))
        if os.path.isfile(candidate_ico):
            ico_path = candidate_ico
        elif os.path.isfile(assets_ico):
            ico_path = assets_ico
        else:
            ico_path = python_path

    if getattr(sys, 'frozen', False):
        target = sys.executable
        args = ''
    else:
        target = python_path
        args = os.path.abspath(script_path)

    def dq(s):
        return s.replace('"', '""')

    vbs = (
        'Set sh = WScript.CreateObject("WScript.Shell")\n'
        f'Set lnk = sh.CreateShortcut("{dq(lnk_path)}")\n'
        f'lnk.TargetPath = "{dq(target)}"\n'
        f'lnk.Arguments = Chr(34) & "{dq(args)}" & Chr(34)\n'
        f'lnk.WorkingDirectory = "{dq(_dir)}"\n'
        f'lnk.IconLocation = "{dq(ico_path)}"\n'
        'lnk.Description = "BTQ Wallet - Post-Quantum Bitcoin"\n'
        'lnk.Save\n'
    )
    try:
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.vbs',
                                          delete=False, encoding='utf-8')
        tmp.write(vbs)
        tmp.close()
        wscript = os.path.join(
            os.environ.get('SystemRoot', r'C:\Windows'),
            'System32', 'wscript.exe'
        )
        subprocess.run(
            [wscript, '//nologo', tmp.name],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15
        )
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
        if os.path.exists(lnk_path):
            settings['shortcut_created'] = True
            save_settings_fn(settings)
            return True
    except Exception:
        pass
    return False


# ══════════════════════════════════════════════
#  LINUX
# ══════════════════════════════════════════════

def _xdg_desktop_dir() -> str:
    """Return the user's Desktop directory, respecting XDG / locale."""
    try:
        r = subprocess.run(['xdg-user-dir', 'DESKTOP'],
                           capture_output=True, text=True, timeout=3)
        path = r.stdout.strip()
        if r.returncode == 0 and path:
            return path
    except Exception:
        pass
    return os.path.join(os.path.expanduser('~'), 'Desktop')


def _find_btqd_linux() -> str:
    """Search common Linux locations for the btqd binary."""
    btqd_bin = 'btqd'

    # Same directory as this module (src/) and project root (one level up)
    try:
        here = os.path.join(_HERE, btqd_bin)
        if os.path.isfile(here) and os.access(here, os.X_OK):
            return here
        root = os.path.join(_HERE, '..', btqd_bin)
        root = os.path.normpath(root)
        if os.path.isfile(root) and os.access(root, os.X_OK):
            return root
    except Exception:
        pass

    # Desktop sub-folders
    desktop = _xdg_desktop_dir()
    try:
        for entry in os.listdir(desktop):
            full = os.path.join(desktop, entry)
            if os.path.isdir(full):
                candidate = os.path.join(full, btqd_bin)
                if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                    return candidate
    except OSError:
        pass

    # Standard bin locations
    for path in [
        os.path.expanduser('~/.local/bin/btqd'),
        '/usr/local/bin/btqd',
        '/usr/bin/btqd',
        os.path.expanduser('~/btqd'),
    ]:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return ''


def _secure_settings_linux(path: str):
    """Restrict settings file to the current user only using chmod 600."""
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def _create_shortcut_linux(script_path: str, python_path: str,
                            icon_path: str, settings: dict,
                            save_settings_fn) -> bool:
    """
    Create a .desktop entry (system menu + Desktop folder) on Linux.
    Returns True on success.
    """
    apps_dir    = os.path.expanduser('~/.local/share/applications')
    desktop_dir = _xdg_desktop_dir()
    work_dir    = os.path.dirname(os.path.abspath(script_path))

    # Properly quote paths so spaces don't break the Exec line
    exec_cmd = f'{shlex.quote(python_path)} {shlex.quote(os.path.abspath(script_path))}'

    # Prefer PNG icon; fall back to assets/ then JPG or whatever was supplied
    icon = icon_path
    if not icon.endswith('.png'):
        png = os.path.splitext(icon)[0] + '.png'
        assets_png = os.path.normpath(os.path.join(_ASSETS, 'btq_wallet.png'))
        if os.path.isfile(png):
            icon = png
        elif os.path.isfile(assets_png):
            icon = assets_png
        # else keep icon_path as-is

    desktop_content = (
        '[Desktop Entry]\n'
        'Version=1.1\n'
        'Type=Application\n'
        'Name=BTQ Wallet\n'
        'GenericName=Bitcoin Quantum Wallet\n'
        'Comment=Post-quantum desktop wallet for the BTQ network\n'
        f'Exec={exec_cmd}\n'
        f'Path={work_dir}\n'
        f'Icon={icon}\n'
        'Terminal=false\n'
        'Categories=Finance;Network;\n'
        'Keywords=bitcoin;quantum;wallet;btq;crypto;dilithium;\n'
        'StartupNotify=false\n'
    )
    try:
        os.makedirs(apps_dir, exist_ok=True)

        # Install into application menu
        app_entry = os.path.join(apps_dir, 'btq-wallet.desktop')
        with open(app_entry, 'w', encoding='utf-8') as f:
            f.write(desktop_content)
        os.chmod(app_entry, 0o755)

        # Refresh GNOME / KDE application database
        try:
            subprocess.run(['update-desktop-database', apps_dir],
                           capture_output=True, timeout=5)
        except Exception:
            pass

        # Desktop shortcut (if the desktop folder exists)
        if os.path.isdir(desktop_dir):
            desk_entry = os.path.join(desktop_dir, 'btq-wallet.desktop')
            with open(desk_entry, 'w', encoding='utf-8') as f:
                f.write(desktop_content)
            os.chmod(desk_entry, 0o755)
            # Mark as trusted on GNOME 3.28+ (removes "untrusted launcher" warning)
            try:
                subprocess.run(
                    ['gio', 'set', desk_entry, 'metadata::trusted', 'true'],
                    capture_output=True, timeout=3
                )
            except Exception:
                pass

        settings['shortcut_created'] = True
        save_settings_fn(settings)
        return True
    except Exception:
        pass
    return False


# ══════════════════════════════════════════════
#  MACOS
# ══════════════════════════════════════════════

def _find_btqd_mac() -> str:
    """Search Desktop sub-folders and standard bin locations on macOS."""
    btqd_bin = 'btqd'

    try:
        here = os.path.join(_HERE, btqd_bin)
        if os.path.isfile(here) and os.access(here, os.X_OK):
            return here
        root = os.path.normpath(os.path.join(_HERE, '..', btqd_bin))
        if os.path.isfile(root) and os.access(root, os.X_OK):
            return root
    except Exception:
        pass

    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    try:
        for entry in os.listdir(desktop):
            full = os.path.join(desktop, entry)
            if os.path.isdir(full):
                candidate = os.path.join(full, btqd_bin)
                if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                    return candidate
    except OSError:
        pass
    for path in [
        '/usr/local/bin/btqd',
        '/opt/homebrew/bin/btqd',
        '/usr/bin/btqd',
        os.path.expanduser('~/.local/bin/btqd'),
        os.path.expanduser('~/btqd'),
    ]:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return ''


def _secure_settings_mac(path: str):
    """Restrict settings file to the current user only using chmod 600."""
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def _create_shortcut_mac(script_path: str, python_path: str,
                          icon_path: str, settings: dict,
                          save_settings_fn) -> bool:
    """macOS shortcut creation is a no-op (drag-to-Dock is the convention)."""
    return False


# ══════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════

def get_settings_path() -> str:
    """
    Return the full path to btq_wallet_settings.json, creating its parent
    directory if necessary.
    """
    if IS_WIN:
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        path = os.path.join(base, 'BTQ', 'btq_wallet_settings.json')
    elif IS_MAC:
        path = os.path.expanduser(
            '~/Library/Application Support/BTQ/btq_wallet_settings.json'
        )
    else:
        path = os.path.expanduser('~/.config/BTQ/btq_wallet_settings.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def get_btqd_exe_name() -> str:
    """Return the btqd binary filename for the current platform."""
    return 'btqd.exe' if IS_WIN else 'btqd'


def find_btqd() -> str:
    """
    Search common platform-specific locations for the btqd binary.
    Returns the absolute path string, or '' if not found.
    """
    if IS_WIN:
        return _find_btqd_windows()
    elif IS_MAC:
        return _find_btqd_mac()
    else:
        return _find_btqd_linux()


def find_btq_configs() -> list:
    """
    Return a list of existing btq.conf paths for the current platform.
    Searches all standard locations across Windows, Linux, and macOS.
    """
    appdata = os.environ.get('APPDATA', '')
    home = os.path.expanduser('~')
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()
    candidates = [
        os.path.join(appdata, 'BTQ', 'btq.conf'),
        os.path.join(appdata, 'BTQ', 'test', 'btq.conf'),
        os.path.join(home, '.btq', 'btq.conf'),
        os.path.join(home, 'btq-data', 'btq.conf'),
        os.path.join(script_dir, 'btq.conf'),
        # Linux / macOS paths
        os.path.expanduser('~/.config/BTQ/btq.conf'),
        os.path.expanduser('~/.BTQ/btq.conf'),
    ]
    return [p for p in candidates if os.path.exists(p)]


def get_btqconf_default_path() -> str:
    """
    Return the canonical btq.conf path displayed in the Settings help text
    for the current platform.
    """
    if IS_WIN:
        return os.path.join(os.environ.get('APPDATA', '~'), 'BTQ', 'btq.conf')
    elif IS_MAC:
        return os.path.expanduser(
            '~/Library/Application Support/BTQ/btq.conf'
        )
    else:
        return os.path.expanduser('~/.config/BTQ/btq.conf')


def create_shortcut(script_path: str, python_path: str, icon_path: str,
                    settings: dict, save_settings_fn) -> bool:
    """
    Create a desktop shortcut for the wallet application.

    Parameters
    ----------
    script_path      : Absolute path to simple_wallet_gui.py (or the frozen exe).
    python_path      : Absolute path to the Python interpreter to use.
    icon_path        : Absolute path to the icon file (.png preferred; .ico used
                       on Windows if available alongside .png).
    settings         : The application settings dict (will be mutated on success).
    save_settings_fn : Callable(settings) that persists the settings dict to disk.

    Returns True on success, False otherwise.
    """
    if IS_WIN:
        return _create_shortcut_windows(script_path, python_path,
                                        icon_path, settings, save_settings_fn)
    elif IS_LINUX:
        return _create_shortcut_linux(script_path, python_path,
                                      icon_path, settings, save_settings_fn)
    elif IS_MAC:
        return _create_shortcut_mac(script_path, python_path,
                                    icon_path, settings, save_settings_fn)
    return False


def secure_settings_file(path: str):
    """
    Apply restrictive file permissions to the settings JSON so that only
    the current OS user can read or write it.
    """
    if IS_WIN:
        _secure_settings_windows(path)
    elif IS_LINUX:
        _secure_settings_linux(path)
    elif IS_MAC:
        _secure_settings_mac(path)


def get_subprocess_kwargs() -> dict:
    """
    Return extra kwargs for subprocess.Popen that hide the console window
    on Windows and detach the process on POSIX systems.
    """
    if IS_WIN:
        return {'creationflags': 0x08000000}   # CREATE_NO_WINDOW
    else:
        return {'start_new_session': True}
