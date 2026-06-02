"""Integration tests for GET /v1/luu-nien/luan-context."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import app
from api.van_trinh_nam_luan_context import build_van_trinh_nam_luan_context
from api.schemas.van_trinh_nam import validate_van_trinh_nam_luan_context
from engine.can_chi import get_can_chi_year, is_xung
from engine.pillars import get_tu_tru

client = TestClient(app)

_BIRTH = {"birth_date": "15/03/1984", "birth_time": 8, "gender": 1}
_PARAMS = {**_BIRTH, "year": 2026}

# Birth 21/03/1990 — đại vận đổi tháng 4 năm 2026 (Nhâm Ngọ → Quý Mùi)
_TRANSITION_BIRTH = {"birth_date": "21/03/1990", "birth_time": 8, "gender": 1, "year": 2026}

_PROSE_MARKERS = (
    "có cửa thăng tiến",
    "thuận cho tích lũy",
    "tránh quyết định hôn nhân",
    "duy trì thói quen tốt",
    "Thuận",
    "Cần thận trọng",
)


def test_luan_context_200():
    r = client.get("/v1/luu-nien/luan-context", params=_PARAMS)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert len(data["part_b"]["luu_nguyet_months"]) == 12


def test_twelve_months_b1_b4():
    data = client.get("/v1/luu-nien/luan-context", params=_PARAMS).json()
    for m in data["part_b"]["luu_nguyet_months"]:
        assert "b1_month_theme" in m
        assert "b2_month_emphasis" in m
        assert "b3_luu_nhat_calendar" in m
        assert "b4_action" in m
        assert len(m["b2_month_emphasis"]) <= 2


def test_four_aspects():
    aspects = client.get("/v1/luu-nien/luan-context", params=_PARAMS).json()
    fa = aspects["part_a"]["four_aspects_year"]
    assert len(fa) == 4
    ids = {a["aspect_id"] for a in fa}
    assert ids == {"su_nghiep", "tai_loc", "tinh_cam", "suc_khoe"}
    assert aspects["part_a"]["you_this_year"]["nhat_chu_hanh"] == "Thổ"


def test_b3_has_calendar():
    data = client.get("/v1/luu-nien/luan-context", params=_PARAMS).json()
    for m in data["part_b"]["luu_nguyet_months"]:
        b3 = m["b3_luu_nhat_calendar"]
        assert b3.get("best_days") or b3.get("avoid_days")


def test_schema_validates():
    payload = build_van_trinh_nam_luan_context(
        year=2026,
        birth_date_iso="1984-03-15",
        birth_time=8,
        gender=1,
        use_cache=False,
    )
    validate_van_trinh_nam_luan_context(payload)


def _json_keys(obj, found: set[str] | None = None) -> set[str]:
    found = found or set()
    if isinstance(obj, dict):
        found.update(obj.keys())
        for v in obj.values():
            _json_keys(v, found)
    elif isinstance(obj, list):
        for item in obj:
            _json_keys(item, found)
    return found


def test_no_prose_verdict_keys():
    payload = build_van_trinh_nam_luan_context(
        year=2026,
        birth_date_iso="1984-03-15",
        birth_time=8,
        gender=1,
        use_cache=False,
    )
    forbidden = {"verdict_vi", "delta_vs_year_vi", "giai_hoa_goi_y_vi", "year_theme_vi"}
    keys = _json_keys({k: v for k, v in payload.items() if k != "writing_brief"})
    assert not (keys & forbidden)


def test_no_prose_in_aspect_bullets():
    payload = build_van_trinh_nam_luan_context(
        year=2026,
        birth_date_iso="1984-03-15",
        birth_time=8,
        gender=1,
        use_cache=False,
    )
    for aspect in payload["part_a"]["four_aspects_year"]:
        text = " ".join(aspect["fact_bullets_vi"]).lower()
        for marker in _PROSE_MARKERS:
            assert marker.lower() not in text, f"prose marker in {aspect['aspect_id']}: {marker}"


def test_dai_van_transition_in_year():
    payload = build_van_trinh_nam_luan_context(
        year=2026,
        birth_date_iso="1990-03-21",
        birth_time=8,
        gender=1,
        use_cache=False,
    )
    tr = payload["part_a"]["you_this_year"]["dai_van"]["transition_in_year"]
    assert tr is not None
    assert tr["from_display"] == "Nhâm Ngọ"
    assert tr["to_display"] == "Quý Mùi"
    assert tr["applies_from_month"] == 4


def test_tinh_cam_parity_with_tinh_duyen():
    payload = build_van_trinh_nam_luan_context(
        year=2026,
        birth_date_iso="1984-03-15",
        birth_time=8,
        gender=1,
        use_cache=False,
    )
    tu_tru = get_tu_tru("1984-03-15", 8)
    ycc = get_can_chi_year(2026)
    flow_xung = is_xung(tu_tru["year"]["chi_idx"], ycc["chi_idx"])
    tinh_cam = next(
        a for a in payload["part_a"]["four_aspects_year"] if a["aspect_id"] == "tinh_cam"
    )
    if flow_xung:
        assert tinh_cam["verdict_signal"] == "than_trong"
        assert "flow_year_xung_tuoi" in tinh_cam["driver_tags"]
    assert any(t.startswith("aspect:tinh_cam") for t in tinh_cam["driver_tags"])
