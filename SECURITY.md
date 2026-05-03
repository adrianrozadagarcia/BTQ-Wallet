# Security Policy

## Supported Versions

This project is currently in active development on the `main` branch.
Only the latest commit is considered supported.

## Reporting a Vulnerability

If you discover a security vulnerability in BTQ Wallet, please report it
**privately** — do not open a public GitHub issue.

**How to report:**

1. Open a [GitHub Security Advisory](https://github.com/adrianrozadagarcia/BTQ-Wallet/security/advisories/new)
   on this repository (preferred), **or**
2. Send an encrypted email to the maintainer. PGP key available on request.

Please include:
- A description of the vulnerability and its potential impact
- Steps to reproduce or a proof-of-concept (if applicable)
- Any suggested mitigations

You will receive a response within **72 hours**. We ask that you give us
reasonable time to address the issue before any public disclosure.

## Scope

Issues we consider in scope:

- Private key or seed exposure
- Bypass of the session lock (PIN)
- Encrypted backup decryption without the passphrase
- RPC credential leakage
- Remote code execution via crafted node responses

Out of scope:

- Attacks that require physical access to an already-unlocked machine
- Vulnerabilities in `btqd` itself (report those upstream to the BTQ Core project)
- Social engineering

## Security Design Notes

- Private keys are **never handled** by the wallet GUI — all signing is delegated to `btqd`
- The wallet communicates with `btqd` over **localhost only**
- No data is sent to any remote server
- The session PIN is stored as a SHA-256 hash; plaintext is never written to disk
- Encrypted backups use AES-256-CBC with PBKDF2-HMAC-SHA256 (100,000 iterations)
