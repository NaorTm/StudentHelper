# worker/app/celery_app.py
from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.autodiscover_tasks(["app"])
