---
id: daemon
type: module-design
status: active
title: Daemon — Gmail IMAP Fetcher and Markdown Sanitizer
parent: architecture
---

## Responsibility

Provides the CLI entrypoint (`fetch_gmail.py`) and the email parsing/sanitization engine (`text_engine.py`):

- **Credential management (`ConfigProvider`, `--save-credentials`):** Resolves Gmail credentials from `OMAIL_USER`/`OMAIL_PASS` environment variables or `~/.config/omail/credentials.json`, and persists new credentials from `stdin` with `0600` file permissions.
- **IMAP operations (`GmailClient`):** Connects to `imap.gmail.com` via SSL, emits an initial `{"status": "CONNECTED"}` frame, fetches paginated messages (`--offset`, `--limit`) using `BODY.PEEK[]<0.102400>`, `UID`, and `X-GM-THRID`, classifies `Inbox` (`X-GM-RAW "category:primary"`) vs `Other`, and marks messages read (`--mark-read <uid>`).
- **New-mail diffing:** On first-page fetches (`--offset 0`), compares current `Inbox` thread URLs against `~/.config/omail/last_ids.json` to compute `has_new`.
- **Safe Markdown extraction (`EmailParser`, `HTMLTextExtractor`):** Decodes MIME headers/parts, normalizes dates to ISO 8601, strips invisible Unicode formatting characters, converts HTML to safe Markdown (or escapes Markdown metacharacters in `text/plain` fallback), and enforces the resource and link security invariants defined in `architecture`.

## Boundary

- **Allowed dependencies:** Python 3 standard library only (`imaplib`, `email`, `html`, `re`, `json`, `os`, `sys`, `argparse`, `typing`). Within the module, `fetch_gmail.py` imports `EmailParser` from `text_engine.py`, and `tests/test_text_engine.py` tests `text_engine.py`.
- **Forbidden reaches:** `text_engine.py` must remain pure parsing logic with no network, filesystem, or environment access. Neither file may depend on QML/Quickshell or external Python packages.

## Known Limitations

- **Message body truncation:** `GmailClient.fetch_emails` fetches at most 100 KB per message (`BODY.PEEK[]<0.102400>`) and truncates the extracted Markdown body at 15,000 characters (`14997 + "..."`).

