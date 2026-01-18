# backend/app/services/validation.py
from __future__ import annotations

from typing import Iterable


def validate_claims(claims: list[dict], allowed_ids: Iterable[str]) -> tuple[bool, str | None]:
    allowed_set = set(allowed_ids)
    for claim in claims:
        citation_ids = claim.get("citation_ids", [])
        if not citation_ids:
            return False, "claim_missing_citation"
        for citation_id in citation_ids:
            if citation_id not in allowed_set:
                return False, "citation_not_in_selected_chunks"
    return True, None
