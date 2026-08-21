#!/usr/bin/env python3
"""
Gmail fetcher script for Omarchy daemon.
Fetches unread emails from Gmail via IMAP and outputs them in JSON format.
"""

import os
import json
import imaplib
import email
import re
import argparse
from email.header import decode_header
from html.parser import HTMLParser
from typing import List, Dict, Any, Optional, Tuple, Set
from email.message import Message
from email.utils import parsedate_to_datetime

class HTMLTextExtractor(HTMLParser):
    """Parses HTML content to extract plain text."""
    def __init__(self) -> None:
        super().__init__()
        self.result: List[str] = []
        self.in_style_or_script: bool = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in ('script', 'style'):
            self.in_style_or_script = True
        elif tag in ('br', 'p', 'div', 'tr', 'li'):
            self.result.append('\n')

    def handle_endtag(self, tag: str) -> None:
        if tag in ('script', 'style'):
            self.in_style_or_script = False

    def handle_data(self, data: str) -> None:
        if not self.in_style_or_script:
            text = data.strip()
            if text:
                self.result.append(text + " ")

    def get_text(self) -> str:
        return "".join(self.result).strip()

class EmailParser:
    """Handles parsing and decoding of email messages."""
    
    @staticmethod
    def strip_html(html_content: str) -> str:
        """Strips HTML tags from the given string."""
        try:
            extractor = HTMLTextExtractor()
            extractor.feed(html_content)
            return extractor.get_text()
        except Exception:
            return html_content

    @staticmethod
    def decode_mime_words(s: Optional[str]) -> str:
        """Decodes MIME encoded strings."""
        if not s:
            return ""
        try:
            decoded_words = decode_header(s)
            parts = []
            for word, charset in decoded_words:
                if isinstance(word, bytes):
                    try:
                        parts.append(word.decode(charset or 'utf-8', errors='replace'))
                    except LookupError:
                        parts.append(word.decode('utf-8', errors='replace'))
                else:
                    parts.append(str(word))
            return "".join(parts)
        except Exception:
            return str(s)

    @staticmethod
    def get_plain_text(msg: Message) -> str:
        """Extracts plain text body from an email Message."""
        body_plain = ""
        body_html = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" in content_disposition:
                    continue
                    
                try:
                    payload = part.get_payload(decode=True)
                    if not payload: 
                        continue
                    charset = part.get_content_charset() or 'utf-8'
                    decoded = payload.decode(charset, errors='replace')
                    
                    if content_type == "text/plain":
                        body_plain += decoded + "\n"
                    elif content_type == "text/html":
                        body_html += decoded + "\n"
                except Exception:
                    pass
        else:
            content_type = msg.get_content_type()
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    decoded = payload.decode(charset, errors='replace')
                    if content_type == "text/plain":
                        body_plain += decoded
                    elif content_type == "text/html":
                        body_html += decoded
            except Exception:
                pass

        final_body = body_plain.strip()
        if not final_body and body_html.strip():
            final_body = EmailParser.strip_html(body_html)
            
        if len(final_body) > 2000:
            final_body = final_body[:2000] + "..."
        return final_body.strip()

    @staticmethod
    def parse_date(raw_date: str) -> str:
        """Parses an email date into ISO 8601 format."""
        try:
            dt = parsedate_to_datetime(raw_date)
            return dt.astimezone().isoformat()
        except Exception:
            return EmailParser.decode_mime_words(raw_date)

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
            self._emit_json({"status": "CONNECTED"})
        except imaplib.IMAP4.error:
            self._emit_json({"error": "AUTH_FAILED"})
            raise ConnectionError("Authentication failed")
        except Exception as e:
            self._emit_json({"error": "CONNECTION_ERROR", "details": str(e)})
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

    def fetch_unread_emails(self, offset: int = 0, limit: int = 60) -> Tuple[int, List[Dict[str, Any]]]:
        """Fetches unread emails with a given offset and limit."""
        if not self.mail:
            raise RuntimeError("Not connected to IMAP server.")
            
        self.mail.select('INBOX', readonly=True)
        
        status, response = self.mail.search(None, 'UNSEEN')
        if status != 'OK':
            raise Exception("Failed to search UNSEEN emails.")
            
        status, response_primary = self.mail.search(None, 'UNSEEN', 'X-GM-RAW', 'category:primary')
        primary_nums: Set[bytes] = set(response_primary[0].split()) if status == 'OK' else set()
            
        unread_msg_nums = response[0].split()
        unread_count = len(unread_msg_nums)
        
        recent_emails: List[Dict[str, Any]] = []
        
        if unread_count > 0:
            latest_nums = unread_msg_nums[::-1]
            start_idx = offset
            end_idx = start_idx + limit
            latest_nums = latest_nums[start_idx:end_idx]
            
            for num in latest_nums:
                typ, msg_data = self.mail.fetch(num, '(X-GM-THRID BODY.PEEK[])')
                if typ != 'OK':
                    continue
                    
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        header_line = response_part[0].decode('utf-8', errors='ignore')
                        
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
                        
                        recent_emails.append({
                            "from": sender,
                            "subject": subject,
                            "date": date,
                            "body": body,
                            "url": url,
                            "category": category
                        })
                        
        return unread_count, recent_emails

    @staticmethod
    def _emit_json(payload: Dict[str, Any]) -> None:
        print(json.dumps(payload), flush=True)

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
    args = parser.parse_args()

    client = GmailClient(user, password)
    
    try:
        client.connect()
        unread_count, emails = client.fetch_unread_emails(offset=args.offset, limit=args.limit)
        
        emit_json({
            "unread_count": unread_count,
            "emails": emails,
            "user_email": user,
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
