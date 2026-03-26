"""Unit tests for engine.hop_tuoi (v2 compatibility)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from engine.hop_tuoi import (
    CRITERIA_BY_RELATIONSHIP,
    RELATIONSHIP_TYPES,
    analyze_compatibility,
    compute_verdict,
    evaluate_criterion,
    sentiment_score,
    year_luc_hop,
    year_tam_hop,
)


def _p(
    hanh: str,
    yc: int,
    dc: int,
    nhat: str,
    tu_tru: dict | None = None,
    gender: int | None = None,
) -> dict:
    return {
        "hanh": hanh,
        "year_chi_idx": yc,
        "day_can_idx": dc,
        "nhat_chu_hanh": nhat,
        "tu_tru": tu_tru,
        "birth_date": "1990-01-01",
        "menh": "X",
        "nhatChu": "X",
        "gender": gender,
    }


class TestRegistry:
    def test_eight_relationships(self):
        assert len(RELATIONSHIP_TYPES) == 8
        assert len(CRITERIA_BY_RELATIONSHIP) == 8
        assert set(RELATIONSHIP_TYPES) == set(CRITERIA_BY_RELATIONSHIP)

    def test_weights_align_with_criteria_count(self):
        for rel, specs in CRITERIA_BY_RELATIONSHIP.items():
            assert all("key" in s and "weight" in s for s in specs)
            assert all(s["weight"] > 0 for s in specs)


class TestYearHarmony:
    def test_luc_hop_ty_suu(self):
        assert year_luc_hop(0, 1) and year_luc_hop(1, 0)

    def test_tam_hop_dan_ngo_tuat(self):
        assert year_tam_hop(2, 6) and year_tam_hop(6, 10)


class TestComputeVerdict:
    def test_all_positive_high_level(self):
        crit = [{"sentiment": "positive"}] * 3
        w = [1, 1, 1]
        v, lv = compute_verdict(crit, w)
        assert lv == 1
        assert v == "Rất tương hợp"

    def test_all_negative_low_level(self):
        crit = [{"sentiment": "negative"}] * 4
        w = [2, 2, 2, 2]
        v, lv = compute_verdict(crit, w)
        assert lv == 4
        assert v == "Nhiều thử thách"

    def test_mixed_threshold(self):
        crit = [
            {"sentiment": "positive"},
            {"sentiment": "neutral"},
            {"sentiment": "negative"},
        ]
        w = [1, 1, 1]
        _, lv = compute_verdict(crit, w)
        assert lv in (2, 3)


class TestPhuTheGioiTinh:
    def test_missing_gender_neutral(self):
        p1 = _p("Kim", 0, 0, "Kim")
        p2 = _p("Kim", 1, 0, "Kim")
        r = evaluate_criterion("phu_the_gioi_tinh", p1, p2, "PHU_THE")
        assert r["sentiment"] == "neutral"
        assert "Chưa có đủ" in r["description"]

    def test_opposite_gender_positive(self):
        p1 = _p("Kim", 0, 0, "Kim", gender=1)
        p2 = _p("Kim", 1, 0, "Kim", gender=-1)
        r = evaluate_criterion("phu_the_gioi_tinh", p1, p2, "PHU_THE")
        assert r["sentiment"] == "positive"

    def test_same_gender_neutral(self):
        p1 = _p("Kim", 0, 0, "Kim", gender=1)
        p2 = _p("Kim", 1, 0, "Kim", gender=1)
        r = evaluate_criterion("phu_the_gioi_tinh", p1, p2, "PHU_THE")
        assert r["sentiment"] == "neutral"
        assert "cùng mã giới" in r["description"]


class TestEvaluateNapAm:
    def test_symmetric_sinh(self):
        p1 = _p("Kim", 8, 0, "Kim")
        p2 = _p("Thủy", 8, 0, "Thủy")
        r = evaluate_criterion("nap_am", p1, p2, "BAN_BE")
        assert r["sentiment"] == "positive"

    def test_dia_chi_xung(self):
        p1 = _p("Kim", 0, 0, "Kim")
        p2 = _p("Kim", 6, 0, "Kim")
        r = evaluate_criterion("dia_chi_xung", p1, p2, "ANH_CHI_EM")
        assert r["sentiment"] == "negative"


class TestAnalyzeCompatibility:
    def test_returns_structure(self):
        p1 = _p("Thổ", 5, 4, "Hỏa")
        p2 = _p("Kim", 9, 5, "Kim")
        out = analyze_compatibility(p1, p2, "DOI_TAC")
        assert out["verdict_level"] in (1, 2, 3, 4)
        assert "criteria" in out and len(out["criteria"]) == len(CRITERIA_BY_RELATIONSHIP["DOI_TAC"])
        assert out["reading"]
        assert out["advice"]

    def test_invalid_relationship_raises(self):
        p1 = _p("Kim", 0, 0, "Kim")
        p2 = _p("Kim", 1, 1, "Kim")
        with pytest.raises(ValueError):
            analyze_compatibility(p1, p2, "INVALID")


class TestSentimentScore:
    def test_map(self):
        assert sentiment_score("positive") == 1
        assert sentiment_score("neutral") == 0
        assert sentiment_score("negative") == -1
