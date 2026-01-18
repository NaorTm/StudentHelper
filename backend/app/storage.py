# backend/app/storage.py
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_upload_file(base_dir: str, version_id: str, upload_file: UploadFile) -> str:
    target_dir = Path(base_dir) / version_id
    ensure_dir(target_dir)
    filename = f"{uuid4().hex}_{upload_file.filename}"
    target_path = target_dir / filename
    with target_path.open("wb") as target:
        while True:
            chunk = upload_file.file.read(1024 * 1024)
            if not chunk:
                break
            target.write(chunk)
    return str(target_path)
