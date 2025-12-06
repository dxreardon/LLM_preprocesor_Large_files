"""
doc_prep

Alpha version of a local tool that converts large documents (PDF/DOCX/TXT)
into "LLM-ready" chunked artifacts.

Public API (for now):
- run_pipeline: process a single document and write artifacts to disk.
"""

from __future__ import annotations

from pathlib import Path

from .pipeline import run_pipeline as _run_pipeline


def run_pipeline(
    input_path: str | Path,
    output_root: str | Path,
    tier_override: str | None = None,
    max_chunk_tokens: int | None = None,
) -> Path:
    """
    Thin wrapper around pipeline.run_pipeline so external code can do:

        from doc_prep import run_pipeline

    Parameters
    ----------
    input_path:
        Path to the input document (.pdf, .docx, or .txt).
    output_root:
        Directory under which a per-run output folder will be created.
    tier_override:
        Optional string label for the tier (e.g. "T0", "T1"...). Only affects
        the 'name' stored in metadata; chunk sizing still comes from token
        count unless you also override max_chunk_tokens.
    max_chunk_tokens:
        Optional override for the maximum tokens per chunk.

    Returns
    -------
    Path
        The directory where artifacts were written.
    """
    return _run_pipeline(
        input_path=input_path,
        output_root=output_root,
        tier_override=tier_override,
        max_chunk_tokens=max_chunk_tokens,
    )
