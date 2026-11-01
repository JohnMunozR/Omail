---
id: architecture
type: architecture-design
status: active
title: Omail — Architecture Design
parent: goal-and-requirements
---

## Drivers

- **Process isolation between UI and network/parsing:** Quickshell QML stays responsive on the UI thread by delegating blocking IMAP SSL operations, MIME decoding, and HTML sanitization to short-lived Python CLI invocations over `stdout`/`stdin` JSON.
- **Defense in depth against untrusted email payloads:** Qt's `Text.MarkdownText` can fetch remote images if `![alt](url)` syntax or raw HTML slips through, so sanitization must happen in the backend before payloads reach QML, with link scheme enforcement repeated at click time in QML.

## Topology & Module Boundaries

Omail is structured as two modules connected by a JSON-over-stdio process boundary:

```
[ ui (Quickshell QML) ]  ──(spawns Process / JSON stdio)──▶  [ daemon (Python 3 CLI) ]
                                                                    │
                                                                    ▼
                                                        Gmail IMAP SSL + ~/.config/omail/
```

- **`ui` (`ui/BarWidget.qml`, `ui/Panel.qml`, `manifest.json`):** Quickshell bar widget and popup panel. Owns polling timer, IPC handler (`nmr.omail`), desktop/sound notifications (`notify-send`, `paplay`), view state, and user interaction. Depends on `daemon` by spawning `daemon/fetch_gmail.py`.
- **`daemon` (`daemon/fetch_gmail.py`, `daemon/text_engine.py`, `tests/test_text_engine.py`):** Stateless CLI worker and HTML-to-Markdown sanitizer. Owns credential persistence (`~/.config/omail/credentials.json`), Gmail IMAP communication (`imap.gmail.com`), new-mail diffing (`~/.config/omail/last_ids.json`), and safe Markdown extraction. Never imports or depends on `ui`.

## Decisions

- **Short-lived CLI invocations instead of a persistent background socket:** Each poll (60s), pagination request, mark-as-read action, or credential save runs `daemon/fetch_gmail.py` as a Quickshell `Process` and communicates via newline-flushed JSON objects (`CONNECTED`, payload, or `error`) to avoid managing a long-lived daemon lifecycle or orphan processes when the shell restarts.
- **Gmail IMAP extensions (`X-GM-RAW`, `X-GM-THRID`):** Instead of local heuristics or full Gmail REST API OAuth flows, `daemon` uses Google App Passwords over IMAP SSL and queries `X-GM-RAW "category:primary"` to classify `Inbox` vs `Other` and `X-GM-THRID` (converted to hex) to build direct web thread URLs (`https://mail.google.com/mail/u/0/#inbox/<hex>`).

## Invariants

- **No remote resource loading from email content:** `daemon` strips `<img>` tags, `<script>`/`<style>`/media blocks, escapes `<` to `&lt;`, and escapes `![` to `\![` in both HTML and plain-text bodies so Qt `Text.MarkdownText` never fetches external resources.
- **Link scheme whitelist (`https://`, `http://`, `mailto:`):** Enforced both when emitting Markdown links in `daemon` and in `Panel.qml`'s `onLinkActivated` handler before calling `Qt.openUrlExternally`.
- **IMAP command injection guard:** `--mark-read` validates UIDs against `^\d+$` before issuing `UID STORE +FLAGS \Seen`.
- **Credential file permissions:** `--save-credentials` reads JSON from `stdin` (never CLI args, avoiding process-list leaks) and writes `~/.config/omail/credentials.json` with `0600` permissions.

## Out of scope

- **Unused repository artifacts:** `ui/Model.js` (leftover clock/calendar template logic), `test_imap.py`, and `out*.json` in the repository root are unused artifacts and not part of the system architecture.

