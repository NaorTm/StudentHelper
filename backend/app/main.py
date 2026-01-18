# backend/app/main.py
from __future__ import annotations

from fastapi import FastAPI

from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.search import router as search_router

app = FastAPI(title="Student Rights Copilot")
app.include_router(health_router)
app.include_router(admin_router)
app.include_router(search_router)
app.include_router(chat_router)
