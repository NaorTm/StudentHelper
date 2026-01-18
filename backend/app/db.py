# backend/app/db.py
from __future__ import annotations

from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.config import settings


def _normalize_dsn(dsn: str) -> str:
    if dsn.startswith("postgresql+psycopg://"):
        return dsn.replace("postgresql+psycopg://", "postgresql://", 1)
    return dsn


@contextmanager
def get_conn():
    conn = psycopg.connect(_normalize_dsn(settings.database_url), row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()
