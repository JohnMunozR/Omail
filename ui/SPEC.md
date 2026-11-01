---
id: ui
type: module-design
status: active
title: UI — Omarchy Bar Widget and Reader Panel
parent: architecture
depends-on: [daemon]
---

## Responsibility

Implements the Omarchy shell bar widget (`BarWidget.qml`) and popup email panel (`Panel.qml`) registered by `manifest.json` (`nmr.omail`):

- **Bar widget & lifecycle (`BarWidget.qml`):** Renders the bar button showing the stateful envelope icon (`󰇮` when `hasNewMail` is true, `󰇰` otherwise), polls `daemon/fetch_gmail.py` every 60 seconds and on right-click, exposes the `nmr.omail` `IpcHandler` (`refresh`, `open`, `close`, `show`, `hide`, `toggle`), and fires desktop/audio alerts (`notify-send`, `paplay`) when `has_new` is reported.
- **Process orchestration (`BarWidget.qml`):** Spawns separate Quickshell `Process` instances for initial fetch, lazy pagination (`--offset`, `--limit 20`), marking an email read (`--mark-read`), saving credentials (`--save-credentials` via `stdin`), and unlinking (`rm -f ~/.config/omail/credentials.json`).
- **Popup reader panel (`Panel.qml`):** Hosts the `KeyboardPanel` with `Inbox` / `All` category filter chips, inline Google App Password sign-in view on `NOT_LOGGED_IN` / `AUTH_FAILED`, expandable email cards with Markdown body rendering, middle/double-click thread opening in browser, and scroll-to-bottom pagination that trims `emailsList` back to 60 items on panel close.

## Boundary

- **Allowed dependencies:** Quickshell & Omarchy UI modules (`QtQuick`, `Quickshell`, `Quickshell.Io`, `qs.Commons`, `qs.Ui`), system notification binaries (`/usr/bin/paplay`, `/usr/bin/notify-send`), and the `daemon` CLI interface (`daemon/fetch_gmail.py`) via `Process` stdio.
- **Forbidden reaches:** Never performs direct network/IMAP calls or raw HTML parsing in QML/JS. `ui/Model.js` is an unused template artifact and must not be imported.

## Known Limitations

- **Expanded preview line cap:** `Panel.qml` restricts expanded email bodies to `maximumLineCount: 15` with `Text.ElideRight`, requiring the user to open longer emails in the web browser.

