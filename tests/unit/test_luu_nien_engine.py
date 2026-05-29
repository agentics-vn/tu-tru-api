"""Unit tests — engine/luu_nien (bazi reading §03 & §05 facts)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from engine.luu_nien import build_luu_nien, build_quy_nhan


def test_build_luu_nien_has_four_life_areas_and_twelve_months():
    payload = build_luu_nien(
        birth_date_iso="1984-03-15",
        birth_time=8,
        gender=1,
        year=2026,
    )
    assert payload["year_can_chi"] == "Bính Ngọ"
    assert payload["year_label_vi"].startswith("Lưu niên 2026")
    assert len(payload["life_areas"]) == 4
    ids = {a["id"] for a in payload["life_areas"]}
    assert ids == {"tai_loc", "su_nghiep", "suc_khoe", "tinh_duyen"}
    for area in payload["life_areas"]:
        assert area["label_vi"]
        assert area["verdict_vi"]
        assert area["detail_vi"]
    assert len(payload["month_scores"]) == 12
    assert payload["month_scores"][0]["month"] == 1
    assert payload["month_scores"][-1]["month"] == 12
    assert len(payload["month_score_values"]) == 12
    assert payload["month_score_values"] == [r["score"] for r in payload["month_scores"]]


def test_quy_nhan_tuoi_hop_and_xung():
    # Tý (0): tam hop Thân, Thìn; luc hop Sửu; xung Ngọ
    qn = build_quy_nhan(
        user_year_chi_idx=0,
        flow_year_chi_idx=6,
        dung_than="Kim",
        year_can_chi="Bính Ngọ",
    )
    assert "Thân" in qn["tuoi_hop"]
    assert "Ngọ" in qn["tuoi_xung"]
    assert qn["huong_quy_nhan"] == "Tây"  # Kim — hướng chính, không cắt "Tây Bắc" → "Tây"
    assert qn["note_vi"]


def test_dai_van_next_present_with_gender():
    payload = build_luu_nien(
        birth_date_iso="1984-03-15",
        birth_time=8,
        gender=1,
        year=2026,
    )
    assert payload["dai_van_next"] is not None
    assert payload["dai_van_next"]["display"]
    assert payload["dai_van_next"]["theme_vi"]
    assert payload["quy_nhan"]["tuoi_hop"]
    assert payload["teaser"]["year_rating"]
