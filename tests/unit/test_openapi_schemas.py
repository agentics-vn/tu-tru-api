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


def test_lich_thang_response_has_days_and_score_methodology():
    props = _schema("LichThangResponse")["properties"]
    assert "days" in props
    assert props["days"]["type"] == "array"
    day_props = _schema(props["days"]["items"]["$ref"].split("/")[-1])["properties"]
    assert {"date", "score", "gio_tot", "summary"} <= set(day_props)
    assert "score_methodology" in props


def test_ngay_hom_nay_response_schema():
    props = _schema("NgayHomNayResponse")["properties"]
    assert {"score", "score_methodology", "gio_tot", "gio_xau", "daily_advice"} <= set(props)


def test_p2_chart_responses_in_openapi():
    la_so = _schema("LaSoResponse")["properties"]
    assert {"pillars", "nhat_chu", "thap_than"} <= set(la_so)
    tu_tru = _schema("TuTruResponse")["properties"]
    assert {"menh", "birth_year_can_chi", "pillars"} <= set(tu_tru)
    pt = _schema("PhongThuyResponse")["properties"]
    assert {"phi_tinh", "phi_tinh_year", "huong_tot_nam_nay"} <= set(pt)


def _array_branch(prop: dict) -> dict:
    """OpenAPI for Optional[BreakdownFour] is anyOf[array, null]."""
    for branch in prop.get("anyOf", [prop]):
        if branch.get("type") == "array":
            return branch
    return prop


def test_breakdown_arrays_have_min_length_four():
    detail = _array_branch(_schema("DayDetailResponse")["properties"]["breakdown"])
    assert detail.get("minItems") == 4
    assert detail.get("maxItems") == 4
    luan = _array_branch(
        _schema("LuanContextResponse")["properties"]["breakdown_summary"]
    )
    assert luan.get("minItems") == 4


def test_luu_nien_response_openapi_rich_facts():
    props = _schema("LuuNienResponse")["properties"]
    assert {
        "quy_nhan",
        "dai_van_next",
        "life_areas",
        "month_scores",
        "month_score_values",
    } <= set(props)
    assert props["life_areas"]["minItems"] == 4
    assert props["month_scores"]["minItems"] == 12
    assert props["month_score_values"]["minItems"] == 12
    qn = _schema(props["quy_nhan"]["$ref"].split("/")[-1])["properties"]
    assert {"tuoi_hop", "tuoi_xung", "huong_quy_nhan"} <= set(qn)


def test_la_so_personality_traits_in_openapi():
    props = _schema("LaSoResponse")["properties"]
    assert "personality_traits" in props
