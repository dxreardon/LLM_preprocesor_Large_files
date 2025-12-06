"""
writers.py

Turn in-memory document representation into "LLM-ready" artifacts on disk.

Alpha version writes:
    - raw_text.txt
    - metadata.json
    - chunk_index.json
    - overview.md
    - chunks/CH-*.txt
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .tiering import TierParams


@dataclass
class Metadata:
    """
    Simple metadata container for serialization to metadata.json.
    """

    file_name: str
    file_type: str
    full_path: str
    token_count: int
    num_chunks: int
    tier: str
    max_chunk_tokens: int
    overlap_tokens: int

    # Optional extra fields can go here as needed
    page_count: Optional[int] = None


def _slugify_file_name(name: str) -> str:
    """
    Turn a file name into a simple slug for directory naming.

    Example:
        'My Spec.docx' -> 'my_spec'
    """
    stem = Path(name).stem
    # Replace non-alphanumeric with underscores, lowercase
    slug_chars = []
    for ch in stem:
        if ch.isalnum():
            slug_chars.append(ch.lower())
        else:
            slug_chars.append("_")
    slug = "".join(slug_chars).strip("_")
    if not slug:
        slug = "document"
    return slug


def _make_output_dir(input_path: Path, output_root: Path) -> Path:
    """
    Build a per-run output directory under `output_root`.

    Alpha version:
        <output_root>/<slug>_artifacts/
    """
    slug = _slugify_file_name(input_path.name)
    dir_name = f"{slug}_artifacts"
    output_dir = output_root / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    # Also create chunks subdir
    (output_dir / "chunks").mkdir(exist_ok=True)
    return output_dir


def write_artifacts(
    input_path: Path,
    output_root: Path,
    cleaned_text: str,
    token_count: int,
    tier_params: TierParams,
    chunks: List[Dict[str, Any]],
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Write core alpha artifacts to disk.

    Creates a directory under `output_root`:
        - raw_text.txt          : cleaned full text
        - metadata.json         : core metadata about the run
        - chunk_index.json      : list of chunk metadata entries
        - overview.md           : human-readable summary of size + preview
        - chunks/CH-XXXX.txt    : one file per chunk

    Parameters
    ----------
    input_path:
        Original input file path.
    output_root:
        Root directory under which the output folder will be created.
    cleaned_text:
        Text after cleaning/normalization.
    token_count:
        Estimated total tokens in the cleaned text.
    tier_params:
        Tier parameters used for chunking.
    chunks:
        List of chunk dictionaries:
            {
                "chunk_id": str,
                "start_char": int,
                "end_char": int,
                "text": str,
                "token_estimate": int
            }
    extra_metadata:
        Additional metadata fields from the loader or pipeline.

    Returns
    -------
    Path
        Path to the directory where artifacts were written.
    """
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    output_dir = _make_output_dir(input_path, output_root)

    # 1) raw_text.txt
    raw_text_path = output_dir / "raw_text.txt"
    raw_text_path.write_text(cleaned_text, encoding="utf-8")

    # 2) metadata.json
    extra_metadata = extra_metadata or {}
    file_name = extra_metadata.get("file_name", input_path.name)
    file_type = extra_metadata.get("file_type", input_path.suffix.lstrip(".") or "unknown")
    full_path = extra_metadata.get("full_path", str(input_path.resolve()))
    page_count = extra_metadata.get("page_count", None)

    metadata_obj = Metadata(
        file_name=file_name,
        file_type=file_type,
        full_path=full_path,
        token_count=token_count,
        num_chunks=len(chunks),
        tier=tier_params.name,
        max_chunk_tokens=tier_params.max_chunk_tokens,
        overlap_tokens=tier_params.overlap_tokens,
        page_count=page_count,
    )

    metadata_dict = asdict(metadata_obj)
    # add run timestamp for debugging
    metadata_dict["run_timestamp"] = datetime.utcnow().isoformat() + "Z"

    metadata_path = output_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata_dict, indent=2), encoding="utf-8")

    # 3) chunk_index.json + chunk files
    chunk_index = []
    chunks_dir = output_dir / "chunks"

    for chunk in chunks:
        chunk_id = chunk["chunk_id"]
        chunk_text = chunk["text"]
        start_char = int(chunk.get("start_char", 0))
        end_char = int(chunk.get("end_char", 0))
        token_estimate = int(chunk.get("token_estimate", 0))

        chunk_filename = f"{chunk_id}.txt"
        chunk_path = chunks_dir / chunk_filename
        chunk_path.write_text(chunk_text, encoding="utf-8")

        chunk_index.append(
            {
                "chunk_id": chunk_id,
                "file": f"chunks/{chunk_filename}",
                "start_char": start_char,
                "end_char": end_char,
                "token_estimate": token_estimate,
            }
        )

    chunk_index_path = output_dir / "chunk_index.json"
    chunk_index_path.write_text(json.dumps(chunk_index, indent=2), encoding="utf-8")

    # 4) overview.md (very basic alpha version)
    overview_lines = []
    overview_lines.append(f"# Overview: {file_name}")
    overview_lines.append("")
    overview_lines.append(f"- Estimated tokens: {token_count}")
    overview_lines.append(f"- Tier: {tier_params.name}")
    overview_lines.append(f"- Number of chunks: {len(chunks)}")
    overview_lines.append("")
    overview_lines.append("## First lines (preview)")
    overview_lines.append("")

    # Show just the first ~10 lines of cleaned text as a preview
    preview_lines = cleaned_text.splitlines()[:10]
    for line in preview_lines:
        overview_lines.append(f"> {line}")

    overview_md = "\n".join(overview_lines).strip() + "\n"

    overview_path = output_dir / "overview.md"
    overview_path.write_text(overview_md, encoding="utf-8")

    return output_dir
