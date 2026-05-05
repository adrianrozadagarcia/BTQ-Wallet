# BTQ Wallet

> **by cypherpunks, for cypherpunks**

A desktop wallet for **Bitcoin Quantum (BTQ)** — a post-quantum blockchain secured by Dilithium lattice-based signatures, resistant to attacks from quantum computers.

No accounts. No cloud. No tracking. Your keys, your coins.

---

## Quick Start

### Option A — Standalone binary *(recommended, no Python required)*

Download the binary for your platform from the [**Releases page**](https://github.com/adrianrozadagarcia/BTQ-Wallet/releases/latest) and run it:

| Platform | File | How to run |
|---|---|---|
| Windows | `BTQWallet-windows.exe` | Double-click |
| Linux | `BTQWallet-linux` | `chmod +x BTQWallet-linux && ./BTQWallet-linux` |
| macOS | `BTQWallet-macos` | `chmod +x BTQWallet-macos && ./BTQWallet-macos` |

**One-liner (PowerShell / Windows):**
```powershell
irm https://github.com/adrianrozadagarcia/BTQ-Wallet/releases/latest/download/BTQWallet-windows.exe -OutFile BTQWallet.exe; Start-Process BTQWallet.exe
```

**One-liner (Linux/macOS):**
```bash
curl -fsSL https://github.com/adrianrozadagarcia/BTQ-Wallet/releases/latest/download/BTQWallet-linux -o BTQWallet && chmod +x BTQWallet && ./BTQWallet
```

### Option B — Run from source

#### First-time install (creates venv, installs deps, adds desktop shortcut)

| Platform | Command |
|---|---|
| Windows | Double-click **`install.bat`** |
| Linux / macOS | `chmod +x install.sh && ./install.sh` |

#### Launch after installing

| Platform | Command |
|---|---|
| Windows | Double-click **`launch.bat`** |
| Linux | `./launch.sh` |
| macOS | Double-click **`launch.command`** |

The scripts handle everything: Python version check, virtual environment, dependency install.

---

## What is BTQ?

Bitcoin Quantum is a testnet blockchain that replaces ECDSA with **CRYSTALS-Dilithium**, a post-quantum cryptographic signature scheme. It is designed to remain secure even against adversaries with access to large-scale quantum computers — a threat that ECDSA-based blockchains are not immune to.

This wallet is a lightweight GUI to interact with a local `btqd` node over JSON-RPC.

---

## Features

- Full wallet management — balances, addresses, send & receive
- Post-quantum address generation (Dilithium signatures)
- QR code display for receiving funds
- **Transaction detail view** — double-click any transaction for full details + Copy TXID
- **Export transactions to CSV** — one-click export of the full history
- **Multi-output send** — send to multiple recipients in a single transaction
- **Balance history chart** — live line chart of balance over time in the Balance tab
- **Real-time address validation** — ✓ / ✗ indicator while typing the destination address
- **Backup reminder** — banner alert after 7 days without a backup
- Network & blockchain stats
- **Wallet encryption** — `encryptwallet` / `walletpassphrase` / `walletlock` via Settings
- **Fee selector** — Slow / Normal / Fast / Custom with live BTQ estimate
- **Coin control** — select specific UTXOs to spend
- **Session lock** — PIN-protected, auto-locks on inactivity
- **Encrypted backups** — AES-256-CBC exports (`.btqenc`) with PBKDF2 key derivation
- **System tray** — minimize to tray, incoming transaction notifications
- **Tor support** — route node traffic through Tor (`-proxy` / `-onlynet=onion`)
- **Clipboard auto-clear** — copied addresses wiped after N seconds
- **Large-send confirmation** — extra prompt above a configurable threshold
- **Address reuse warning** — flags previously-used destination addresses
- **Node integrity check** — SHA-256 verification of `btqd` before launch
- **Hardened settings file** — owner read/write only (NTFS ACLs / chmod 600)
- Multi-language UI: English, Español, Русский, 中文
- Windows · Linux · macOS

---

## Node setup

The wallet requires a local BTQ node. Download the binary for your platform from the [BTQ releases page](https://github.com/btq-ag/btq-core/releases).

| Platform | Binary | Config path |
|---|---|---|
| Windows | `btqd.exe` | `%APPDATA%\BTQ\btq.conf` |
| Linux | `btqd` | `~/.config/BTQ/btq.conf` |
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

## Linux Installation (detailed)

### Requirements

| Package | Minimum | Notes |
|---|---|---|
| Python | 3.9+ | `python3 --version` to check |
| python3-venv | any | Needed to create the virtual environment |
| python3-pip | any | Usually bundled with Python |
| PyQt5 | 5.15+ | Can be installed via pip **or** the system package manager |

### Step-by-step

**1 — Clone the repository**
```bash
git clone https://github.com/adrianrozadagarcia/BTQ-Wallet.git
cd BTQ-Wallet
```

**2 — Run the installer**
```bash
chmod +x install.sh
./install.sh
```

The installer will:
- Verify Python 3.9+ is available
- Check that `python3-venv` is installed
- Create a `.venv` virtual environment
- Install all Python dependencies (`PyQt5`, `qrcode`, `cryptography`, …)
- Create a `.desktop` shortcut in `~/.local/share/applications/` (app menu) and `~/Desktop/` (if it exists)

**3 — Launch**
```bash
./launch.sh
```

Or use the desktop shortcut created in step 2.

### Installing system dependencies by distro

If `install.sh` warns that PyQt5 could not be installed via pip, install it through your package manager:

```bash
# Debian / Ubuntu
sudo apt install python3 python3-venv python3-pip python3-pyqt5

# Fedora
sudo dnf install python3 python3-pip python3-qt5

# Arch Linux
sudo pacman -S python python-pyqt5

# openSUSE
sudo zypper install python3 python3-Qt5
```

### Setting up the node on Linux

```bash
# Download btqd from the BTQ releases page and place it next to the wallet
chmod +x btqd

# Create the config directory and file
mkdir -p ~/.config/BTQ
cat > ~/.config/BTQ/btq.conf << 'EOF'
testnet=1
server=1
rpcuser=youruser
rpcpassword=yourpassword
rpcallowip=127.0.0.1
EOF

# Start the node
./btqd -conf=$HOME/.config/BTQ/btq.conf
```

Or use **Settings → BTQ Node → Start Node** inside the wallet — it will auto-detect `btqd` if it is in the same folder or in `~/.local/bin/`.

### Desktop shortcut details

The installer creates two files:

| File | Purpose |
|---|---|
| `~/.local/share/applications/btq-wallet.desktop` | GNOME / KDE app menu entry |
| `~/Desktop/btq-wallet.desktop` | Desktop icon (if `~/Desktop` exists) |

On **GNOME 3.28+** the desktop icon is automatically marked as trusted (no "untrusted launcher" prompt).  
On **KDE Plasma** the file is trusted by default.

To remove the shortcut manually:
```bash
rm ~/.local/share/applications/btq-wallet.desktop ~/Desktop/btq-wallet.desktop
update-desktop-database ~/.local/share/applications
```

---

## Building from source (advanced)

To build a standalone binary yourself:

```bat
REM Windows
build.bat
REM Output: dist\BTQWallet.exe
```

```bash
# Linux / macOS
chmod +x build.sh && ./build.sh
# Output: dist/BTQWallet
```

Both scripts create a `.venv`, install [PyInstaller](https://pyinstaller.org), and produce a single-file executable with no external dependencies.

**Runtime requirements (source only):**

| Dependency | Version |
|---|---|
| Python | 3.9+ |
| PyQt5 | 5.15+ |
| qrcode[pil] | 7.0+ |
| cryptography | 41.0+ |

---

## Security

- Private keys **never leave your machine** — all signing happens inside `btqd`
- The wallet communicates with the node over **localhost only** (127.0.0.1)
- Wallet file encrypted at rest via `encryptwallet` (AES-256 inside btqd)
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
