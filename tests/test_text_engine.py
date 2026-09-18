#!/usr/bin/env python3
"""
Unit tests for Omail daemon text_engine.
Verifies strict non-resource Markdown subset extraction and security mitigations.
"""

import sys
import os
import unittest
from email.message import EmailMessage

# Add daemon directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'daemon')))

from text_engine import HTMLTextExtractor, EmailParser


class TestTextEngineFormatting(unittest.TestCase):
    """Tests that Markdown formatting is preserved for allowed safe elements."""

    def test_basic_formatting(self):
        html = "<p>Hello <b>bold</b> and <i>italic</i> and <code>inline_code</code></p>"
        result = EmailParser.strip_html(html)
        self.assertIn("**bold**", result)
        self.assertIn("*italic*", result)
        self.assertIn("`inline_code`", result)

    def test_strong_and_em(self):
        html = "<p><strong>Strong</strong> and <em>Emphasis</em></p>"
        result = EmailParser.strip_html(html)
        self.assertIn("**Strong**", result)
        self.assertIn("*Emphasis*", result)

    def test_lists_and_paragraphs(self):
        html = "<p>Intro:</p><ul><li>First item</li><li>Second item</li></ul>"
        result = EmailParser.strip_html(html)
        self.assertIn("• First item", result)
        self.assertIn("• Second item", result)


class TestTextEngineLinks(unittest.TestCase):
    """Tests that hyperlinks with safe schemes are emitted and dangerous schemes are neutralized."""

    def test_safe_https_link(self):
        html = '<p>Check <a href="https://example.com/login">this link</a></p>'
        result = EmailParser.strip_html(html)
        self.assertIn("[this link](https://example.com/login)", result)

    def test_safe_http_link(self):
        html = '<p>Check <a href="http://insecure.example.com">HTTP site</a></p>'
        result = EmailParser.strip_html(html)
        self.assertIn("[HTTP site](http://insecure.example.com)", result)

    def test_safe_mailto_link(self):
        html = '<p>Contact <a href="mailto:support@example.com">Support</a></p>'
        result = EmailParser.strip_html(html)
        self.assertIn("[Support](mailto:support@example.com)", result)

    def test_unsafe_javascript_link(self):
        html = '<p><a href="javascript:alert(1)">Click Me</a></p>'
        result = EmailParser.strip_html(html)
        self.assertNotIn("javascript:", result)
        self.assertNotIn("[Click Me](", result)
        self.assertIn("Click Me", result)

    def test_unsafe_file_link(self):
        html = '<p><a href="file:///etc/passwd">Secret File</a></p>'
        result = EmailParser.strip_html(html)
        self.assertNotIn("file:", result)
        self.assertNotIn("[Secret File](", result)
        self.assertIn("Secret File", result)

    def test_unsafe_data_link(self):
        html = '<p><a href="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">Data</a></p>'
        result = EmailParser.strip_html(html)
        self.assertNotIn("data:", result)
        self.assertNotIn("[Data](", result)
        self.assertIn("Data", result)

    def test_relative_link_rejected(self):
        html = '<p><a href="/relative/path">Relative</a></p>'
        result = EmailParser.strip_html(html)
        self.assertNotIn("[Relative](", result)
        self.assertIn("Relative", result)

    def test_parentheses_and_brackets_in_link_sanitized(self):
        html = '<p><a href="https://en.wikipedia.org/wiki/Rust_(programming_language)">[Rust]</a></p>'
        result = EmailParser.strip_html(html)
        # Should escape brackets in text and URL parens to preserve Markdown link syntax
        self.assertIn(r"\[Rust\]", result)
        self.assertIn("%28programming_language%29", result)


class TestTextEngineResourceSuppression(unittest.TestCase):
    """Tests that images and rich media are never emitted as external resources."""

    def test_img_tag_completely_stripped(self):
        html = '<p>Here is an image: <img src="https://evil.com/tracker.png" alt="Company Logo"></p>'
        result = EmailParser.strip_html(html)
        # Should not contain any <img> tag
        self.assertNotIn("<img", result)
        # Should not contain markdown image syntax ![
        self.assertNotIn("![", result)
        # Should completely strip the image and alt text
        self.assertEqual(result, "Here is an image:")

    def test_img_tag_without_alt_stripped(self):
        html = '<p>Pixel tracker: <img src="https://evil.com/pixel.gif"></p>'
        result = EmailParser.strip_html(html)
        self.assertNotIn("<img", result)
        self.assertNotIn("![", result)
        self.assertNotIn("https://evil.com/pixel.gif", result)

    def test_markdown_image_syntax_in_text_neutralized(self):
        import re
        html = '<p>Look at this: ![Malicious Image](https://evil.com/exploit.png)</p>'
        result = EmailParser.strip_html(html)
        # Markdown image ![ MUST be neutralized to \![ so Qt does not fetch it
        self.assertIn(r"\![Malicious Image]", result)
        self.assertIsNone(re.search(r'(?<!\\)!\[', result))

    def test_ignored_tags_completely_stripped(self):
        html = (
            '<style>body { color: red; }</style>'
            '<script>alert("xss")</script>'
            '<svg><circle cx="50" cy="50" r="40"/></svg>'
            '<video src="movie.mp4"></video>'
            '<iframe src="https://evil.com"></iframe>'
            '<p>Clean content</p>'
        )
        result = EmailParser.strip_html(html)
        self.assertNotIn("alert", result)
        self.assertNotIn("color: red", result)
        self.assertNotIn("circle", result)
        self.assertNotIn("movie.mp4", result)
        self.assertNotIn("evil.com", result)
        self.assertEqual(result, "Clean content")

    def test_raw_html_tag_injection_escaped(self):
        # Text containing < should be escaped to prevent Qt Markdown from parsing HTML tags
        html = '<p>Calculation: 5 &lt; 10 &gt; 2 and &lt;img src="x"&gt;</p>'
        result = EmailParser.strip_html(html)
        self.assertNotIn("<img", result)


class TestPlainTextEmails(unittest.TestCase):
    """Tests plain text email extraction and character neutralization."""

    def test_plain_text_with_markdown_characters(self):
        msg = EmailMessage()
        msg.set_content("This is plain text with *asterisks*, `backticks`, and ![not an image](http://foo.com)")
        result = EmailParser.get_plain_text(msg)
        # Must escape markdown special characters
        self.assertIn(r"\*asterisks\*", result)
        self.assertIn(r"\`backticks\`", result)
        self.assertIn(r"\!\[not an image\]", result)
        # Crucially: no unescaped ![ that Qt could interpret as an image
        self.assertNotIn("![", result)


class TestEmailParserDate(unittest.TestCase):
    """Tests date parsing to ISO format."""

    def test_valid_date(self):
        date_str = "Wed, 26 Aug 2026 21:13:02 -0500"
        parsed = EmailParser.parse_date(date_str)
        self.assertTrue(parsed.startswith("2026-08-26"))

    def test_invalid_date_fallback(self):
        parsed = EmailParser.parse_date("not-a-real-date")
        self.assertEqual(parsed, "1970-01-01T00:00:00+00:00")


if __name__ == '__main__':
    unittest.main()
