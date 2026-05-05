#!/usr/bin/env bash
# BTQ Wallet — Linux / macOS installer
# Run once to set up the virtual environment, install dependencies,
# and create a desktop shortcut.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " =========================================="
echo "   BTQ Wallet — Installation"
echo " =========================================="
echo ""

# ── Python 3.9+ ────────────────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | awk '{print $2}')
        maj=$(echo "$ver" | cut -d. -f1)
        min=$(echo "$ver" | cut -d. -f2)
        if [ "$maj" -ge 3 ] && [ "$min" -ge 9 ]; then
            PYTHON="$cmd"
            echo " [OK] Python $ver ($cmd)"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo " [ERROR] Python 3.9+ is required but was not found."
    echo ""
    echo "   Debian / Ubuntu:  sudo apt install python3 python3-venv python3-pip"
    echo "   Fedora:           sudo dnf install python3"
    echo "   Arch:             sudo pacman -S python"
    echo "   openSUSE:         sudo zypper install python3"
    echo "   macOS:            brew install python"
    echo ""
    exit 1
fi

# ── python3-venv guard (Debian/Ubuntu split package) ───────────────────────
if ! "$PYTHON" -c "import venv" &>/dev/null 2>&1; then
    echo " [ERROR] The 'venv' module is missing."
    echo "   On Debian / Ubuntu run:  sudo apt install python3-venv"
    exit 1
fi

# ── Virtual environment ────────────────────────────────────────────────────
if [ ! -f ".venv/bin/python" ]; then
    echo " Creating virtual environment..."
    "$PYTHON" -m venv .venv
    echo " [OK] Virtual environment created."
else
    echo " [OK] Virtual environment already exists."
fi

VENV_PY="$SCRIPT_DIR/.venv/bin/python"

# ── Dependencies ───────────────────────────────────────────────────────────
echo " Installing / updating dependencies..."

# PyQt5 hint — pip installs wheels but some distros need system Qt libs
if ! "$VENV_PY" -c "import PyQt5" &>/dev/null 2>&1; then
    echo ""
    echo " [INFO] PyQt5 will be installed from PyPI (binary wheel)."
    echo "        If it fails, install the system package instead:"
    if command -v apt-get &>/dev/null; then
        echo "          sudo apt install python3-pyqt5"
    elif command -v dnf &>/dev/null; then
        echo "          sudo dnf install python3-qt5"
    elif command -v pacman &>/dev/null; then
        echo "          sudo pacman -S python-pyqt5"
    fi
    echo ""
fi

"$VENV_PY" -m pip install --upgrade pip -q --disable-pip-version-check
"$VENV_PY" -m pip install -r requirements.txt -q --disable-pip-version-check
echo " [OK] Dependencies installed."

# ── Desktop shortcut ───────────────────────────────────────────────────────
echo " Creating desktop shortcut..."

# Resolve the best icon available (prefer PNG)
ICON=""
for ext in png ico jpg jpeg; do
    f="$SCRIPT_DIR/assets/btq_wallet.$ext"
    if [ -f "$f" ]; then ICON="$f"; break; fi
done
[ -z "$ICON" ] && ICON="$SCRIPT_DIR/assets/btq_wallet.png"  # fallback (may not exist)

# Run shortcut creation via the venv Python so platform_utils is available
set +e
"$VENV_PY" - <<PYEOF
import sys, os
sys.path.insert(0, '$SCRIPT_DIR/src')
import platform_utils

def _save(s):
    pass  # install.sh does not persist settings; the app does on first launch

platform_utils.create_shortcut(
    script_path      = '$SCRIPT_DIR/src/simple_wallet_gui.py',
    python_path      = '$SCRIPT_DIR/.venv/bin/python',
    icon_path        = '$ICON',
    settings         = {},
    save_settings_fn = _save,
)
PYEOF
SC_EXIT=$?
set -e

if [ $SC_EXIT -eq 0 ]; then
    echo " [OK] Desktop shortcut created."
else
    echo " [WARN] Could not create desktop shortcut (non-fatal)."
    echo "        You can launch the wallet manually with:  ./launch.sh"
fi

# ── Done ───────────────────────────────────────────────────────────────────
echo ""
echo " =========================================="
echo "   Installation complete!"
echo "   Launch the wallet with:  ./launch.sh"
echo " =========================================="
echo ""
