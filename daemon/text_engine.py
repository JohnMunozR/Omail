#!/usr/bin/env python3
"""
HTML-to-Markdown text cleaning engine for Omail.
Converts HTML email content into clean, QML-compatible Markdown.
"""

import re
from html import escape as html_escape
from html.parser import HTMLParser
from typing import List, Optional, Tuple
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime


# --- Pre-compiled regex patterns (W1) ---
_RE_DATA_SPACES = re.compile(r' +')
_RE_BOLD_FIX = re.compile(r'\*\*(.*?)\*\*', re.DOTALL)  # W2: DOTALL for multiline
_RE_WHITESPACE_NEWLINE = re.compile(r'[ \t]*\n[ \t]*')
_RE_LEADING_WHITESPACE = re.compile(r'^[ \t]+', re.MULTILINE)
_RE_MULTI_SPACE = re.compile(r' {2,}')
_RE_MULTI_NEWLINE = re.compile(r'\n{3,}')

# Translation table for invisible/formatting characters (G2: str.translate, G1: soft hyphen)
_TRANSLATE_TABLE: dict[int, str | None] = {0x00A0: ' '}
for _cp in (
    0x00AD,   # Soft hyphen (G1)
    0x034F,   # Combining grapheme joiner
    0xFEFF,   # BOM / ZWNBSP
):
    _TRANSLATE_TABLE[_cp] = None
for _start, _end in ((0x200B, 0x2010), (0x2028, 0x2030), (0x2060, 0x2070)):
    for _cp in range(_start, _end):
        _TRANSLATE_TABLE[_cp] = None


class HTMLTextExtractor(HTMLParser):
    """Parses HTML content and extracts clean Markdown for QML rendering."""

    # Class-level tag constants (DRY: W6)
    _BLOCK_TAGS = frozenset((
        'br', 'p', 'div', 'tr',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'td', 'th',
    ))
    _SCRIPT_TAGS = frozenset(('script', 'style'))
    _BOLD_TAGS = frozenset(('b', 'strong'))
    _ITALIC_TAGS = frozenset(('i', 'em'))

    def __init__(self) -> None:
        super().__init__()
        self.result: List[str] = []
        self.in_style_or_script: bool = False
        self.current_link: Optional[str] = None
        self.link_start_index: int = -1
        self._bold_depth: int = 0    # W4: depth tracking
        self._italic_depth: int = 0  # W4: depth tracking

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in self._SCRIPT_TAGS:
            self.in_style_or_script = True
        elif tag in self._BLOCK_TAGS:
            self.result.append(' ' if self.current_link else '\n\n')
        elif tag == 'li':
            self.result.append(' ' if self.current_link else '\n\n• ')
        elif tag in self._BOLD_TAGS:
            if self._bold_depth == 0:
                self.result.append('**')
            self._bold_depth += 1
        elif tag in self._ITALIC_TAGS:
            if self._italic_depth == 0:
                self.result.append('*')
            self._italic_depth += 1
        elif tag in ('ul', 'ol'):
            self.result.append(' ' if self.current_link else '\n\n')
        elif tag == 'a':
            if not self.current_link:
                href = next((v for k, v in attrs if k == 'href'), None)
                if href:
                    self.current_link = href.replace(' ', '%20').replace('\n', '')
                    self.link_start_index = len(self.result)

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SCRIPT_TAGS:
            self.in_style_or_script = False
        elif tag in self._BOLD_TAGS:
            if self._bold_depth > 0:
                self._bold_depth -= 1
                if self._bold_depth == 0:
                    self.result.append('**')
        elif tag in self._ITALIC_TAGS:
            if self._italic_depth > 0:
                self._italic_depth -= 1
                if self._italic_depth == 0:
                    self.result.append('*')
        elif tag in ('ul', 'ol'):
            self.result.append(' ' if self.current_link else '\n\n')
        elif tag in self._BLOCK_TAGS or tag == 'li':
            self.result.append(' ' if self.current_link else '\n\n')
        elif tag == 'a':
            if self.current_link:
                # W3: Strip link text here instead of post-processing with
                # broad bracket regexes that could match non-link brackets
                link_text = "".join(self.result[self.link_start_index:]).strip()
                self.result = self.result[:self.link_start_index]
                if link_text:
                    self.result.append(f'[{link_text}]({self.current_link})')
                self.current_link = None

    def handle_data(self, data: str) -> None:
        if not self.in_style_or_script:
            text = data.replace('\n', ' ').replace('\r', '')
            text = _RE_DATA_SPACES.sub(' ', text)
            if text.strip() or (text and self.result and not self.result[-1].endswith('\n')):
                self.result.append(text)

    def get_text(self) -> str:
        # W4: Auto-close unclosed formatting tags
        if self._bold_depth > 0:
            self.result.append('**')
            self._bold_depth = 0
        if self._italic_depth > 0:
            self.result.append('*')
            self._italic_depth = 0

        content = "".join(self.result)
        content = content.translate(_TRANSLATE_TABLE)
        content = _RE_BOLD_FIX.sub(lambda m: f" **{m.group(1).strip()}** ", content)
        content = _RE_WHITESPACE_NEWLINE.sub('\n', content)
        content = _RE_LEADING_WHITESPACE.sub('', content)
        content = _RE_MULTI_SPACE.sub(' ', content)
        content = _RE_MULTI_NEWLINE.sub('\n\n', content)
        return content.strip()


class EmailParser:
    """Handles parsing and decoding of email messages."""

    @staticmethod
    def strip_html(html_content: str) -> str:
        """Converts HTML to clean Markdown text."""
        if not html_content:
            return ""
        try:
            extractor = HTMLTextExtractor()
            extractor.feed(html_content)
            return extractor.get_text()
        except Exception:
            # S2: Escape raw HTML to prevent QML layout breakage
            return html_escape(str(html_content), quote=False)

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

        # W7: Unified iteration — msg.walk() handles both multipart and single
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" in content_disposition:
                continue
            decoded = EmailParser._decode_part(part)
            if decoded is None:
                continue
            content_type = part.get_content_type()
            if content_type == "text/plain":
                body_plain += decoded + "\n"
            elif content_type == "text/html":
                body_html += decoded + "\n"

        if body_html.strip():
            return EmailParser.strip_html(body_html).strip()

        if body_plain.strip():
            plain = body_plain.strip()
            for char in ('*', '_', '`', '#', '[', ']', '<', '>'):
                plain = plain.replace(char, f'\\{char}')
            return plain

        return ""

    @staticmethod
    def _decode_part(part: Message) -> Optional[str]:
        """Decodes a single email MIME part. Returns None on failure."""
        try:
            payload = part.get_payload(decode=True)
            if not payload:
                return None
            charset = part.get_content_charset() or 'utf-8'
            return payload.decode(charset, errors='replace')
        except Exception:
            return None

    @staticmethod
    def parse_date(raw_date: str) -> str:
        """Parses an email date into strict ISO 8601 format for QML."""
        try:
            dt = parsedate_to_datetime(raw_date)
            return dt.astimezone().isoformat()
        except Exception:
            # S3: Return safe ISO fallback instead of raw date string
            return "1970-01-01T00:00:00+00:00"
