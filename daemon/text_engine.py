#!/usr/bin/env python3
"""
HTML-to-Markdown text cleaning engine for Omail.
Converts HTML email content into clean, QML-compatible Markdown,
restricted to a strict non-resource subset (no images, safe schemes only).
"""

import re
from html import escape as html_escape
from html.parser import HTMLParser
from typing import List, Optional, Tuple
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime


# --- Pre-compiled regex patterns ---
_RE_DATA_SPACES = re.compile(r' +')
_RE_BOLD_FIX = re.compile(r'\*\*(.*?)\*\*', re.DOTALL)
_RE_WHITESPACE_NEWLINE = re.compile(r'[ \t]*\n[ \t]*')
_RE_LEADING_WHITESPACE = re.compile(r'^[ \t]+', re.MULTILINE)
_RE_MULTI_SPACE = re.compile(r' {2,}')
_RE_MULTI_NEWLINE = re.compile(r'\n{3,}')
_RE_IMAGE_MARKDOWN = re.compile(r'!\[')

# Translation table for invisible/formatting characters
_TRANSLATE_TABLE: dict[int, str | None] = {0x00A0: ' '}
for _cp in (
    0x00AD,   # Soft hyphen
    0x034F,   # Combining grapheme joiner
    0xFEFF,   # BOM / ZWNBSP
):
    _TRANSLATE_TABLE[_cp] = None
for _start, _end in ((0x200B, 0x2010), (0x2028, 0x2030), (0x2060, 0x2070)):
    for _cp in range(_start, _end):
        _TRANSLATE_TABLE[_cp] = None

# Allowed URL schemes for hyperlinks in QML
_ALLOWED_SCHEMES = ('https://', 'http://', 'mailto:')


class HTMLTextExtractor(HTMLParser):
    """Parses HTML content and extracts clean, safe Markdown for QML rendering."""

    _BLOCK_TAGS = frozenset((
        'br', 'p', 'div', 'tr',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'td', 'th',
    ))
    _IGNORE_TAGS = frozenset((
        'script', 'style', 'head', 'title',
        'svg', 'canvas', 'video', 'audio', 'iframe', 'object', 'picture'
    ))
    _BOLD_TAGS = frozenset(('b', 'strong'))
    _ITALIC_TAGS = frozenset(('i', 'em'))
    _CODE_TAGS = frozenset(('code', 'tt'))

    def __init__(self) -> None:
        super().__init__()
        self.result: List[str] = []
        self._ignore_depth: int = 0
        self.current_link: Optional[str] = None
        self.link_start_index: int = -1
        self._bold_depth: int = 0
        self._italic_depth: int = 0
        self._code_depth: int = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in self._IGNORE_TAGS:
            self._ignore_depth += 1
            return
        if self._ignore_depth > 0:
            return

        if tag in self._BLOCK_TAGS:
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
        elif tag in self._CODE_TAGS:
            if self._code_depth == 0:
                self.result.append('`')
            self._code_depth += 1
        elif tag in ('ul', 'ol'):
            self.result.append(' ' if self.current_link else '\n\n')
        elif tag == 'a':
            if not self.current_link:
                href = next((v.strip() for k, v in attrs if k == 'href' and v), None)
                if href:
                    cleaned_href = href.replace(' ', '%20').replace('\n', '').replace('\r', '')
                    lower_href = cleaned_href.lower()
                    if any(lower_href.startswith(scheme) for scheme in _ALLOWED_SCHEMES):
                        self.current_link = cleaned_href
                        self.link_start_index = len(self.result)

    def handle_endtag(self, tag: str) -> None:
        if tag in self._IGNORE_TAGS:
            if self._ignore_depth > 0:
                self._ignore_depth -= 1
            return
        if self._ignore_depth > 0:
            return

        if tag in self._BOLD_TAGS:
            if self._bold_depth > 0:
                self._bold_depth -= 1
                if self._bold_depth == 0:
                    self.result.append('**')
        elif tag in self._ITALIC_TAGS:
            if self._italic_depth > 0:
                self._italic_depth -= 1
                if self._italic_depth == 0:
                    self.result.append('*')
        elif tag in self._CODE_TAGS:
            if self._code_depth > 0:
                self._code_depth -= 1
                if self._code_depth == 0:
                    self.result.append('`')
        elif tag in ('ul', 'ol'):
            self.result.append(' ' if self.current_link else '\n\n')
        elif tag in self._BLOCK_TAGS or tag == 'li':
            self.result.append(' ' if self.current_link else '\n\n')
        elif tag == 'a':
            if self.current_link:
                link_text = "".join(self.result[self.link_start_index:]).strip()
                self.result = self.result[:self.link_start_index]
                if link_text:
                    safe_text = link_text.replace('[', '\\[').replace(']', '\\]')
                    safe_url = self.current_link.replace('(', '%28').replace(')', '%29')
                    self.result.append(f'[{safe_text}]({safe_url})')
                self.current_link = None

    def handle_data(self, data: str) -> None:
        if self._ignore_depth == 0:
            text = data.replace('\n', ' ').replace('\r', '').replace('<', '&lt;')
            text = _RE_DATA_SPACES.sub(' ', text)
            if text.strip() or (text and self.result and not self.result[-1].endswith('\n')):
                self.result.append(text)

    def get_text(self) -> str:
        if self._bold_depth > 0:
            self.result.append('**')
            self._bold_depth = 0
        if self._italic_depth > 0:
            self.result.append('*')
            self._italic_depth = 0
        if self._code_depth > 0:
            self.result.append('`')
            self._code_depth = 0

        content = "".join(self.result)
        content = content.translate(_TRANSLATE_TABLE)
        # Neutralize any markdown image syntax ![alt](url) -> \![alt](url)
        content = _RE_IMAGE_MARKDOWN.sub(r'\![', content)
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
        """Converts HTML to clean, safe Markdown text."""
        if not html_content:
            return ""
        try:
            extractor = HTMLTextExtractor()
            extractor.feed(html_content)
            return extractor.get_text()
        except Exception:
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
            for char in ('*', '_', '`', '#', '[', ']', '<', '>', '!'):
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
            return "1970-01-01T00:00:00+00:00"
