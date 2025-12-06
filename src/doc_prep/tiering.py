"""
tiering.py

Map whole-document token counts to simple tier parameters.

Tiers (alpha version):

    T0: <=  2k tokens  → max_chunk_tokens=1500, overlap_tokens=0
    T1: 2k–10k tokens  → max_chunk_tokens=2000, overlap_tokens=100
    T2: 10k–50k tokens → max_chunk_tokens=1500, overlap_tokens=150
    T3: > 50k tokens   → max_chunk_tokens=1000, overlap_tokens=200

These are deliberately simple and can be tuned later.
"""

from __future__ import annotations

from typing import NamedTuple


class TierParams(NamedTuple):
    """
    Parameters controlling chunking behavior for a given tier.

    Attributes
    ----------
    name:
        Human-friendly tier label (e.g. "T0", "T1"...).
    max_chunk_tokens:
        Target maximum token count per chunk.
    overlap_tokens:
        Desired overlap between consecutive chunks, in tokens (approximate).
        The alpha chunker uses this as a rough signal and implements a simple
        paragraph-level overlap; it's not exact.
    """

    name: str
    max_chunk_tokens: int
    overlap_tokens: int


def infer_tier(token_count: int) -> TierParams:
    """
    Infer tier parameters from a document-level token count.

    Parameters
    ----------
    token_count:
        Estimated total tokens in the cleaned document.

    Returns
    -------
    TierParams
        Tier parameters controlling downstream chunking.
    """
    if token_count <= 2000:
        # Very small document; usually fits in a single chunk.
        return TierParams(name="T0", max_chunk_tokens=1500, overlap_tokens=0)

    if token_count <= 10_000:
        # Small/medium document.
        return TierParams(name="T1", max_chunk_tokens=2000, overlap_tokens=100)

    if token_count <= 50_000:
        # Large spec / report.
        return TierParams(name="T2", max_chunk_tokens=1500, overlap_tokens=150)

    # Very large document; keep chunks smaller to maintain quality.
    return TierParams(name="T3", max_chunk_tokens=1000, overlap_tokens=200)
