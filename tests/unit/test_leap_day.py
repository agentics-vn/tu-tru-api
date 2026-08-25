"""
Gregorian leap-day natal dates (29/02).

People born on 29 February must keep that civil day as the day pillar.
Projecting the birthday onto a non-leap year (lưu niên / view_year) must
not construct date(year, 2, 29) and must not rewrite the natal day to 28/02.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from engine.bazi_solar import bazi_cycle_year
from engine.can_chi import get_can_chi_day
from engine.chart_bundle import build_full_chart
from engine.luu_nien_list import build_luu_nien_list
from engine.pillars import get_tu_tru


LEAP_BIRTH_YEARS = (1988, 1992, 1996, 2000, 2004, 2024)


class TestBaziCycleYearLeapDay:
    def test_leap_year_uses_real_feb_29(self):
        assert bazi_cycle_year(2000, 2, 29) == 2000

    def test_non_leap_projection_does_not_raise(self):
        assert bazi_cycle_year(2026, 2, 29) == 2026
        assert bazi_cycle_year(2001, 2, 29) == 2001

    def test_invalid_day_still_raises(self):
        with pytest.raises(ValueError, match="day is out of range"):
            bazi_cycle_year(2000, 2, 30)


class TestNatalDayPillarUnchanged:
    def test_feb_29_differs_from_feb_28(self):
        d28 = get_can_chi_day(2000, 2, 28)
        d29 = get_can_chi_day(2000, 2, 29)
        assert (d28["can_idx"], d28["chi_idx"]) != (d29["can_idx"], d29["chi_idx"])
        assert f"{d29['can_name']} {d29['chi_name']}" == "Đinh Tỵ"

        tu28 = get_tu_tru("2000-02-28", 6)
        tu29 = get_tu_tru("2000-02-29", 6)
        assert (tu28["day"]["can_idx"], tu28["day"]["chi_idx"]) != (
            tu29["day"]["can_idx"], tu29["day"]["chi_idx"],
        )
        assert tu29["display"] == "Canh Thìn | Mậu Dần | Đinh Tỵ | Quý Mão"

    @pytest.mark.parametrize("year", LEAP_BIRTH_YEARS)
    def test_get_tu_tru_accepts_leap_day(self, year: int):
        tu = get_tu_tru(f"{year}-02-29", 6)
        assert tu["day"]["can_name"]
        assert tu["day"]["chi_name"]


class TestLuuNienLeapDayProjection:
    @pytest.mark.parametrize("year", LEAP_BIRTH_YEARS)
    def test_list_from_birth_year(self, year: int):
        rows = build_luu_nien_list(f"{year}-02-29", num_years=10)
        assert len(rows) == 10
        assert rows[0]["year"] == year
        assert rows[1]["year"] == year + 1

    def test_list_from_non_leap_view_year(self):
        rows = build_luu_nien_list("2000-02-29", num_years=10, start_year=2026)
        assert [r["year"] for r in rows] == list(range(2026, 2036))
        assert rows[0]["display"] == "Bính Ngọ"


class TestFullChartLeapDay:
    @pytest.mark.parametrize("year", LEAP_BIRTH_YEARS)
    def test_build_full_chart(self, year: int):
        tu = get_tu_tru(f"{year}-02-29", 6)
        chart = build_full_chart(
            tu, f"{year}-02-29", gender=1, birth_time_slot=6, view_year=2026,
        )
        assert chart["header"]["duong_lich"] == f"{year}-02-29"
        assert "29/2/" in chart["header"]["duong_lich_display"]
        assert chart["pillars"]["day"]["display"] == (
            f"{tu['day']['can_name']} {tu['day']['chi_name']}"
        )
        assert len(chart["luu_nien"]) == 10
        assert chart["luu_nien"][0]["year"] == 2026
