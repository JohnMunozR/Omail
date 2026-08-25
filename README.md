# Omail

A powerful and seamless Gmail client plugin for the Omarchy shell environment. Omail provides a system tray unread counter and an interactive panel to read emails directly from your desktop in a clean, distration-free format.

## Features

- **Bar Widget Integration:** A sleek bar icon that displays your unread email count.
- **Reader View:** Emails are parsed from HTML to clean, readable Markdown right inside the Omarchy UI. Invisible marketing characters, empty links, and messy tables are stripped away.
- **Instant Mark as Read:** Clicking an email to read it locally marks it as read immediately and syncs with Gmail via IMAP.
- **Notifications:** Receive desktop notifications and sounds when new mail arrives in your inbox.
- **Quick Actions:** Middle-click or double-click to instantly open the email in Gmail on your web browser.

## Requirements

- **Omarchy Shell**
- **Python 3** (Used for the background daemon)
- Python packages (standard library): `imaplib`, `email`, `html`, `re`, `json`
- **paplay** (for sound notifications)
- **notify-send** (for desktop notifications)

## Installation

You can install Omail directly from the Omarchy Marketplace using the command line:

```bash
omarchy plugin install nmr.omail
```

Alternatively, you can clone it manually:

```bash
omarchy plugin clone https://github.com/JohnMunozR/Omail
```

## Setup and Credentials

Since Google no longer allows basic authentication, you will need to use an App Password:

1. Go to your Google Account settings -> Security.
2. Enable 2-Step Verification if it isn't already.
3. Go to App Passwords and create a new password for "Omail" or "Custom app".
4. When you first launch Omail from the Omarchy bar, click the settings gear to enter your Gmail address and the 16-character App Password.

The credentials are saved locally in your user configuration directory at `~/.config/omail/credentials.json`.

## Usage

- **Click the bar widget** to toggle the email panel.
- **Left-click an email** in the list to expand it and read its content (this automatically marks it as read in Gmail).
- **Double-click or middle-click an email** to open it externally in your web browser.
- **Click links** inside the email to navigate directly to them (this will close the panel).
- **Right-click the bar widget** to manually refresh the inbox.

## Security and Privacy

Omail runs locally on your machine.
Your credentials are never sent anywhere except directly to Google's IMAP servers via SSL.
All emails are processed locally using a built-in Markdown extraction engine.

## License

This project is open-sourced under the MIT License.
