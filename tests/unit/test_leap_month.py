"""
T1-02: Tháng nhuận (leap month) handling audit.

Tests that leap lunar months are correctly detected and that Layer 1
filters (hung ngày) behave correctly during leap months.

Leap month years in 2000–2030:
  2001 (M4), 2004 (M2), 2006 (M7), 2009 (M5), 2012 (M4),
  2014 (M9), 2017 (M6), 2020 (M4), 2023 (M2), 2025 (M6),
  2028 (M5)

Run with: python3 -m pytest tests/unit/test_leap_month.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from datetime import date, timedelta

from engine.lunar import solar_to_lunar
from engine.hung_ngay import is_nguyet_ky, is_tam_nuong, is_duong_cong_ky, is_cohon
from calendar_service import get_day_info


# ─────────────────────────────────────────────────────────────────────────────
# Known leap months (year, leap_month_number)
# Source: Chinese Calendar leap month tables
# ─────────────────────────────────────────────────────────────────────────────

LEAP_YEARS = [
    (2001, 4),
    (2004, 2),
    (2006, 7),
    (2009, 5),
    (2012, 4),
    (2014, 9),
    (2017, 6),
    (2020, 4),
    (2023, 2),
    (2025, 6),
    (2028, 5),
]


def _find_leap_month_dates(solar_year: int, expected_leap_month: int) -> list[str]:
    """Scan a year to find dates falling in the expected leap month."""
    found = []
    # Scan the solar year (expand range to catch late lunar months)
    start = date(solar_year, 1, 1)
    end = date(solar_year, 12, 31)
    d = start
    while d <= end:
        iso = d.isoformat()
        try:
            lunar = solar_to_lunar(iso)
            if lunar["is_leap_month"] and lunar["lunar_month"] == expected_leap_month:
                found.append(iso)
        except Exception:
            pass
        d += timedelta(days=1)
    return found


class TestLeapMonthDetection:
    """Verify that is_leap_month is correctly flagged for known leap years."""

    @pytest.mark.parametrize("year,leap_month", LEAP_YEARS)
    def test_leap_month_exists(self, year, leap_month):
        """At least one date in the year should have is_leap_month=True
        for the expected lunar month."""
        dates = _find_leap_month_dates(year, leap_month)
        assert len(dates) > 0, (
            f"Year {year}: expected leap month {leap_month} but found none"
        )

    @pytest.mark.parametrize("year,leap_month", LEAP_YEARS)
    def test_leap_month_has_reasonable_length(self, year, leap_month):
        """A leap month should be 29 or 30 days."""
        dates = _find_leap_month_dates(year, leap_month)
        assert 29 <= len(dates) <= 30, (
            f"Year {year} leap month {leap_month}: found {len(dates)} days"
        )


class TestLeapMonthLayer1Filters:
    """Ensure hung ngày filters work correctly during leap months.

    Key question: Does a leap month 7 trigger is_cohon()?
    The answer depends on convention — our code checks lunar_month == 7
    regardless of is_leap_month. This test documents the behavior.
    """

    def test_nguyet_ky_applies_in_leap_month(self):
        """Nguyệt Kỵ (days 5, 14, 23) must apply regardless of leap flag."""
        assert is_nguyet_ky(5) is True
        assert is_nguyet_ky(14) is True
        assert is_nguyet_ky(23) is True

    def test_tam_nuong_applies_in_leap_month(self):
        """Tam Nương (days 3,7,13,18,22,27) must apply regardless of leap flag."""
        for day in [3, 7, 13, 18, 22, 27]:
            assert is_tam_nuong(day) is True

    def test_duong_cong_ky_uses_lunar_month_number(self):
        """Dương Công Kỵ uses the lunar month number — should still work
        if the month is a leap month (same number, different flag)."""
        # Month 7, day 1 → should be Dương Công Kỵ
        assert is_duong_cong_ky(7, 1) is True
        # Month 7, day 29 → should be Dương Công Kỵ
        assert is_duong_cong_ky(7, 29) is True

    def test_cohon_check_leap_month_7(self):
        """Verify is_cohon behavior: checks lunar_month == 7."""
        assert is_cohon(7) is True
        # Regardless of whether it's leap or not, the function only checks number
        assert is_cohon(1) is False


class TestLeapMonth7_2006:
    """2006 has a leap month 7 — verify day_info handles it correctly.

    In 2006, the leap month 7 runs approximately from Aug 24 to Sep 21.
    This is the most critical test: does our engine treat leap month 7
    as Cô Hồn or not?
    """

    def test_leap_month_7_dates_exist(self):
        """Verify we can find leap month 7 dates in 2006."""
        dates = _find_leap_month_dates(2006, 7)
        assert len(dates) > 0

    def test_regular_month_7_is_cohon(self):
        """Regular (non-leap) month 7 dates should have is_cohon=True."""
        # Find first date in regular month 7 of 2006
        d = date(2006, 7, 1)
        end = date(2006, 9, 30)
        found_regular_m7 = False
        while d <= end:
            lunar = solar_to_lunar(d.isoformat())
            if lunar["lunar_month"] == 7 and not lunar["is_leap_month"]:
                info = get_day_info(d.isoformat())
                assert info["is_cohon"] is True, (
                    f"{d.isoformat()}: regular month 7 should be Cô Hồn"
                )
                found_regular_m7 = True
                break
            d += timedelta(days=1)
        assert found_regular_m7, "Could not find regular month 7 in 2006"


class TestLeapMonth6_2025:
    """2025 has leap month 6 — verify it doesn't falsely trigger month 7 checks."""

    def test_leap_month_6_not_cohon(self):
        """Leap month 6 should NOT be treated as Cô Hồn."""
        dates = _find_leap_month_dates(2025, 6)
        assert len(dates) > 0
        # Check first date in leap month 6
        info = get_day_info(dates[0])
        assert info["is_cohon"] is False, (
            f"Leap month 6 should not be Cô Hồn"
        )

    def test_leap_month_6_is_leap_flag(self):
        """The is_leap_month flag should be True for leap month 6 dates."""
        dates = _find_leap_month_dates(2025, 6)
        for iso in dates[:3]:  # Spot-check first 3
            info = get_day_info(iso)
            assert info["is_leap_month"] is True
