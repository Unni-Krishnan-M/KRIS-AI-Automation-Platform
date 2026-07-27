"""Unit tests for the text chunker (no database or services)."""

from __future__ import annotations

import pytest

from app.utils.chunking import chunk_text


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_text("   ") == []


def test_short_text_is_single_chunk() -> None:
    assert chunk_text("hello world") == ["hello world"]


def test_long_text_is_split_with_overlap() -> None:
    text = "abcdefghij" * 20  # 200 chars
    chunks = chunk_text(text, chunk_size=80, overlap=20)
    assert len(chunks) > 1
    # Every chunk is within the size bound.
    assert all(len(c) <= 80 for c in chunks)
    # Consecutive chunks overlap by `overlap` characters.
    assert chunks[0][-20:] == chunks[1][:20]


def test_invalid_overlap_raises() -> None:
    with pytest.raises(ValueError):
        chunk_text("abc", chunk_size=10, overlap=10)
