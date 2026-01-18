# worker/app/ingestion.py
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import fitz
from pgvector.psycopg import Vector, register_vector

from app.chunking import chunk_text
from app.db import get_conn
from app.embeddings import embed_texts
from app.sectioning import extract_sections


@dataclass
class ParsedChunk:
    text: str
    page_start: int
    page_end: int
    section_path: str | None
    excerpt: str
    source_hash: str


def parse_pdf(file_path: str) -> list[tuple[int, str]]:
    doc = fitz.open(file_path)
    pages = []
    for page_number in range(len(doc)):
        page = doc[page_number]
        text = page.get_text("text")
        pages.append((page_number + 1, text))
    doc.close()
    return pages


def build_chunks(pages: list[tuple[int, str]]) -> list[ParsedChunk]:
    parsed = []
    for page_number, text in pages:
        for section_path, section_text in extract_sections(text):
            for chunk in chunk_text(section_text, page_number, section_path):
                excerpt = chunk.text[:300]
                source_hash = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
                parsed.append(
                    ParsedChunk(
                        text=chunk.text,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        section_path=chunk.section_path,
                        excerpt=excerpt,
                        source_hash=source_hash,
                    )
                )
    return parsed


def store_chunks(version_id: str, chunks: list[ParsedChunk]) -> list[str]:
    if not chunks:
        return []

    chunk_ids = []
    with get_conn() as conn:
        with conn.cursor() as cur:
            for index, chunk in enumerate(chunks):
                cur.execute(
                    """
                    INSERT INTO chunks (
                        document_version_id, chunk_index, page_start, page_end,
                        section_path, text, excerpt, source_hash
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        version_id,
                        index,
                        chunk.page_start,
                        chunk.page_end,
                        chunk.section_path,
                        chunk.text,
                        chunk.excerpt,
                        chunk.source_hash,
                    ),
                )
                chunk_ids.append(cur.fetchone()["id"])
        conn.commit()
    return [str(chunk_id) for chunk_id in chunk_ids]


def store_embeddings(chunk_ids: list[str], vectors: list[list[float]], model_name: str) -> None:
    if not chunk_ids:
        return
    with get_conn() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            for chunk_id, vector in zip(chunk_ids, vectors, strict=True):
                cur.execute(
                    """
                    INSERT INTO embeddings (chunk_id, model_name, embedding_dim, vector)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (chunk_id, model_name, len(vector), Vector(vector)),
                )
        conn.commit()


def ingest_version(version_id: str, file_path: str, embeddings_model: str) -> int:
    pages = parse_pdf(file_path)
    chunks = build_chunks(pages)
    chunk_ids = store_chunks(version_id, chunks)
    if not chunk_ids:
        return 0
    vectors = embed_texts([chunk.text for chunk in chunks])
    store_embeddings(chunk_ids, vectors, embeddings_model)
    return len(chunk_ids)
