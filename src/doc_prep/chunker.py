"""
chunker.py

Turn cleaned document text into a sequence of "LLM-ready" chunks.

Alpha design:
- Split text into paragraphs using blank lines as boundaries.
- Build chunks by aggregating paragraphs until the estimated token
  count would exceed `max_chunk_tokens`.
- Optionally overlap consecutive chunks by reusing the last paragraph.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List


def _split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs.

    We treat one or more blank lines as a paragraph boundary.

    Parameters
    ----------
    text:
        Cleaned, normalized document text.

    Returns
    -------
    List[str]
        List of non-empty paragraph strings.
    """
    # Simple split on blank lines; keep only non-empty paragraphs
    raw_paras = text.split("\n\n")
    paragraphs = [p.strip() for p in raw_paras if p.strip()]
    return paragraphs


def chunk_text(
    text: str,
    max_chunk_tokens: int,
    overlap_tokens: int,
    token_estimator: Callable[[str], int],
) -> List[Dict[str, Any]]:
    """
    Split text into chunks suitable for feeding to an LLM.

    Strategy (alpha version):
    - Break the document into paragraphs.
    - Accumulate paragraphs into a chunk until adding another would exceed
      `max_chunk_tokens` (based on estimated tokens).
    - If a single paragraph is larger than `max_chunk_tokens`, it becomes a
      chunk by itself.
    - If `overlap_tokens > 0` and a chunk contains more than one paragraph,
      we overlap by reusing the last paragraph in the next chunk.
      (This is a simple approximation; the token count is not exact.)

    Parameters
    ----------
    text:
        Cleaned document text.
    max_chunk_tokens:
        Target maximum tokens per chunk.
    overlap_tokens:
        Desired overlap in tokens (approximate). In the alpha version,
        we treat any positive value as "overlap by one paragraph".
    token_estimator:
        Callable that estimates token count for a given string.

    Returns
    -------
    List[Dict[str, Any]]
        List of chunk dictionaries:
            {
                "chunk_id": "CH-0001",
                "start_char": int,
                "end_char": int,
                "text": str,
                "token_estimate": int
            }
    """
    if not text.strip():
        return []

    paragraphs = _split_into_paragraphs(text)
    if not paragraphs:
        return []

    # Pre-compute estimated tokens per paragraph
    para_tokens: List[int] = [token_estimator(p) for p in paragraphs]

    # Approximate character offsets for each paragraph.
    # We reconstruct text using "\n\n".join(paragraphs), so we compute offsets
    # under that assumption.
    char_offsets: List[int] = []
    running = 0
    for idx, para in enumerate(paragraphs):
        char_offsets.append(running)
        # length of this paragraph + two newlines (except we don't care about
        # the trailing newlines for the last paragraph; this is approximate).
        running += len(para)
        if idx < len(paragraphs) - 1:
            running += 2  # for "\n\n"

    chunks: List[Dict[str, Any]] = []
    i = 0
    chunk_index = 1

    # Overlap behavior: any positive overlap_tokens → overlap by one paragraph
    overlap_paragraphs = 1 if overlap_tokens > 0 else 0

    while i < len(paragraphs):
        current_paras: List[str] = []
        current_tokens = 0

        start_para_idx = i

        # Start char offset for this chunk (approximate)
        start_char = char_offsets[start_para_idx]

        j = i
        while j < len(paragraphs):
            para = paragraphs[j]
            t = para_tokens[j]

            if current_paras and current_tokens + t > max_chunk_tokens:
                # Stop before we exceed the max for this chunk
                break

            current_paras.append(para)
            current_tokens += t
            j += 1

            # If the first paragraph alone is bigger than max_chunk_tokens,
            # we still accept it as a chunk by itself.
            if not current_paras or j == len(paragraphs):
                continue

        if not current_paras:
            # Safety net: should not happen, but avoid infinite loops.
            current_paras.append(paragraphs[j])
            current_tokens += para_tokens[j]
            j += 1

        chunk_text_str = "\n\n".join(current_paras).strip()
        token_estimate = token_estimator(chunk_text_str)

        end_char = start_char + len(chunk_text_str)

        chunk_id = f"CH-{chunk_index:04d}"
        chunks.append(
            {
                "chunk_id": chunk_id,
                "start_char": start_char,
                "end_char": end_char,
                "text": chunk_text_str,
                "token_estimate": token_estimate,
            }
        )
        chunk_index += 1

        if j >= len(paragraphs):
            break

        # Move i forward for the next chunk, with optional overlap
        consumed_paras = j - i
        if overlap_paragraphs > 0 and consumed_paras > overlap_paragraphs:
            # Reuse the last `overlap_paragraphs` paragraphs in next chunk
            i = i + consumed_paras - overlap_paragraphs
        else:
            i = i + consumed_paras

    return chunks
