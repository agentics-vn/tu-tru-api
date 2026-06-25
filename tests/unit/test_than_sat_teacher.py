"""Unit tests: Thần sát rules vs Lý Cư Minh Tra Cứu Bát Tự lookup table."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.chart_bundle import build_full_chart
from engine.pillars import get_tu_tru
from engine.than_sat import analyze_than_sat

CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
STEM = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]

SEED = json.loads(Path("docs/seed/than-sat.json").read_text())


@pytest.mark.parametrize("stem_idx,stem", list(enumerate(STEM)))
def test_thien_loc_matches_teacher(stem_idx: int, stem: str):
    teacher = {
        0: "Dần", 1: "Mão", 2: "Tỵ", 3: "Ngọ", 4: "Tỵ", 5: "Ngọ",
        6: "Thân", 7: "Dậu", 8: "Hợi", 9: "Tý",
    }
    got = [CHI[i] for i in SEED["thien_loc_by_day_stem"][str(stem_idx)]]
    assert got == [teacher[stem_idx]]


@pytest.mark.parametrize("stem_idx,stem", list(enumerate(STEM)))
def test_thien_at_matches_teacher(stem_idx: int, stem: str):
    teacher = {
        0: ["Sửu", "Mùi"], 1: ["Tý", "Thân"], 2: ["Dậu", "Hợi"], 3: ["Dậu", "Hợi"],
        4: ["Sửu", "Mùi"], 5: ["Tý", "Thân"], 6: ["Dần", "Ngọ"], 7: ["Dần", "Ngọ"],
        8: ["Tỵ", "Mão"], 9: ["Tỵ", "Mão"],
    }
    got = [CHI[i] for i in SEED["thien_at_by_day_stem"][str(stem_idx)]]
    assert set(got) == set(teacher[stem_idx])


@pytest.mark.parametrize("stem_idx", range(10))
def test_hong_diem_matches_teacher(stem_idx: int):
    teacher = [6, 8, 2, 7, 4, 4, 10, 9, 0, 8]
    got = SEED["hong_diem_by_day_stem"][str(stem_idx)][0]
    assert got == teacher[stem_idx]


@pytest.mark.parametrize("ref_idx", range(12))
def test_hong_loan_and_thien_hi_match_teacher(ref_idx: int):
    teacher_hl = [3, 2, 1, 0, 11, 10, 9, 8, 7, 6, 5, 4]
    teacher_th = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 11, 10]
    hl = SEED["hong_loan_by_branch"][str(ref_idx)]
    assert hl == teacher_hl[ref_idx]
    assert (hl + 6) % 12 == teacher_th[ref_idx]


def test_all_teacher_branch_stars_on_synthetic_chart():
    """Year Hợi + Day Dần → exercise hong_loan, co_than, qua_tu, vong_than."""
    tu_tru = get_tu_tru("1984-02-02", 0)
    stars = analyze_than_sat(tu_tru)
    names = {pk: [s["name"] for s in stars[pk]] for pk in stars}
    assert "Hồng Loan" in names["month"]
    assert "Quả Tú" in names["month"]
    assert "Cô Thần" in names["day"]
    assert "Vong Thần" in names["day"]


def test_canh_day_master_thien_at_on_dan_ngo():
    tu_tru = get_tu_tru("1990-03-21", 6)
    tu_tru["day"]["can_idx"] = 6
    stars = analyze_than_sat(tu_tru)
    year_names = [s["name"] for s in stars["year"]]
    assert "Thiên Ất Quý Nhân" in year_names  # Ngọ
