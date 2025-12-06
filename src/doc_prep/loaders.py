"""
Document loaders for the doc_prep alpha tool.

For now, everything lives in a single module:

    - PDF loader using pypdf
    - DOCX loader using python-docx
    - Plain-text loader

All loaders return `(text, metadata_dict)`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple


class UnsupportedFileTypeError(RuntimeError):
    """Raised when the input file type is not supported."""


def load_document(input_path: str | Path) -> Tuple[str, Dict]:
    """
    Load a document from disk and return (raw_text, metadata).

    Parameters
    ----------
    input_path:
        Path to the input file.

    Returns
    -------
    (str, dict)
        - raw_text: the extracted text
        - metadata: a minimal dictionary with keys like:
            - file_name
            - file_type ('pdf', 'docx', 'txt')
            - page_count (where available)
            - full_path (string)
    """
    path = Path(input_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        text, meta = _load_pdf(path)
    elif suffix == ".docx":
        text, meta = _load_docx(path)
    elif suffix == ".txt":
        text, meta = _load_txt(path)
    else:
        raise UnsupportedFileTypeError(
            f"Unsupported file type: {suffix!r}. "
            "Alpha version supports only .pdf, .docx, and .txt."
        )

    # Common metadata fields
    meta.setdefault("file_name", path.name)
    meta.setdefault("file_type", suffix.lstrip("."))
    meta.setdefault("full_path", str(path.resolve()))

    return text, meta


def _load_pdf(path: Path) -> Tuple[str, Dict]:
    """
    Extract text from a PDF using pypdf.

    Notes (alpha version):
        - We simply concatenate page texts with two newlines between pages.
        - More advanced header/footer stripping is handled later by text_cleaner.
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - import error only at runtime
        raise RuntimeError(
            "pypdf is required to load PDF files. Install it with:\n"
            "    pip install pypdf"
        ) from exc

    reader = PdfReader(str(path))
    pages_text = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages_text.append(page_text)

    combined_text = "\n\n".join(pages_text)

    metadata: Dict = {
        "file_name": path.name,
        "file_type": "pdf",
        "page_count": len(reader.pages),
    }
    return combined_text, metadata


def _load_docx(path: Path) -> Tuple[str, Dict]:
    """
    Extract text from a DOCX using python-docx.

    Notes (alpha version):
        - Joins all paragraphs with newlines.
        - We ignore explicit style/heading info for now; that can be added later.
    """
    try:
        import docx  # python-docx
    except ImportError as exc:  # pragma: no cover - import error only at runtime
        raise RuntimeError(
            "python-docx is required to load DOCX files. Install it with:\n"
            "    pip install python-docx"
        ) from exc

    doc = docx.Document(str(path))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

    combined_text = "\n".join(paragraphs)

    metadata: Dict = {
        "file_name": path.name,
        "file_type": "docx",
        "page_count": None,  # DOCX doesn't have a fixed 'page count'
    }
    return combined_text, metadata


def _load_txt(path: Path) -> Tuple[str, Dict]:
    """
    Load plain text from a .txt file.

    Notes:
        - Assumes UTF-8 encoding by default.
        - If you need other encodings, you can extend this later.
    """
    text = path.read_text(encoding="utf-8")

    metadata: Dict = {
        "file_name": path.name,
        "file_type": "txt",
        "page_count": None,
    }
    return text, metadata
