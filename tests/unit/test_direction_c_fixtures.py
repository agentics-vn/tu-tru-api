"""Golden fixtures for Direction C contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from api.schemas.direction_c import validate_chon_ngay_response

FIXTURES = Path(__file__).resolve().parents[2] / "docs" / "fixtures" / "direction-c"

pytestmark = pytest.mark.direction_c


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_chon_ngay_empty_fixture_contract():
    data = _load("chon-ngay-empty.json")
    validate_chon_ngay_response(data)
    assert data["ranked_days"] == []
    assert data["empty_reason_vi"]


def test_day_detail_fixture_scores():
    p35 = _load("day-detail-personalized-35.json")
    p76 = _load("day-detail-personalized-76.json")
    assert p35["score"] == 35
    assert p76["score"] == 76
