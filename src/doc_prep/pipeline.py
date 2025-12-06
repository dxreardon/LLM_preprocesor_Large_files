"""
Pipeline orchestration for the doc_prep alpha tool.

This ties together:
    - document loading
    - text cleaning
    - token estimation
    - tier selection
    - chunking
    - artifact writing
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .loaders import load_document
from .text_cleaner import clean_text
from .token_estimator import estimate_tokens
from .tiering import TierParams, infer_tier
from .chunker import chunk_text
from .writers import write_artifacts


def run_pipeline(
    input_path: str | Path,
    output_root: str | Path,
    tier_override: str | None = None,
    max_chunk_tokens: int | None = None,
) -> Path:
    """
    Run the full alpha pipeline on a single document.

    Steps:
        1. Load raw text + loader metadata.
        2. Clean the text.
        3. Estimate token count.
        4. Infer tier (and optionally override name / chunk size).
        5. Chunk the text.
        6. Write artifacts to disk.

    Parameters
    ----------
    input_path:
        Path to the input .pdf, .docx, or .txt file.
    output_root:
        Directory under which a per-run output folder will be created.
    tier_override:
        Optional tier name override. Only affects the label stored in metadata,
        not the default chunk sizing.
    max_chunk_tokens:
        Optional override for maximum tokens per chunk.

    Returns
    -------
    Path
        Path to the directory where artifacts were written.
    """
    input_path = Path(input_path)
    output_root = Path(output_root)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # 1) Load
    raw_text, loader_metadata = load_document(input_path)

    # 2) Clean
    cleaned_text = clean_text(raw_text)

    # 3) Token estimate
    token_count = estimate_tokens(cleaned_text)

    # 4) Tier selection
    params = infer_tier(token_count)  # type: ignore[call-arg]

    # Override tier name if requested
    if tier_override is not None:
        params = TierParams(
            name=tier_override,
            max_chunk_tokens=params.max_chunk_tokens,
            overlap_tokens=params.overlap_tokens,
        )

    # Override chunk size if requested
    if max_chunk_tokens is not None:
        params = TierParams(
            name=params.name,
            max_chunk_tokens=max_chunk_tokens,
            overlap_tokens=params.overlap_tokens,
        )

    # 5) Chunking
    chunks: List[Dict[str, Any]] = chunk_text(
        text=cleaned_text,
        max_chunk_tokens=params.max_chunk_tokens,
        overlap_tokens=params.overlap_tokens,
        token_estimator=estimate_tokens,
    )

    # 6) Write artifacts
    extra_metadata: Dict[str, Any] = dict(loader_metadata)
    extra_metadata.update(
        {
            "token_count": token_count,
            "tier": params.name,
            "max_chunk_tokens": params.max_chunk_tokens,
            "overlap_tokens": params.overlap_tokens,
        }
    )

    output_dir = write_artifacts(
        input_path=input_path,
        output_root=output_root,
        cleaned_text=cleaned_text,
        token_count=token_count,
        tier_params=params,
        chunks=chunks,
        extra_metadata=extra_metadata,
    )

    return output_dir
