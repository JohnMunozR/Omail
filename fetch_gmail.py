#!/usr/bin/env python3
import os
import json
import imaplib
import email
from email.header import decode_header
from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.in_style_or_script = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.in_style_or_script = True
        elif tag in ('br', 'p', 'div', 'tr', 'li'):
            self.result.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.in_style_or_script = False

    def handle_data(self, data):
        if not self.in_style_or_script:
            text = data.strip()
            if text:
                self.result.append(text + " ")

    def get_text(self):
        return "".join(self.result).strip()

def strip_html(html_content):
    try:
        extractor = HTMLTextExtractor()
        extractor.feed(html_content)
        return extractor.get_text()
    except Exception:
        return html_content

def decode_mime_words(s):
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

def get_plain_text(msg):
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
                if not payload: continue
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

    # Prefer plain text if available and not empty, otherwise strip HTML
    final_body = body_plain.strip()
    if not final_body and body_html.strip():
        final_body = strip_html(body_html)
        
    if len(final_body) > 2000:
        final_body = final_body[:2000] + "..."
    return final_body.strip()

def main():
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
            
    if not user or not password:
        print(json.dumps({
            "error": "NOT_LOGGED_IN"
        }))
        return

    try:
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(user, password)
            print(json.dumps({"status": "CONNECTED"}), flush=True)
        except imaplib.IMAP4.error:
            print(json.dumps({"error": "AUTH_FAILED"}))
            return
        except Exception as e:
            print(json.dumps({"error": "CONNECTION_ERROR", "details": str(e)}))
            return
        mail.select('INBOX', readonly=True)
        
        status, response = mail.search(None, 'UNSEEN')
        if status != 'OK':
            raise Exception("Failed to search UNSEEN emails.")
            
        status, response_primary = mail.search(None, 'UNSEEN', 'X-GM-RAW', 'category:primary')
        primary_nums = set(response_primary[0].split()) if status == 'OK' else set()
            
        unread_msg_nums = response[0].split()
        unread_count = len(unread_msg_nums)
        
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--offset', type=int, default=0)
        parser.add_argument('--limit', type=int, default=60)
        args = parser.parse_args()
        
        recent_emails = []
        
        if unread_count > 0:
            latest_nums = unread_msg_nums[::-1]
            start_idx = args.offset
            end_idx = start_idx + args.limit
            latest_nums = latest_nums[start_idx:end_idx]
            
            import re
            
            for num in latest_nums:
                typ, msg_data = mail.fetch(num, '(X-GM-THRID BODY.PEEK[])')
                if typ != 'OK':
                    continue
                    
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        header_line = response_part[0].decode('utf-8', errors='ignore')
                        
                        # Extract X-GM-THRID
                        thrid_match = re.search(r'X-GM-THRID (\d+)', header_line)
                        url = "https://mail.google.com/mail/u/0/#inbox"
                        if thrid_match:
                            thrid_decimal = int(thrid_match.group(1))
                            thrid_hex = hex(thrid_decimal)[2:]
                            url = f"https://mail.google.com/mail/u/0/#inbox/{thrid_hex}"
                            
                        # Si está en el set de Primary, es Inbox. Si no, es Other.
                        category = "Inbox" if num in primary_nums else "Other"
                            
                        msg = email.message_from_bytes(response_part[1])
                        subject = decode_mime_words(msg.get('Subject', ''))
                        sender = decode_mime_words(msg.get('From', ''))
                        from email.utils import parsedate_to_datetime
                        raw_date = msg.get('Date', '')
                        try:
                            dt = parsedate_to_datetime(raw_date)
                            date = dt.astimezone().isoformat()
                        except Exception:
                            date = decode_mime_words(raw_date)
                        body = get_plain_text(msg)
                        
                        recent_emails.append({
                            "from": sender,
                            "subject": subject,
                            "date": date,
                            "body": body,
                            "url": url,
                            "category": category
                        })
                        
        mail.close()
        mail.logout()

        
        print(json.dumps({
            "unread_count": unread_count,
            "emails": recent_emails,
            "user_email": user,
            "error": None
        }))
        
    except Exception as e:
        print(json.dumps({
            "unread_count": 0,
            "emails": [],
            "error": str(e)
        }))

if __name__ == '__main__':
    main()
