# scripts/apply_migrations.py
from __future__ import annotations

import glob
import os
from pathlib import Path

import psycopg


def normalize_dsn(dsn: str) -> str:
    if dsn.startswith("postgresql+psycopg://"):
        return dsn.replace("postgresql+psycopg://", "postgresql://", 1)
    return dsn


def main() -> int:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL is required")
        return 1

    migration_paths = sorted(glob.glob("backend/db/migrations/*.sql"))
    if not migration_paths:
        print("No migrations found")
        return 1

    with psycopg.connect(normalize_dsn(dsn)) as conn:
        with conn.cursor() as cur:
            for path in migration_paths:
                sql = Path(path).read_text(encoding="utf-8")
                cur.execute(sql)
        conn.commit()

    print(f"Applied {len(migration_paths)} migrations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
