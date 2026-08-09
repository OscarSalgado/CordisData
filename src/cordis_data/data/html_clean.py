"""HTML cleaning and plaintext extraction utilities."""

import html
import re
from typing import Optional


def clean_html_to_text(html_content: Optional[str]) -> str:
    """Convert HTML content to plaintext with entities unescaped.

    Args:
        html_content: HTML string or None

    Returns:
        Plaintext with tags stripped, entities unescaped, whitespace normalized
    """
    if not html_content:
        return ""

    # Remove common HTML tags first (while they're still tags)
    text = re.sub(r"<[^>]+>", "", html_content)

    # Unescape HTML entities (e.g., &amp; → &, &lt; → <)
    text = html.unescape(text)

    # Normalize whitespace: collapse multiple spaces/newlines
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text
