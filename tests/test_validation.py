# tests/test_validation.py
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend" / "app"))

from services.validation import validate_claims  # type: ignore


def test_validate_claims_missing_citation():
    ok, error = validate_claims([{"text": "test", "citation_ids": []}], ["a"])
    assert ok is False
    assert error == "claim_missing_citation"


def test_validate_claims_not_in_set():
    ok, error = validate_claims([{"text": "test", "citation_ids": ["b"]}], ["a"])
    assert ok is False
    assert error == "citation_not_in_selected_chunks"


def test_validate_claims_ok():
    ok, error = validate_claims([{"text": "test", "citation_ids": ["a"]}], ["a"])
    assert ok is True
    assert error is None
