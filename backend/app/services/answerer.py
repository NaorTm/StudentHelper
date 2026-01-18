# backend/app/services/answerer.py
from __future__ import annotations

import json

from pydantic import ValidationError

from app.config import settings
from app.services.llm import call_llm
from app.services.llm_schema import StructuredAnswer
from app.services.validation import validate_claims


def _build_llm_prompt(chunks: list[dict]) -> tuple[str, str]:
    system_prompt = (
        "You are a document-grounded assistant. Use only the provided sources. "
        "Every factual claim must cite at least one source id. "
        "If evidence is missing or ambiguous, set confidence to \"abstain\" or \"uncertain\"."
    )

    sources_lines = []
    for chunk in chunks:
        sources_lines.append(
            f"- id: {chunk['chunk_id']}\n"
            f"  title: {chunk['document_title']}\n"
            f"  version: {chunk['version_label']}\n"
            f"  pages: {chunk['page_start']}-{chunk['page_end']}\n"
            f"  excerpt: {chunk['excerpt']}"
        )

    user_prompt = "\n".join(
        [
            "Return JSON only with the schema:",
            "{",
            '  \"claims\": [{\"text\": \"...\", \"citation_ids\": [\"...\"]}],',
            '  \"steps\": [\"...\"],',
            '  \"confidence\": \"supported|uncertain|abstain\",',
            '  \"follow_up_questions\": [\"...\"]',
            "}",
            "",
            "Sources:",
            "\n".join(sources_lines),
        ]
    )

    return system_prompt, user_prompt


def build_structured_answer(chunks: list[dict]) -> dict:
    system_prompt, user_prompt = _build_llm_prompt(chunks)
    raw = call_llm(system_prompt, user_prompt)
    parsed = json.loads(raw)
    structured = StructuredAnswer.model_validate(parsed)
    return structured.model_dump()


def render_answer(structured: dict, citations: list[dict]) -> dict:
    claims = structured.get("claims", [])
    summary = ""
    if claims:
        summary = claims[0]["text"]
    else:
        summary = "I could not find this in the corpus."

    conditions = []
    for claim in claims[1:3]:
        conditions.append(f"- {claim['text']}")

    steps = structured.get("steps") or []
    step_lines = [f"- {step}" for step in steps] if steps else ["- None."]

    sources = []
    for citation in citations:
        sources.append(
            "- {title} ({version}, pages {start}-{end}): {excerpt}".format(
                title=citation["document_title"],
                version=citation["document_version_label"],
                start=citation["pages"]["start"],
                end=citation["pages"]["end"],
                excerpt=citation["excerpt"],
            )
        )

    answer_text = "\n".join(
        [
            "Summary:",
            summary,
            "",
            "Conditions and exceptions:",
            "\n".join(conditions) if conditions else "- None.",
            "",
            "Steps to act:",
            "\n".join(step_lines),
            "",
            "Sources:",
            "\n".join(sources) if sources else "- None.",
        ]
    )

    return {
        "answer_text": answer_text,
        "steps": structured.get("steps"),
        "citations": citations,
        "confidence": structured.get("confidence", "abstain"),
        "follow_up_questions": structured.get("follow_up_questions"),
    }


def generate_answer(chunks: list[dict]) -> dict:
    try:
        structured = build_structured_answer(chunks)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        structured = {
            "claims": [],
            "steps": None,
            "confidence": "abstain",
            "follow_up_questions": None,
            "error": str(exc),
        }
    allowed_ids = [chunk["chunk_id"] for chunk in chunks]
    ok, error = validate_claims(structured.get("claims", []), allowed_ids)
    if not ok:
        structured = {
            "claims": [],
            "steps": None,
            "confidence": "abstain",
            "follow_up_questions": None,
            "error": error,
        }

    citations = []
    for chunk in chunks:
        citations.append(
            {
                "citation_id": f"cite-{chunk['chunk_id']}",
                "document_title": chunk["document_title"],
                "document_version_label": chunk["version_label"],
                "effective_date": chunk["effective_date"],
                "pages": {"start": chunk["page_start"], "end": chunk["page_end"]},
                "section_path": chunk["section_path"],
                "excerpt": chunk["excerpt"],
                "chunk_id": chunk["chunk_id"],
                "relevance_score": chunk["score"],
            }
        )

    return render_answer(structured, citations)


def has_min_relevance(chunks: list[dict]) -> bool:
    if not chunks:
        return False
    return chunks[0]["score"] >= settings.min_similarity_score
