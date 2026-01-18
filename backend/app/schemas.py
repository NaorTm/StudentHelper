# backend/app/schemas.py
from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: UUID
    title: str
    institution: str | None = None
    source_type: str | None = None


class DocumentVersionOut(BaseModel):
    id: UUID
    document_id: UUID
    version_label: str
    effective_date: date | None = None
    published_date: date | None = None
    revision_date: date | None = None
    language: str | None = None
    categories: list[str] | None = None
    tags: list[str] | None = None
    trust_level: str | None = None
    is_active: bool
    source_uri: str | None = None
    file_path: str | None = None


class IngestionJobOut(BaseModel):
    id: UUID
    document_version_id: UUID
    status: str
    error_message: str | None = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    institution: str | None = None
    language: str | None = None
    categories: list[str] | None = None
    effective_date_start: date | None = None
    effective_date_end: date | None = None
    active_only: bool = True


class ChunkOut(BaseModel):
    id: UUID
    document_id: UUID
    document_title: str
    version_id: UUID
    version_label: str
    page_start: int
    page_end: int
    section_path: str | None = None
    excerpt: str
    relevance_score: float


class SearchResponse(BaseModel):
    chunks: list[ChunkOut]


class ConversationOut(BaseModel):
    id: UUID


class MessageCreateRequest(BaseModel):
    content: str
    institution: str | None = None
    language: str | None = None
    categories: list[str] | None = None
    effective_date_start: date | None = None
    effective_date_end: date | None = None
    top_k: int = 8


class CitationOut(BaseModel):
    citation_id: str
    document_title: str
    document_version_label: str
    effective_date: date | None
    pages: dict[str, int]
    section_path: str | None = None
    excerpt: str
    chunk_id: str
    relevance_score: float


class AnswerOut(BaseModel):
    answer_text: str
    steps: list[str] | None = None
    citations: list[CitationOut]
    confidence: str
    follow_up_questions: list[str] | None = None


class FeedbackCreateRequest(BaseModel):
    conversation_id: UUID
    message_id: UUID
    rating: str = Field(..., examples=["helpful", "not_helpful"])
    flags: list[str] | None = None
    notes: str | None = None


class ConversationMessagesOut(BaseModel):
    conversation_id: UUID
    messages: list[dict[str, Any]]
