#!/usr/bin/env bash
# Start the BTQ node (testnet) on Linux / macOS
set -euo pipefail

# ── Locate btqd ────────────────────────────────────────────────────────────
BTQD=""
for candidate in \
    "./btqd" \
    "$HOME/.local/bin/btqd" \
    "/usr/local/bin/btqd" \
    "/usr/bin/btqd"
do
    if [ -x "$candidate" ]; then
        BTQD="$candidate"
        break
    fi
done

if [ -z "$BTQD" ]; then
    echo " [ERROR] btqd not found."
    echo ""
    echo " Download it from https://github.com/btq-ag/btq-core/releases"
    echo " and place it next to this script (./btqd) or in /usr/local/bin/btqd"
    echo ""
    exit 1
fi

# ── Data directory ─────────────────────────────────────────────────────────
if [[ "$(uname)" == "Darwin" ]]; then
    DATADIR="$HOME/Library/Application Support/BTQ"
else
    DATADIR="$HOME/.btq"
fi
mkdir -p "$DATADIR"

# ── Check if already running ───────────────────────────────────────────────
if pgrep -x btqd &>/dev/null; then
    echo " [OK] btqd is already running."
    exit 0
fi

echo ""
echo " ========================================="
echo "   BTQ Node - Testnet"
echo " ========================================="
echo " Binary : $BTQD"
echo " DataDir: $DATADIR"
echo ""

# ── Start ──────────────────────────────────────────────────────────────────
"$BTQD" -testnet -datadir="$DATADIR" -daemon
echo " [OK] Node started in daemon mode."
echo ""
echo " Wait a few seconds, then connect BTQ Wallet."
echo " Log: $DATADIR/testnet/debug.log"
echo ""
