"""
text_cleaner.py

Simple text normalization utilities for the alpha version.

Goals:
- Normalize newline conventions.
- Remove obvious junk (page-number-only lines).
- Collapse excessive blank lines.
"""

from __future__ import annotations

import re


def clean_text(raw_text: str) -> str:
    """
    Clean and normalize raw document text.

    Steps (alpha version):
    1. Normalize newlines to '\n'.
    2. Replace tabs with spaces.
    3. Strip trailing whitespace on each line.
    4. Remove lines that look like bare page numbers (digits only, short).
    5. Collapse runs of >=3 newlines into exactly 2.
    6. Strip leading/trailing whitespace from the whole string.

    Parameters
    ----------
    raw_text:
        Text as extracted from PDF/DOCX/TXT loader.

    Returns
    -------
    str
        Cleaned text suitable for downstream token estimation and chunking.
    """
    if not raw_text:
        return ""

    # 1) Normalize newlines
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    # 2) Tabs to spaces
    text = text.replace("\t", " ")

    # 3) Strip trailing whitespace per line
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)

    # 4) Remove lines that look like bare page numbers
    filtered_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        # Numeric-only line, short (likely a page number), drop it
        if stripped.isdigit() and len(stripped) <= 3:
            continue
        filtered_lines.append(line)
    text = "\n".join(filtered_lines)

    # 5) Collapse excessive blank lines (3+ → 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 6) Strip outer whitespace
    text = text.strip()

    return text
