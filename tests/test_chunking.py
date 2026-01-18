# tests/test_chunking.py
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "worker" / "app"))

from sectioning import extract_sections  # type: ignore
from chunking import chunk_text  # type: ignore


def test_extract_sections_detects_heading():
    text = "1.1 Overview\nThis is the overview paragraph.\n\nBACKGROUND\nMore text here."
    sections = extract_sections(text)
    assert len(sections) == 2
    assert sections[0][0].startswith("1.1")
    assert sections[1][0] == "BACKGROUND"


def test_chunk_text_preserves_section_path():
    chunks = chunk_text("word " * 200, page_number=2, section_path="1.2 Scope", target_words=50, overlap=10)
    assert chunks
    assert all(chunk.section_path == "1.2 Scope" for chunk in chunks)
    assert all(chunk.page_start == 2 for chunk in chunks)
