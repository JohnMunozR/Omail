#!/usr/bin/env python3
"""
Gmail fetcher daemon for Omarchy.
Fetches emails from Gmail via IMAP and outputs them in JSON format.
"""

import os
import json
import imaplib
import email
import re
import sys
import argparse
from typing import List, Dict, Any, Optional, Tuple, Set

from text_engine import EmailParser


class ConfigProvider:
    """Handles retrieval of configuration and credentials."""

    @staticmethod
    def get_credentials() -> Tuple[Optional[str], Optional[str]]:
        """Retrieves email and app password from environment or config file."""
        user = os.environ.get('OMAIL_USER')
        password = os.environ.get('OMAIL_PASS')

        config_path = os.path.expanduser('~/.config/omail/credentials.json')
        if (not user or not password) and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    user = user or config.get('email')
                    password = password or config.get('app_password')
            except Exception:
                pass
        return user, password


class GmailClient:
    """Handles communication with Gmail IMAP server."""

    def __init__(self, user: str, password: str) -> None:
        self.user = user
        self.password = password
        self.mail: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> None:
        """Connects and authenticates to Gmail IMAP."""
        try:
            self.mail = imaplib.IMAP4_SSL('imap.gmail.com')
            self.mail.login(self.user, self.password)
            emit_json({"status": "CONNECTED"})
        except imaplib.IMAP4.error:
            emit_json({"error": "AUTH_FAILED"})
            raise ConnectionError("Authentication failed")
        except Exception as e:
            emit_json({"error": "CONNECTION_ERROR", "details": str(e)})
            raise ConnectionError(f"Connection error: {e}")

    def disconnect(self) -> None:
        """Closes connection and logs out."""
        if self.mail:
            try:
                self.mail.close()
            except Exception:
                pass
            try:
                self.mail.logout()
            except Exception:
                pass

    def fetch_emails(self, offset: int = 0, limit: int = 60) -> Tuple[int, List[Dict[str, Any]]]:
        """Fetches emails with a given offset and limit, returning unread count and latest emails."""
        if not self.mail:
            raise RuntimeError("Not connected to IMAP server.")

        self.mail.select('INBOX', readonly=True)

        status, response = self.mail.search(None, 'UNSEEN')
        if status != 'OK':
            raise Exception("Failed to search UNSEEN emails.")
        unseen_nums: Set[bytes] = set(response[0].split()) if status == 'OK' else set()
        unread_count = len(unseen_nums)

        status_all, response_all = self.mail.search(None, 'ALL')
        all_msg_nums = response_all[0].split() if status_all == 'OK' else []

        status_primary, response_primary = self.mail.search(None, 'ALL', 'X-GM-RAW', 'category:primary')
        primary_nums: Set[bytes] = set(response_primary[0].split()) if status_primary == 'OK' else set()

        recent_emails: List[Dict[str, Any]] = []

        if len(all_msg_nums) > 0:
            latest_nums = all_msg_nums[::-1]
            start_idx = offset
            end_idx = start_idx + limit
            latest_nums = latest_nums[start_idx:end_idx]

            for num in latest_nums:
                typ, msg_data = self.mail.fetch(num, '(UID X-GM-THRID BODY.PEEK[]<0.102400>)')
                if typ != 'OK':
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        header_line = response_part[0].decode('utf-8', errors='ignore')

                        uid_match = re.search(r'UID (\d+)', header_line)
                        uid = uid_match.group(1) if uid_match else None

                        thrid_match = re.search(r'X-GM-THRID (\d+)', header_line)
                        url = "https://mail.google.com/mail/u/0/#inbox"
                        if thrid_match:
                            thrid_decimal = int(thrid_match.group(1))
                            thrid_hex = hex(thrid_decimal)[2:]
                            url = f"https://mail.google.com/mail/u/0/#inbox/{thrid_hex}"

                        category = "Inbox" if num in primary_nums else "Other"

                        msg = email.message_from_bytes(response_part[1])
                        subject = EmailParser.decode_mime_words(msg.get('Subject', ''))
                        sender = EmailParser.decode_mime_words(msg.get('From', ''))
                        raw_date = str(msg.get('Date', ''))
                        date = EmailParser.parse_date(raw_date)
                        
                        body = EmailParser.get_plain_text(msg)
                        if len(body) > 15000:
                            body = body[:14997] + "..."

                        is_unread = num in unseen_nums

                        recent_emails.append({
                            "uid": uid,
                            "from": sender,
                            "subject": subject,
                            "date": date,
                            "body": body,
                            "url": url,
                            "category": category,
                            "is_unread": is_unread
                        })

        return unread_count, recent_emails


_RE_UID = re.compile(r'^\d+$')


def emit_json(payload: Dict[str, Any]) -> None:
    """Emits JSON payload and flushes the stdout buffer."""
    print(json.dumps(payload), flush=True)


def main() -> None:
    user, password = ConfigProvider.get_credentials()

    if not user or not password:
        emit_json({"error": "NOT_LOGGED_IN"})
        return

    parser = argparse.ArgumentParser()
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--limit', type=int, default=60)
    parser.add_argument('--mark-read', type=str, help='Mark email UID as read')
    args = parser.parse_args()

    client = GmailClient(user, password)

    try:
        client.connect()

        if args.mark_read:
            # S1: Validate UID to prevent IMAP command injection
            if not _RE_UID.match(args.mark_read):
                emit_json({"error": "INVALID_UID"})
                return
            client.mail.select('INBOX', readonly=False)
            client.mail.uid('STORE', args.mark_read.encode('utf-8'), '+FLAGS', '\\Seen')
            emit_json({"status": "READ_MARKED", "uid": args.mark_read})
            return

        unread_count, emails = client.fetch_emails(offset=args.offset, limit=args.limit)

        # Diffing logic
        has_new = False
        if args.offset == 0:
            last_ids_path = os.path.expanduser('~/.config/omail/last_ids.json')
            current_ids = [e['url'] for e in emails if e['category'] == 'Inbox']
            try:
                if os.path.exists(last_ids_path):
                    with open(last_ids_path, 'r') as f:
                        old_ids = set(json.load(f))
                    for cid in current_ids:
                        if cid not in old_ids:
                            has_new = True
                            break
            except (OSError, json.JSONDecodeError) as err:
                print(f"Error reading last_ids.json: {err}", file=sys.stderr)

            # Save current ids
            try:
                os.makedirs(os.path.dirname(last_ids_path), exist_ok=True)
                with open(last_ids_path, 'w') as f:
                    json.dump(current_ids, f)
            except OSError as err:
                print(f"Error writing last_ids.json: {err}", file=sys.stderr)

        emit_json({
            "unread_count": unread_count,
            "emails": emails,
            "user_email": user,
            "has_new": has_new,
            "error": None
        })
    except Exception as e:
        err_msg = str(e)
        if "Authentication failed" not in err_msg and "Connection error:" not in err_msg:
            emit_json({
                "unread_count": 0,
                "emails": [],
                "error": err_msg
            })
    finally:
        client.disconnect()


if __name__ == '__main__':
    main()
