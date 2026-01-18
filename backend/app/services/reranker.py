# backend/app/services/reranker.py
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.config import settings


@lru_cache(maxsize=1)
def _model() -> CrossEncoder | None:
    if not settings.reranker_model:
        return None
    return CrossEncoder(settings.reranker_model)


def rerank_chunks(query: str, chunks: list[dict], top_n: int) -> list[dict]:
    model = _model()
    if model is None or not chunks:
        return chunks

    pairs = [(query, chunk.get("text") or chunk.get("excerpt") or "") for chunk in chunks]
    scores = model.predict(pairs)

    for chunk, score in zip(chunks, scores, strict=True):
        chunk["rerank_score"] = float(score)

    reranked = sorted(chunks, key=lambda item: item.get("rerank_score", 0.0), reverse=True)
    return reranked[:top_n]
