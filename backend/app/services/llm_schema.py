# backend/app/services/llm_schema.py
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Claim(BaseModel):
    text: str
    citation_ids: list[str] = Field(default_factory=list)


class StructuredAnswer(BaseModel):
    claims: list[Claim] = Field(default_factory=list)
    steps: list[str] | None = None
    confidence: Literal["supported", "uncertain", "abstain"]
    follow_up_questions: list[str] | None = None
