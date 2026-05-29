"""Integration tests — Direction C P3 deferred items."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

_GIO_KEYS = {"chi", "chi_name", "start_hour", "end_hour", "label_vi", "range"}


def test_health_p3_fields():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "engine_version" in data


def test_rate_limit_headers_present():
    r = client.get("/health")
    assert "X-RateLimit-Limit" in r.headers
    assert "X-RateLimit-Remaining" in r.headers


def test_gio_slot_shape_ngay_hom_nay():
    r = client.get(
        "/v1/ngay-hom-nay",
        params={"birth_date": "15/03/1984", "date": "2026-05-28"},
    )
    assert r.status_code == 200
    data = r.json()
    for slot in data["gio_tot"]:
        assert _GIO_KEYS <= set(slot.keys())


def test_purpose_rows_on_day_detail():
    r = client.get(
        "/v1/day-detail",
        params={
            "birth_date": "15/03/1984",
            "birth_time": 8,
            "gender": 1,
            "date": "2026-05-28",
            "mode": "personalized",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "purpose_rows" in data
    assert len(data["purpose_rows"]) >= 10
    row = data["purpose_rows"][0]
    assert {"intent", "intent_label_vi", "verdict", "reason_vi"} <= set(row.keys())


def test_chon_ngay_candidates_scanned_alias():
    r = client.post(
        "/v1/chon-ngay",
        json={
            "birth_date": "15/03/1984",
            "intent": "KHAI_TRUONG",
            "range_start": "01/04/2026",
            "range_end": "30/04/2026",
            "top_n": 3,
        },
    )
    assert r.status_code == 200
    meta = r.json()["meta"]
    assert meta["candidates_scanned"] == meta["days_passed_layer2"]


def test_hop_tuoi_v2_criteria_points():
    r = client.post(
        "/v1/hop-tuoi",
        json={
            "person1_birth_date": "15/05/1990",
            "person2_birth_date": "20/03/1992",
            "person1_birth_time": 8,
            "person2_birth_time": 10,
            "relationship_type": "PHU_THE",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["version"] == 2
    for c in data["criteria"]:
        assert "points" in c
        assert 0 <= c["points"] <= 100
