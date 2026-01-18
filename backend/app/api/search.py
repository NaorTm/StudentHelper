# backend/app/api/search.py
from __future__ import annotations

from fastapi import APIRouter

from app.schemas import SearchRequest, SearchResponse
from app.services.retrieval import retrieve_chunks

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    chunks = retrieve_chunks(
        query=request.query,
        top_k=request.top_k,
        institution=request.institution,
        language=request.language,
        categories=request.categories,
        effective_date_start=request.effective_date_start,
        effective_date_end=request.effective_date_end,
        active_only=request.active_only,
    )

    response_chunks = []
    for chunk in chunks:
        response_chunks.append(
            {
                "id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "document_title": chunk["document_title"],
                "version_id": chunk["version_id"],
                "version_label": chunk["version_label"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "section_path": chunk["section_path"],
                "excerpt": chunk["excerpt"],
                "relevance_score": chunk["score"],
            }
        )

    return {"chunks": response_chunks}
