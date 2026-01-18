# worker/app/tasks.py
from __future__ import annotations

from celery import shared_task

from app.config import settings
from app.db import get_conn
from app.ingestion import ingest_version


@shared_task(name="worker.ingest_document_version")
def ingest_document_version(version_id: str, job_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE ingestion_jobs SET status = %s, started_at = NOW() WHERE id = %s",
                ("processing", job_id),
            )
            cur.execute(
                "SELECT file_path FROM document_versions WHERE id = %s",
                (version_id,),
            )
            row = cur.fetchone()
        conn.commit()

    if not row or not row.get("file_path"):
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ingestion_jobs SET status = %s, error_message = %s, finished_at = NOW() WHERE id = %s",
                    ("failed", "file_path_missing", job_id),
                )
            conn.commit()
        return

    try:
        ingest_version(version_id, row["file_path"], settings.embeddings_model)
    except Exception as exc:  # noqa: BLE001
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE ingestion_jobs SET status = %s, error_message = %s, finished_at = NOW() WHERE id = %s",
                    ("failed", str(exc), job_id),
                )
            conn.commit()
        raise

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE ingestion_jobs SET status = %s, finished_at = NOW() WHERE id = %s",
                ("completed", job_id),
            )
        conn.commit()
