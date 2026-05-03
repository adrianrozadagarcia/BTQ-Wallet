# BTQ Wallet

> **by cypherpunks, for cypherpunks**

A desktop wallet for **Bitcoin Quantum (BTQ)** — a post-quantum blockchain secured by Dilithium lattice-based signatures, resistant to attacks from quantum computers.

No accounts. No cloud. No tracking. Your keys, your coins.

---

## Quick Start

### Option A — Standalone binary (no Python required)

Download `BTQWallet.exe` (Windows) or `BTQWallet` (Linux/macOS) from the [**Releases page**](https://github.com/adrianrozadagarcia/BTQ-Wallet/releases) and double-click it. That's it.

### Option B — Run from source

| Platform | Command |
|---|---|
| Windows | Double-click **`launch.bat`** |
| Linux | `chmod +x launch.sh && ./launch.sh` |
| macOS | Double-click **`launch.command`** |

The launcher scripts handle everything: Python version check, virtual environment, dependency install.

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
