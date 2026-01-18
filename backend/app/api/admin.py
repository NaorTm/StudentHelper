# backend/app/api/admin.py
from __future__ import annotations

from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.celery_client import celery_client
from app.config import settings
from app.db import get_conn
from app.deps import require_admin_token
from app.storage import save_upload_file

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/documents", dependencies=[Depends(require_admin_token)])
def create_document(
    title: str = Form(...),
    institution: str | None = Form(default=None),
    source_type: str | None = Form(default=None),
    version_label: str = Form(...),
    effective_date: date | None = Form(default=None),
    published_date: date | None = Form(default=None),
    revision_date: date | None = Form(default=None),
    language: str | None = Form(default=None),
    categories: list[str] | None = Form(default=None),
    tags: list[str] | None = Form(default=None),
    trust_level: str | None = Form(default=None),
    source_uri: str | None = Form(default=None),
    file: UploadFile = File(...),
):
    document_id = str(uuid4())
    version_id = str(uuid4())

    file_path = save_upload_file(settings.files_dir, version_id, file)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (id, title, institution, source_type)
                VALUES (%s, %s, %s, %s)
                """,
                (document_id, title, institution, source_type),
            )
            cur.execute(
                """
                INSERT INTO document_versions (
                    id, document_id, version_label, effective_date, published_date,
                    revision_date, language, categories, tags, trust_level, source_uri, file_path
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    version_id,
                    document_id,
                    version_label,
                    effective_date,
                    published_date,
                    revision_date,
                    language,
                    categories,
                    tags,
                    trust_level,
                    source_uri,
                    file_path,
                ),
            )
            cur.execute(
                """
                INSERT INTO ingestion_jobs (document_version_id, status)
                VALUES (%s, %s)
                RETURNING id
                """,
                (version_id, "queued"),
            )
            job_id = cur.fetchone()["id"]
        conn.commit()

    celery_client.send_task("worker.ingest_document_version", args=[version_id, str(job_id)])

    return {"document_id": document_id, "version_id": version_id, "ingestion_job_id": str(job_id)}


@router.post("/documents/{document_id}/versions", dependencies=[Depends(require_admin_token)])
def create_document_version(
    document_id: str,
    version_label: str = Form(...),
    effective_date: date | None = Form(default=None),
    published_date: date | None = Form(default=None),
    revision_date: date | None = Form(default=None),
    language: str | None = Form(default=None),
    categories: list[str] | None = Form(default=None),
    tags: list[str] | None = Form(default=None),
    trust_level: str | None = Form(default=None),
    source_uri: str | None = Form(default=None),
    file: UploadFile = File(...),
):
    version_id = str(uuid4())
    file_path = save_upload_file(settings.files_dir, version_id, file)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO document_versions (
                    id, document_id, version_label, effective_date, published_date,
                    revision_date, language, categories, tags, trust_level, source_uri, file_path
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    version_id,
                    document_id,
                    version_label,
                    effective_date,
                    published_date,
                    revision_date,
                    language,
                    categories,
                    tags,
                    trust_level,
                    source_uri,
                    file_path,
                ),
            )
            cur.execute(
                """
                INSERT INTO ingestion_jobs (document_version_id, status)
                VALUES (%s, %s)
                RETURNING id
                """,
                (version_id, "queued"),
            )
            job_id = cur.fetchone()["id"]
        conn.commit()

    celery_client.send_task("worker.ingest_document_version", args=[version_id, str(job_id)])

    return {"version_id": version_id, "ingestion_job_id": str(job_id)}


@router.get("/documents", dependencies=[Depends(require_admin_token)])
def list_documents():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, institution, source_type FROM documents ORDER BY created_at DESC")
            rows = cur.fetchall()
    return rows


@router.get("/documents/{document_id}", dependencies=[Depends(require_admin_token)])
def get_document(document_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, institution, source_type
                FROM documents
                WHERE id = %s
                """,
                (document_id,),
            )
            doc = cur.fetchone()
            cur.execute(
                """
                SELECT * FROM document_versions
                WHERE document_id = %s
                ORDER BY created_at DESC
                """,
                (document_id,),
            )
            versions = cur.fetchall()
    return {"document": doc, "versions": versions}


@router.post("/document-versions/{version_id}/activate", dependencies=[Depends(require_admin_token)])
def activate_version(version_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE document_versions SET is_active = TRUE, updated_at = NOW() WHERE id = %s",
                (version_id,),
            )
        conn.commit()
    return {"version_id": version_id, "is_active": True}


@router.get("/ingestion-jobs/{job_id}", dependencies=[Depends(require_admin_token)])
def get_ingestion_job(job_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, document_version_id, status, error_message FROM ingestion_jobs WHERE id = %s",
                (job_id,),
            )
            job = cur.fetchone()
    return job


@router.get("/explain/conversations/{conversation_id}", dependencies=[Depends(require_admin_token)])
def explain_conversation(conversation_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, retrieved_chunk_ids, similarity_scores, rerank_scores, filters, corpus_snapshot_id
                FROM retrieval_traces
                WHERE conversation_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (conversation_id,),
            )
            trace = cur.fetchone()

            if not trace:
                return {"conversation_id": conversation_id, "retrieval_trace": None, "chunks": []}

            cur.execute(
                """
                SELECT
                    chunks.id AS chunk_id,
                    chunks.page_start,
                    chunks.page_end,
                    chunks.section_path,
                    COALESCE(chunks.excerpt, LEFT(chunks.text, 300)) AS excerpt,
                    document_versions.version_label,
                    documents.title AS document_title
                FROM chunks
                JOIN document_versions ON chunks.document_version_id = document_versions.id
                JOIN documents ON document_versions.document_id = documents.id
                WHERE chunks.id = ANY(%s)
                """,
                (trace["retrieved_chunk_ids"],),
            )
            rows = cur.fetchall()

    chunk_map = {str(row["chunk_id"]): row for row in rows}
    ordered = []
    for index, chunk_id in enumerate(trace["retrieved_chunk_ids"]):
        row = chunk_map.get(str(chunk_id))
        if not row:
            continue
        ordered.append(
            {
                "chunk_id": str(row["chunk_id"]),
                "document_title": row["document_title"],
                "version_label": row["version_label"],
                "page_start": row["page_start"],
                "page_end": row["page_end"],
                "section_path": row["section_path"],
                "excerpt": row["excerpt"],
                "similarity_score": trace["similarity_scores"][index]
                if trace["similarity_scores"]
                else None,
                "rerank_score": trace["rerank_scores"][index]
                if trace["rerank_scores"]
                else None,
            }
        )

    return {
        "conversation_id": conversation_id,
        "retrieval_trace": {
            "id": str(trace["id"]),
            "filters": trace["filters"],
            "corpus_snapshot_id": trace["corpus_snapshot_id"],
        },
        "chunks": ordered,
    }
