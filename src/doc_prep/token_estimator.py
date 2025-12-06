"""
token_estimator.py

Approximate token counting for sizing and chunking.

Alpha version:
- If tiktoken is installed, use it (cl100k_base encoding).
- Otherwise, fall back to a simple heuristic based on word count.
"""

from __future__ import annotations


def _estimate_tokens_heuristic(text: str) -> int:
    """
    Fallback heuristic: estimate tokens from word count.

    Rough rule of thumb: 1 token ≈ 0.75 words.
    """
    if not text:
        return 0

    words = text.split()
    # multiply by ~1.3 to convert words -> tokens (inverse of 0.75)
    approx_tokens = int(len(words) * 1.3)
    return max(1, approx_tokens)


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in the given text.

    Parameters
    ----------
    text:
        Input text.

    Returns
    -------
    int
        Approximate token count.

    Notes
    -----
    - If the `tiktoken` package is available, we use the `cl100k_base`
      encoding (which is used by many modern OpenAI models) to get a
      more accurate count.
    - If `tiktoken` is not available, we use a word-count heuristic.
    """
    # Try to use tiktoken if present, otherwise use heuristic
    try:
        import tiktoken  # type: ignore

        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Any import or runtime error -> fallback
        return _estimate_tokens_heuristic(text)
