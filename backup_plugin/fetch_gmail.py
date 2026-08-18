#!/usr/bin/env python3
import os
import json
import imaplib
import email
from email.header import decode_header

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

def main():
    user = os.environ.get('OMAIL_USER')
    password = os.environ.get('OMAIL_PASS')
    
    if not user or not password:
        print(json.dumps({
            "unread_count": 0,
            "emails": [],
            "error": "Missing OMAIL_USER or OMAIL_PASS environment variables."
        }))
        return

    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(user, password)
        mail.select('INBOX', readonly=True)
        
        status, response = mail.search(None, 'UNSEEN')
        if status != 'OK':
            raise Exception("Failed to search UNSEEN emails.")
            
        unread_msg_nums = response[0].split()
        unread_count = len(unread_msg_nums)
        
        recent_emails = []
        
        if unread_count > 0:
            latest_nums = unread_msg_nums[-5:]
            latest_nums.reverse()
            
            for num in latest_nums:
                typ, msg_data = mail.fetch(num, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])')
                if typ != 'OK':
                    continue
                    
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = decode_mime_words(msg.get('Subject', ''))
                        sender = decode_mime_words(msg.get('From', ''))
                        date = decode_mime_words(msg.get('Date', ''))
                        recent_emails.append({
                            "from": sender,
                            "subject": subject,
                            "date": date
                        })
                        
        mail.close()
        mail.logout()
        
        print(json.dumps({
            "unread_count": unread_count,
            "emails": recent_emails,
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
