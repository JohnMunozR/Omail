---
id: goal-and-requirements
type: goal-and-requirements
status: active
title: Omail — Goal and Requirements
---

## Goal

Omail is a lightweight Gmail bar-widget plugin (`nmr.omail`) for the Omarchy desktop shell (Quickshell). It gives desktop users instant visibility into incoming Gmail messages and a distraction-free, privacy-preserving Markdown reader panel directly in the top bar—without keeping a browser tab open or exposing the user to tracking pixels, remote images, or unsafe links.

## Audience

Omarchy shell users on Linux who use a single Gmail account and want fast, local notification and triage (read or open in browser) from their desktop bar.

## Capabilities

- **Stateful Bar Indicator:** Displays a top-bar icon that switches between a default envelope (`󰇰`) and a new-mail envelope (`󰇮`) when new messages arrive in the Primary Inbox, plus right-click manual refresh and IPC commands (`open`, `close`, `toggle`, `refresh`).
- **Desktop & Audio Notifications:** Triggers a desktop notification (`notify-send`) and sound alert (`paplay`) when polling detects newly arrived Primary Inbox threads compared against locally cached thread URLs (`~/.config/omail/last_ids.json`).
- **Strict Non-Resource Markdown Reader:** Parses HTML and plain-text emails locally into a restricted, QML-safe Markdown subset—stripping all images, tracking pixels, scripts, styles, and media tags, neutralizing Markdown image syntax (`![` → `\![`), and permitting only `https://`, `http://`, and `mailto:` links.
- **Inbox / All Filtering & Lazy Pagination:** Lets the user switch between `Inbox` (Gmail `category:primary`) and `All` views, fetching 60 messages initially and lazily loading 20 more at a time on scroll, freeing extra pages when the panel closes.
- **Instant Mark-as-Read & Browser Handoff:** Left-clicking an unread message expands its preview and marks it `\Seen` on Gmail via IMAP UID `STORE`; middle-clicking or double-clicking opens the specific Gmail thread URL (`#inbox/<hex-thrid>`) in the default browser.
- **In-Panel Account Linking:** Provides an inline login form for Gmail address + Google App Password, storing credentials locally at `~/.config/omail/credentials.json` with `0600` permissions (or reading `OMAIL_USER` / `OMAIL_PASS` from the environment) and supporting one-click account unlinking.

## Non-Goals

- **Full email client workflows:** Composing, replying, forwarding, deleting, archiving, or managing labels/folders inside the panel.
- **Multi-account or generic IMAP support:** Supporting multiple simultaneous accounts or non-Gmail IMAP servers (relies on Gmail-specific `X-GM-RAW` and `X-GM-THRID` extensions).
- **Rich HTML / remote media rendering:** Rendering remote images, CSS layouts, or embedded media in emails.
- **Numeric unread badge in the bar:** The bar button intentionally shows only the stateful envelope icon (`󰇰` / `󰇮`) rather than a numeric unread count badge.

## Principles

- **Privacy and security by construction:** Untrusted email content never loads external resources or executes scripts; link schemes are validated both during HTML-to-Markdown extraction and before opening URLs in QML, and IMAP UIDs are strictly validated as digits before `STORE`.
- **Zero third-party Python dependencies:** The backend relies exclusively on the Python 3 standard library (`imaplib`, `email`, `html.parser`, `json`, `re`) so it runs out of the box on any system with Python 3.

