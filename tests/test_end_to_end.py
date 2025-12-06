"""
End-to-end test for the alpha pipeline.

This uses a tiny .txt document to avoid external dependencies like pypdf
and python-docx, and verifies that core artifacts are created.
"""

from __future__ import annotations

from pathlib import Path

from doc_prep.pipeline import run_pipeline


def test_end_to_end_txt(tmp_path):
    # 1) Create a tiny text file
    sample_text = (
        "This is a small test document.\n\n"
        "It has a few paragraphs of text to verify chunking behavior.\n\n"
        "Final paragraph for good measure."
    )

    input_dir = tmp_path / "input"
    input_dir.mkdir()
    input_path = input_dir / "sample.txt"
    input_path.write_text(sample_text, encoding="utf-8")

    # 2) Run pipeline with output_root under tmp_path
    output_root = tmp_path / "artifacts"
    output_dir = run_pipeline(
        input_path=input_path,
        output_root=output_root,
        tier_override=None,
        max_chunk_tokens=80,  # small enough to guarantee multiple chunks for future tests
    )

    # 3) Basic structural checks
    assert output_dir.is_dir()

    raw_text_path = output_dir / "raw_text.txt"
    metadata_path = output_dir / "metadata.json"
    chunk_index_path = output_dir / "chunk_index.json"
    overview_path = output_dir / "overview.md"
    chunks_dir = output_dir / "chunks"

    assert raw_text_path.is_file()
    assert metadata_path.is_file()
    assert chunk_index_path.is_file()
    assert overview_path.is_file()
    assert chunks_dir.is_dir()

    # At least one chunk file should exist
    chunk_files = list(chunks_dir.glob("CH-*.txt"))
    assert len(chunk_files) >= 1

    # 4) Content sanity checks
    raw_text = raw_text_path.read_text(encoding="utf-8")
    assert "This is a small test document." in raw_text

    metadata = metadata_path.read_text(encoding="utf-8")
    assert '"file_name": "sample.txt"' in metadata
    assert '"token_count"' in metadata
    assert '"num_chunks"' in metadata

    chunk_index = chunk_index_path.read_text(encoding="utf-8")
    assert '"chunk_id"' in chunk_index
    assert '"file": "chunks/CH-' in chunk_index

    overview = overview_path.read_text(encoding="utf-8")
    assert "Overview: sample.txt" in overview
    assert "Estimated tokens:" in overview
