#!/usr/bin/env bash
# BTQ Wallet launcher — Linux / macOS
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " =========================================="
echo "   BTQ Wallet - Starting..."
echo " =========================================="
echo ""

# ── Find Python 3 ──────────────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | awk '{print $2}')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
            PYTHON="$cmd"
            echo " [OK] Python $ver found ($cmd)"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo " [ERROR] Python 3.9+ not found."
    echo ""
    echo " Install it with your package manager, for example:"
    echo "   Debian/Ubuntu:  sudo apt install python3 python3-venv python3-pip"
    echo "   Fedora:         sudo dnf install python3"
    echo "   Arch:           sudo pacman -S python"
    echo "   macOS:          brew install python"
    echo ""
    exit 1
fi

# ── PyQt5 system check (optional hint) ─────────────────────────────────────
# PyQt5 sometimes needs system Qt libs on Linux; pip alone isn't always enough.
if ! "$PYTHON" -c "import PyQt5" &>/dev/null 2>&1; then
    if command -v apt-get &>/dev/null; then
        echo " [INFO] PyQt5 not yet installed. On Debian/Ubuntu you can also run:"
        echo "        sudo apt install python3-pyqt5"
    fi
fi

# ── Create virtual environment ─────────────────────────────────────────────
if [ ! -f ".venv/bin/python" ]; then
    echo " Creating virtual environment..."
    "$PYTHON" -m venv .venv
    echo " [OK] Virtual environment created."
fi

VENV_PYTHON=".venv/bin/python"

# ── Install / update dependencies ─────────────────────────────────────────
echo " Checking dependencies..."
"$VENV_PYTHON" -m pip install --upgrade pip -q --disable-pip-version-check
"$VENV_PYTHON" -m pip install -r requirements.txt -q --disable-pip-version-check
echo " [OK] Dependencies ready."
echo ""

# ── Launch ─────────────────────────────────────────────────────────────────
echo " Opening BTQ Wallet..."
echo ""
"$VENV_PYTHON" simple_wallet_gui.py
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo " [!] Wallet exited with error code $EXIT_CODE."
fi
