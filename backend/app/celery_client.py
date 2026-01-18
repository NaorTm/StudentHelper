# backend/app/celery_client.py
from __future__ import annotations

from celery import Celery

from app.config import settings

celery_client = Celery(
    "backend",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
