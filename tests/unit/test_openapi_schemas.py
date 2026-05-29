"""OpenAPI schema documents Direction C response contracts."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from app import app


def _schema(name: str) -> dict:
    return app.openapi()["components"]["schemas"][name]


def test_chon_ngay_response_schema_has_ranked_days():
    props = _schema("ChonNgayResponse")["properties"]
    assert "ranked_days" in props
    assert "empty_reason_vi" in props
    assert "score_methodology" in props
    assert props["ranked_days"]["items"]["$ref"].endswith("/RankedDay")


def test_ranked_day_schema_has_gio_slot_fields():
    props = _schema("RankedDay")["properties"]
    gio_ref = props["gio_tot"]["items"]["$ref"]
    slot_props = _schema(gio_ref.split("/")[-1])["properties"]
    assert {"chi", "chi_name", "start_hour", "end_hour", "label_vi", "range"} <= set(slot_props)


def test_day_detail_and_luan_context_schemas():
    detail = _schema("DayDetailResponse")["properties"]
    assert "breakdown" in detail
    assert "purpose_rows" in detail
    luan = _schema("LuanContextResponse")["properties"]
    assert "gio_tot_labels" in luan
    assert "breakdown_summary" in luan


def test_health_response_schema():
    props = _schema("HealthResponse")["properties"]
    assert {"status", "version", "engine_version"} <= set(props)
