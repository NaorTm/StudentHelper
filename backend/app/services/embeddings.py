# backend/app/services/embeddings.py
from __future__ import annotations

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(settings.embeddings_model)


def embed_text(text: str) -> list[float]:
    model = _model()
    vector = model.encode(text, normalize_embeddings=True)
    return np.asarray(vector, dtype=float).tolist()
