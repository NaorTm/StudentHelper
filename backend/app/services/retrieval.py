# backend/app/services/retrieval.py
from __future__ import annotations

from datetime import date

from pgvector.psycopg import Vector, register_vector

from app.db import get_conn
from app.services.embeddings import embed_text


def retrieve_chunks(
    query: str,
    top_k: int,
    institution: str | None,
    language: str | None,
    categories: list[str] | None,
    effective_date_start: date | None,
    effective_date_end: date | None,
    active_only: bool,
):
    embedding = embed_text(query)
    vector = Vector(embedding)

    filters = []
    params: list[object] = []

    if active_only:
        filters.append("document_versions.is_active = TRUE")
    if institution:
        filters.append("documents.institution = %s")
        params.append(institution)
    if language:
        filters.append("document_versions.language = %s")
        params.append(language)
    if categories:
        filters.append("document_versions.categories && %s")
        params.append(categories)
    if effective_date_start:
        filters.append("document_versions.effective_date >= %s")
        params.append(effective_date_start)
    if effective_date_end:
        filters.append("document_versions.effective_date <= %s")
        params.append(effective_date_end)

    where_sql = "WHERE " + " AND ".join(filters) if filters else ""

    sql = f"""
        SELECT
            chunks.id AS chunk_id,
            chunks.page_start,
            chunks.page_end,
            chunks.section_path,
            COALESCE(chunks.excerpt, LEFT(chunks.text, 500)) AS excerpt,
            chunks.text AS full_text,
            document_versions.id AS version_id,
            document_versions.version_label,
            document_versions.effective_date,
            documents.id AS document_id,
            documents.title AS document_title,
            (embeddings.vector <-> %s) AS distance
        FROM embeddings
        JOIN chunks ON embeddings.chunk_id = chunks.id
        JOIN document_versions ON chunks.document_version_id = document_versions.id
        JOIN documents ON document_versions.document_id = documents.id
        {where_sql}
        ORDER BY embeddings.vector <-> %s
        LIMIT %s
    """

    with get_conn() as conn:
        register_vector(conn)
        with conn.cursor() as cur:
            params_with_vector = [vector] + params + [vector, top_k]
            cur.execute(sql, params_with_vector)
            rows = cur.fetchall()

    results = []
    for row in rows:
        distance = float(row["distance"])
        score = 1.0 / (1.0 + distance)
        results.append(
            {
                "chunk_id": str(row["chunk_id"]),
                "page_start": row["page_start"],
                "page_end": row["page_end"],
                "section_path": row["section_path"],
                "excerpt": row["excerpt"],
                "text": row["full_text"],
                "version_id": str(row["version_id"]),
                "version_label": row["version_label"],
                "effective_date": row["effective_date"],
                "document_id": str(row["document_id"]),
                "document_title": row["document_title"],
                "score": score,
                "distance": distance,
            }
        )

    return results
