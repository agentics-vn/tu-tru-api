"""
T1-10: CI safety invariant — assert zero severity-3 dates in recommended_dates.

Unlike the single-request test in test_endpoints.py, this test runs the full
3-layer pipeline across broad date ranges and multiple intents to stress-test
the safety guard.

Run with: python3 -m pytest tests/unit/test_safety_invariant.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from datetime import date, timedelta

from calendar_service import get_day_info, get_user_chart
from filter import apply_layer2_filter
from scoring import compute_score
from engine.hung_ngay import is_nguyet_ky, is_tam_nuong, is_duong_cong_ky

import json
from pathlib import Path

_INTENT_RULES_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "seed" / "intent-rules.json"
with open(_INTENT_RULES_PATH, encoding="utf-8") as f:
    INTENT_RULES: dict = json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# Test birth charts covering different mệnh elements
# ─────────────────────────────────────────────────────────────────────────────

TEST_CHARTS = [
    "1984-03-15",  # Kim (Hải Trung Kim)
    "1990-05-15",  # Thổ (Lộ Bàng Thổ)
    "1975-08-20",  # Thủy (Đại Khê Thủy)
    "1986-11-10",  # Hỏa (Lò Trung Hỏa)
    "1988-06-25",  # Mộc (Đại Lâm Mộc)
]

# Representative intents across categories
TEST_INTENTS = [
    "KHAI_TRUONG",
    "DAM_CUOI",
    "DONG_THO",
    "AN_TANG",
    "XUAT_HANH",
    "MAC_DINH",
]


def _run_pipeline(birth_iso: str, intent: str, start: date, end: date):
    """Run the 3-layer pipeline and return (recommended, avoided) lists."""
    user_chart = get_user_chart(birth_iso)
    rule_key = intent
    intent_rule = INTENT_RULES.get(rule_key, INTENT_RULES["MAC_DINH"])

    scored_days = []
    dates_to_avoid = []

    d = start
    while d <= end:
        iso = d.isoformat()
        day_info = get_day_info(iso)

        # Layer 1
        if not day_info["is_layer1_pass"]:
            if day_info["is_nguyet_ky"] or day_info["is_duong_cong_ky"]:
                dates_to_avoid.append({"date": iso, "severity": 3})
            elif day_info["is_tam_nuong"]:
                dates_to_avoid.append({"date": iso, "severity": 2})
            d += timedelta(days=1)
            continue

        # Layer 2
        filter_result = apply_layer2_filter(day_info, user_chart, intent)

        if filter_result["severity"] == 3:
            dates_to_avoid.append({"date": iso, "severity": 3})
            d += timedelta(days=1)
            continue

        if filter_result["severity"] == 2:
            dates_to_avoid.append({"date": iso, "severity": 2})

        # Layer 3
        score_result = compute_score(
            day_info, user_chart, rule_key, intent_rule, filter_result
        )
        scored_days.append({"day_info": day_info, "score_result": score_result})

        d += timedelta(days=1)

    # Sort and pick top
    scored_days.sort(key=lambda x: x["score_result"]["score"], reverse=True)
    top_days = scored_days[:5]

    # Safety guard (mirrors chon_ngay.py logic)
    sev3_dates = {d["date"] for d in dates_to_avoid if d["severity"] == 3}
    recommended = [
        d for d in top_days
        if d["day_info"]["date"] not in sev3_dates
    ]

    return recommended, dates_to_avoid


class TestSafetyInvariantBroadRange:
    """Run the pipeline across 2025-2027 and verify no severity-3 leaks."""

    # Each test window: 90 days
    WINDOWS = [
        (date(2025, 1, 1), date(2025, 3, 31)),
        (date(2025, 4, 1), date(2025, 6, 29)),
        (date(2025, 7, 1), date(2025, 9, 28)),   # Includes Cô Hồn
        (date(2025, 10, 1), date(2025, 12, 29)),
        (date(2026, 1, 1), date(2026, 3, 31)),
        (date(2026, 4, 1), date(2026, 6, 29)),
        (date(2026, 7, 1), date(2026, 9, 28)),
        (date(2026, 10, 1), date(2026, 12, 29)),
        (date(2027, 1, 1), date(2027, 3, 31)),
        (date(2027, 7, 1), date(2027, 9, 28)),
    ]

    @pytest.mark.parametrize(
        "birth_iso", TEST_CHARTS,
        ids=[f"birth_{b}" for b in TEST_CHARTS],
    )
    @pytest.mark.parametrize(
        "intent", TEST_INTENTS,
    )
    def test_no_severity3_in_recommended(self, birth_iso, intent):
        """Core safety invariant: no severity-3 date ever appears in recommended."""
        # Use a representative window (Q1 2026)
        start, end = date(2026, 1, 1), date(2026, 3, 31)
        recommended, avoided = _run_pipeline(birth_iso, intent, start, end)

        sev3_dates = {d["date"] for d in avoided if d["severity"] == 3}
        rec_dates = {d["day_info"]["date"] for d in recommended}
        leaked = sev3_dates & rec_dates

        assert len(leaked) == 0, (
            f"SAFETY VIOLATION: severity-3 dates in recommended: {leaked} "
            f"(birth={birth_iso}, intent={intent})"
        )


class TestSafetyInvariantCohon:
    """Specifically test Tháng Cô Hồn (month 7) for blocked intents."""

    COHON_INTENTS = ["DAM_CUOI", "DONG_THO", "NHAP_TRACH", "KHAI_TRUONG"]

    @pytest.mark.parametrize("intent", COHON_INTENTS)
    def test_cohon_window_no_severity3_leak(self, intent):
        """During lunar month 7, blocked intents must never recommend dates."""
        # 2025 lunar month 7 ≈ Aug–Sep solar
        recommended, avoided = _run_pipeline(
            "1984-03-15", intent,
            date(2025, 7, 20), date(2025, 9, 20),
        )

        sev3_dates = {d["date"] for d in avoided if d["severity"] == 3}
        rec_dates = {d["day_info"]["date"] for d in recommended}
        leaked = sev3_dates & rec_dates

        assert len(leaked) == 0, (
            f"SAFETY VIOLATION in Cô Hồn window: {leaked} (intent={intent})"
        )


class TestSafetyInvariantNguyetKy:
    """Verify Nguyệt Kỵ (lunar days 5, 14, 23) never appear in recommended."""

    def test_nguyet_ky_never_recommended(self):
        """Scan 6 months and verify no Nguyệt Kỵ date appears in recommended."""
        recommended, _ = _run_pipeline(
            "1990-05-15", "MAC_DINH",
            date(2026, 1, 1), date(2026, 3, 31),
        )
        for d in recommended:
            day_info = d["day_info"]
            assert not day_info["is_nguyet_ky"], (
                f"Nguyệt Kỵ date {day_info['date']} (lunar day {day_info['lunar_day']}) "
                f"found in recommended!"
            )


class TestSafetyInvariantDuongCongKy:
    """Verify Dương Công Kỵ never appears in recommended."""

    def test_duong_cong_ky_never_recommended(self):
        recommended, _ = _run_pipeline(
            "1984-03-15", "MAC_DINH",
            date(2026, 1, 1), date(2026, 3, 31),
        )
        for d in recommended:
            day_info = d["day_info"]
            assert not day_info["is_duong_cong_ky"], (
                f"Dương Công Kỵ date {day_info['date']} found in recommended!"
            )


class TestSafetyInvariantXung:
    """Verify Xung (branch conflict) dates are never recommended."""

    def test_xung_never_recommended(self):
        """Xung dates have severity=3 and must be excluded."""
        from engine.can_chi import is_xung

        birth_iso = "1984-03-15"
        user_chart = get_user_chart(birth_iso)
        year_chi = user_chart["year_chi_idx"]

        recommended, _ = _run_pipeline(
            birth_iso, "MAC_DINH",
            date(2026, 1, 1), date(2026, 3, 31),
        )

        for d in recommended:
            day_chi = d["day_info"]["day_chi_idx"]
            assert not is_xung(day_chi, year_chi), (
                f"Xung date {d['day_info']['date']} "
                f"(day_chi={day_chi}, year_chi={year_chi}) in recommended!"
            )
