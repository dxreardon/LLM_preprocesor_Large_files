"""
Command-line interface for the doc_prep alpha tool.

Usage (from repo root, after installing dependencies):

    python -m doc_prep.cli process path/to/file.pdf -o path/to/output_root

This keeps the CLI thin: it just parses arguments and calls pipeline.run_pipeline().
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import run_pipeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="doc_prep",
        description=(
            "Convert a PDF/DOCX/TXT document into 'LLM-ready' chunked artifacts "
            "(cleaned text, chunks, chunk index, basic metadata)."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Sub-commands",
    )

    # Only one sub-command for the alpha: 'process'
    process_parser = subparsers.add_parser(
        "process",
        help="Process a single document and write artifacts.",
    )
    process_parser.add_argument(
        "input_path",
        type=str,
        help="Path to the input .pdf, .docx, or .txt file.",
    )
    process_parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="artifacts",
        help=(
            "Directory under which a new per-run output folder will be created. "
            "Defaults to ./artifacts"
        ),
    )
    process_parser.add_argument(
        "--tier",
        type=str,
        default=None,
        help=(
            "Optional tier label override (e.g. 'T0', 'T1', 'T2'). "
            "This only affects the name stored in metadata; chunk sizing "
            "still comes from the document size unless you also set "
            "--max-chunk-tokens."
        ),
    )
    process_parser.add_argument(
        "--max-chunk-tokens",
        type=int,
        default=None,
        help=(
            "Optional override for maximum tokens per chunk. "
            "If omitted, a default derived from the inferred tier is used."
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Entry point for the CLI.

    Parameters
    ----------
    argv:
        Optional list of arguments (defaults to sys.argv[1:]).

    Returns
    -------
    int
        Exit code (0 for success, non-zero for error).
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "process":
        input_path = Path(args.input_path)
        output_root = Path(args.output_dir)

        try:
            output_dir = run_pipeline(
                input_path=input_path,
                output_root=output_root,
                tier_override=args.tier,
                max_chunk_tokens=args.max_chunk_tokens,
            )
        except Exception as exc:  # alpha: simple error reporting
            parser.exit(status=1, message=f"Error: {exc}\n")

        print(f"\n✓ Processing complete.")
        print(f"  Input : {input_path}")
        print(f"  Output: {output_dir}")
        return 0

    # Should be unreachable because command is required
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
