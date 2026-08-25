# Omail

A powerful and seamless Gmail client plugin for the Omarchy shell environment. Omail provides a system tray unread counter and an interactive panel to read emails directly from your desktop in a clean, distraction-free format.

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

Run the following command to download and enable the plugin directly from GitHub:

```bash
omarchy plugin add https://github.com/JohnMunozR/Omail.git --enable --yes
```

Then restart your shell so the icon appears:
```bash
omarchy restart shell
```

## Setup and Credentials

For security reasons, Google does not allow using your regular password in third-party applications. You will need to create an "App Password":

1. Go to your Google Account **Security Settings**: [https://myaccount.google.com/security](https://myaccount.google.com/security)
2. Ensure you have **2-Step Verification** turned on.
3. In the top search bar, type **"App passwords"** and select that option.
4. Type a name to identify it (for example: `Omail`) and click **Create**.
5. Copy the 16-letter password that appears on the screen (without spaces).
6. **First login:** Click on the new mail icon that appeared on your top bar. The panel will open showing a login form; simply enter your Gmail address along with the **App Password** you generated, and click the link account button.

*(The credentials are saved locally in your user configuration directory at `~/.config/omail/credentials.json`)*

## Usage

- **Click the bar widget** to toggle the email panel.
- **Left-click an email** in the list to expand it and read its content (this automatically marks it as read in Gmail).
- **Double-click or middle-click an email** to open it externally in your web browser.
- **Click links** inside the email to navigate directly to them (this will close the panel).
- **Right-click the bar widget** to manually refresh the inbox.

## Uninstallation

To cleanly remove the plugin from your system, run:

```bash
omarchy plugin remove nmr.omail --yes
omarchy restart shell
```

## Security and Privacy

Omail runs locally on your machine.
Your credentials are never sent anywhere except directly to Google's IMAP servers via SSL.
All emails are processed locally using a built-in Markdown extraction engine.

## License

This project is open-sourced under the MIT License.
