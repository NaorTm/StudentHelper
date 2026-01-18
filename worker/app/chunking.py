# worker/app/chunking.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    page_start: int
    page_end: int
    section_path: str | None


def chunk_text(
    text: str,
    page_number: int,
    section_path: str | None,
    target_words: int = 450,
    overlap: int = 80,
) -> list[Chunk]:
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(len(words), start + target_words)
        chunk_words = words[start:end]
        chunks.append(
            Chunk(
                text=" ".join(chunk_words),
                page_start=page_number,
                page_end=page_number,
                section_path=section_path,
            )
        )
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks
