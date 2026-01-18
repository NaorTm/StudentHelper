# worker/app/embeddings.py
from __future__ import annotations

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(settings.embeddings_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [np.asarray(vector, dtype=float).tolist() for vector in vectors]
