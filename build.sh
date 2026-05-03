#!/usr/bin/env bash
# Build a standalone BTQWallet binary for Linux or macOS
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " =========================================="
echo "   BTQ Wallet — Building standalone binary"
echo " =========================================="
echo ""

# ── Find Python 3.9+ ──────────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | awk '{print $2}')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
            PYTHON="$cmd"
            echo " [OK] Python $ver ($cmd)"
            break
        fi
    fi
done

[ -z "$PYTHON" ] && { echo " [ERROR] Python 3.9+ not found."; exit 1; }

# ── Virtual environment ───────────────────────────────────────────────────
if [ ! -f ".venv/bin/python" ]; then
    echo " Creating virtual environment..."
    "$PYTHON" -m venv .venv
fi

# ── Dependencies ──────────────────────────────────────────────────────────
echo " Installing dependencies..."
.venv/bin/pip install --upgrade pip -q --disable-pip-version-check
.venv/bin/pip install -r requirements.txt -q --disable-pip-version-check
.venv/bin/pip install pyinstaller -q --disable-pip-version-check

# ── Build ─────────────────────────────────────────────────────────────────
echo " Running PyInstaller..."
.venv/bin/pyinstaller BTQWallet.spec --clean --noconfirm

echo ""
echo " =========================================="
echo "   Build complete!"
echo "   Output: dist/BTQWallet"
echo " =========================================="
echo ""
echo " You can distribute dist/BTQWallet — no Python required."
echo ""
