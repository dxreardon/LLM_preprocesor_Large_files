"""
Basic tests for the alpha chunker.

Focus:
- Multiple chunks produced when max_chunk_tokens is small.
- Each original paragraph appears in at least one chunk.
- Chunk IDs are unique and sequential.
"""

from __future__ import annotations

from typing import List

from doc_prep.chunker import chunk_text
from doc_prep.token_estimator import estimate_tokens


def _make_sample_text(num_paragraphs: int = 8) -> str:
    """
    Generate a synthetic document with `num_paragraphs` paragraphs separated
    by blank lines.
    """
    paras: List[str] = []
    for i in range(1, num_paragraphs + 1):
        # Slightly different lengths so we don't get identical estimates
        sentence = " ".join([f"word{i}_{j}" for j in range(1, 20 + i)])
        paras.append(f"Paragraph {i}. {sentence}")
    return "\n\n".join(paras)


def test_chunker_basic_multiple_chunks():
    text = _make_sample_text(num_paragraphs=10)
    max_chunk_tokens = 150  # intentionally small to enforce multiple chunks
    overlap_tokens = 50

    chunks = chunk_text(
        text=text,
        max_chunk_tokens=max_chunk_tokens,
        overlap_tokens=overlap_tokens,
        token_estimator=estimate_tokens,
    )

    # Expect more than one chunk
    assert len(chunks) > 1

    # Chunk IDs should be unique and sequential
    chunk_ids = [c["chunk_id"] for c in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))

    # Expect pattern CH-0001, CH-0002, ...
    for index, chunk_id in enumerate(chunk_ids, start=1):
        assert chunk_id == f"CH-{index:04d}"

    # Each estimated token count should be reasonably bounded
    # (allowing some slack because we re-estimate on the final chunk text)
    for c in chunks:
        assert c["token_estimate"] > 0
        assert c["token_estimate"] <= max_chunk_tokens * 2

    # Ensure every original paragraph appears in at least one chunk
    original_paragraphs = text.split("\n\n")
    for para in original_paragraphs:
        para = para.strip()
        if not para:
            continue
        assert any(para in chunk["text"] for chunk in chunks)
