# BTQ Wallet

> **by cypherpunks, for cypherpunks**

A desktop wallet for **Bitcoin Quantum (BTQ)** — a post-quantum blockchain secured by Dilithium lattice-based signatures, resistant to attacks from quantum computers.

No accounts. No cloud. No tracking. Your keys, your coins.

---

## What is BTQ?

Bitcoin Quantum is a testnet blockchain that replaces ECDSA with **CRYSTALS-Dilithium**, a post-quantum cryptographic signature scheme. It is designed to remain secure even against adversaries with access to large-scale quantum computers — a threat that ECDSA-based blockchains are not immune to.

This wallet is a lightweight GUI to interact with a local `btqd` node over JSON-RPC.

---

## Features

- Full wallet management — balances, addresses, send & receive
- Post-quantum address generation (Dilithium signatures)
- QR code display for receiving funds
- Transaction history with confirmations
- Network & blockchain stats
- **Session lock** — PIN-protected, auto-locks on inactivity
- **Encrypted backups** — AES-256-CBC exports (`.btqenc`) with PBKDF2 key derivation
- **Clipboard auto-clear** — copied addresses wiped after N seconds
- **Large-send confirmation** — extra prompt above a configurable threshold
- **Address reuse warning** — flags previously-used destination addresses
- **Node integrity check** — SHA-256 verification of `btqd.exe` before launch
- **Hardened settings file** — restricted to owner read/write via NTFS ACLs
- Multi-language UI: English, Español, Русский, 中文

---

## Requirements

| Dependency | Version | Notes |
|---|---|---|
| Python | 3.9+ | |
| PyQt5 | 5.15+ | GUI framework |
| qrcode[pil] | 7.0+ | QR code generation |
| cryptography | 41.0+ | Encrypted backups (optional but recommended) |
| BTQ node (`btqd.exe`) | 0.3.0+ | Must be running for wallet to connect |

---

## Installation

### Windows

Double-click **`launch.bat`** — it handles the virtual environment and dependencies automatically.

Or from a terminal:

```bat
git clone https://github.com/adrianrozadagarcia/BTQ-Wallet.git
cd BTQ-Wallet
launch.bat
```

### Linux

```bash
# 1. Install system prerequisites (Debian/Ubuntu example)
sudo apt install python3 python3-venv python3-pip python3-pyqt5

# 2. Clone and launch
git clone https://github.com/adrianrozadagarcia/BTQ-Wallet.git
cd BTQ-Wallet
chmod +x launch.sh start_node.sh
./launch.sh
```

On Fedora/RHEL: `sudo dnf install python3 python3-qt5`  
On Arch: `sudo pacman -S python python-pyqt5`

**Optional — desktop launcher:**

```bash
# Install for the current user (shows up in your app menu)
cp btq-wallet.desktop ~/.local/share/applications/
# Edit the Exec path to point to your clone directory, then:
update-desktop-database ~/.local/share/applications/
```

### macOS

```bash
# Install prerequisites
brew install python pyqt@5

# Clone and launch
git clone https://github.com/adrianrozadagarcia/BTQ-Wallet.git
cd BTQ-Wallet
chmod +x launch.sh start_node.sh
./launch.sh
```

### Manual (any platform)

```bash
python3 -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
python simple_wallet_gui.py
```

---

## Node setup

The wallet requires a local BTQ node. Download the binary for your platform from the [BTQ releases page](https://github.com/btq-ag/btq-core/releases).

| Platform | Binary | Config path |
|---|---|---|
| Windows | `btqd.exe` | `%APPDATA%\BTQ\btq.conf` |
| Linux | `btqd` | `~/.btq/btq.conf` |
| macOS | `btqd` | `~/Library/Application Support/BTQ/btq.conf` |

Create `btq.conf`:

```ini
testnet=1
server=1
rpcuser=youruser
rpcpassword=yourpassword
rpcallowip=127.0.0.1
```

**Windows:** use **Settings → BTQ Node → Start Node** or run `start_node.bat`.

**Linux / macOS:** place `btqd` next to the wallet (or in `~/.local/bin/`), make it executable (`chmod +x btqd`), then use **Settings → BTQ Node → Start Node** or run `./start_node.sh`.

> **Windows note:** downloaded executables may be blocked by SmartScreen. The wallet handles this automatically (`Unblock-File`) on first launch.  
> **Linux note:** if `btqd` was downloaded (not installed via package manager), run `chmod +x btqd` before first use.

---

## Security

- Private keys **never leave your machine** — all signing happens inside `btqd`
- The wallet communicates with the node over **localhost only** (127.0.0.1)
- Settings file (`btq_wallet_settings.json`) is restricted to the current OS user
- Encrypted backups use AES-256-CBC with a 100,000-iteration PBKDF2 key derivation
- PIN is stored as a SHA-256 hash — the plaintext PIN is never written to disk
- Clipboard is cleared on copy (configurable timer) and on application exit

For reporting vulnerabilities, see [SECURITY.md](SECURITY.md).

---

## Information

```
"Privacy is necessary for an open society in the electronic age."
  — A Cypherpunk's Manifesto, Eric Hughes, 1993
```

BTQ Wallet is built on the belief that financial privacy is a fundamental right, not a privilege. Quantum-resistant cryptography is not paranoia — it is preparation.

**Principles this wallet is designed around:**

- No telemetry, no analytics, no opt-outs needed
- No remote servers — every bit of data stays on your hardware
- Open source — read every line, trust no one blindly
- Post-quantum by default — Dilithium signatures from day one
- Minimal surface area — no browser engine, no Electron, no web stack

```
by cypherpunks, for cypherpunks
```

---

## License

**Public domain** — [Unlicense](LICENSE).

No copyright. No restrictions. No conditions.
Take it, fork it, sell it, change it, do whatever you want with it.
Knowledge belongs to everyone.
