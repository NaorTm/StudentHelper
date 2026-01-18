# backend/app/config.py
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str
    redis_url: str
    files_dir: str
    embeddings_model: str
    reranker_model: str | None = None
    reranker_top_n: int = 5
    llm_provider: str
    llm_model: str
    llm_api_key: str
    admin_token: str
    min_similarity_score: float = 0.2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
