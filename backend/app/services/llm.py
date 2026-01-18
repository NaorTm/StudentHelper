# backend/app/services/llm.py
from __future__ import annotations

import json
import os
import urllib.request

from app.config import settings


def _post_json(url: str, headers: dict[str, str], payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def call_openai(system_prompt: str, user_prompt: str) -> str:
    url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.llm_model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    response = _post_json(url, headers, payload)
    return response["choices"][0]["message"]["content"]


def call_anthropic(system_prompt: str, user_prompt: str) -> str:
    url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages")
    headers = {
        "x-api-key": settings.llm_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": settings.llm_model,
        "temperature": 0,
        "max_tokens": 800,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt},
        ],
    }
    response = _post_json(url, headers, payload)
    content = response.get("content", [])
    if not content:
        return "{}"
    return content[0].get("text", "{}")


def call_llm(system_prompt: str, user_prompt: str) -> str:
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return call_openai(system_prompt, user_prompt)
    if provider == "anthropic":
        return call_anthropic(system_prompt, user_prompt)
    raise ValueError(f"unsupported llm provider: {settings.llm_provider}")
