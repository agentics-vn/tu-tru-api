"""
test_hoang_dao.py — Unit tests for Hoang Dao / Hac Dao module.

Source of truth: docs/algorithm.md §15, §16.
Run with: python3 -m pytest tests/unit/test_hoang_dao.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from engine.hoang_dao import (
    STARS_12,
    HOANG_DAO_INDICES,
    GOOD_HOURS_EVEN,
    GOOD_HOURS_ODD,
    CHI_HOUR_RANGES,
    get_day_star,
    is_hoang_dao,
    get_gio_hoang_dao,
    get_gio_hac_dao,
)


# ─────────────────────────────────────────────────────────────────────────────
# §15 — Day Star Classification
# ─────────────────────────────────────────────────────────────────────────────

class TestDayStar:

    def test_12_stars_defined(self):
        assert len(STARS_12) == 12

    def test_6_hoang_dao_indices(self):
        assert len(HOANG_DAO_INDICES) == 6
        assert HOANG_DAO_INDICES == frozenset({0, 1, 4, 5, 7, 10})

    def test_month1_day_dan_is_thanh_long(self):
        """Month 1: start = ((1-1)%6)*2 = 0. Dan(2) => star_idx = (2-0)%12 = 2 => Thien Hinh"""
        result = get_day_star(1, 2)
        assert result["star_idx"] == 2
        assert result["star_name"] == "Thiên Hình"
        assert result["is_hoang_dao"] is False

    def test_month1_day_ty_is_thanh_long(self):
        """Month 1: start = 0. Ty(0) => star_idx = 0 => Thanh Long"""
        result = get_day_star(1, 0)
        assert result["star_idx"] == 0
        assert result["star_name"] == "Thanh Long"
        assert result["is_hoang_dao"] is True

    def test_month1_day_suu_is_minh_duong(self):
        """Month 1: start=0. Suu(1) => star_idx=1 => Minh Duong (hoang dao)"""
        result = get_day_star(1, 1)
        assert result["star_idx"] == 1
        assert result["star_name"] == "Minh Đường"
        assert result["is_hoang_dao"] is True

    def test_month7_start_position(self):
        """Month 7: start = ((7-1)%6)*2 = 0. Same as month 1."""
        result7 = get_day_star(7, 0)
        result1 = get_day_star(1, 0)
        assert result7["star_idx"] == result1["star_idx"]

    def test_month2_start_position(self):
        """Month 2: start = ((2-1)%6)*2 = 2. Day Chi=Dan(2) => star_idx=(2-2)%12=0 => Thanh Long"""
        result = get_day_star(2, 2)
        assert result["star_idx"] == 0
        assert result["star_name"] == "Thanh Long"

    def test_month3_start_position(self):
        """Month 3: start = ((3-1)%6)*2 = 4. Day Chi=Thin(4) => star_idx=(4-4)%12=0 => Thanh Long"""
        result = get_day_star(3, 4)
        assert result["star_idx"] == 0
        assert result["star_name"] == "Thanh Long"

    def test_is_hoang_dao_matches_get_day_star(self):
        """is_hoang_dao must match get_day_star result."""
        for lm in range(1, 13):
            for dci in range(12):
                star = get_day_star(lm, dci)
                assert is_hoang_dao(lm, dci) == star["is_hoang_dao"]

    def test_star_type_matches_hoang_dao_flag(self):
        """star_type must match is_hoang_dao flag."""
        for lm in range(1, 13):
            for dci in range(12):
                star = get_day_star(lm, dci)
                if star["is_hoang_dao"]:
                    assert star["star_type"] == "hoang_dao"
                else:
                    assert star["star_type"] == "hac_dao"

    def test_each_month_has_6_hoang_dao_days(self):
        """Each lunar month should have exactly 6 hoang dao out of 12 chi."""
        for lm in range(1, 13):
            count = sum(1 for dci in range(12) if is_hoang_dao(lm, dci))
            assert count == 6, f"Month {lm} has {count} hoang dao days, expected 6"


# ─────────────────────────────────────────────────────────────────────────────
# §16 — Gio Hoang Dao
# ─────────────────────────────────────────────────────────────────────────────

class TestGioHoangDao:

    def test_12_chi_hour_ranges(self):
        assert len(CHI_HOUR_RANGES) == 12

    def test_even_day_6_good_hours(self):
        """Even day chi (e.g. Ty=0) => 6 good hours."""
        gio = get_gio_hoang_dao(0)  # Ty is even
        assert len(gio) == 6

    def test_odd_day_6_good_hours(self):
        """Odd day chi (e.g. Suu=1) => 6 good hours."""
        gio = get_gio_hoang_dao(1)  # Suu is odd
        assert len(gio) == 6

    def test_even_day_good_set(self):
        """Even day chi => good hours are {Ty, Suu, Thin, Ty, Mui, Tuat}"""
        gio = get_gio_hoang_dao(0)
        chi_indices = {h["chi_idx"] for h in gio}
        assert chi_indices == GOOD_HOURS_EVEN

    def test_odd_day_good_set(self):
        """Odd day chi => good hours are {Dan, Mao, Ty, Ngo, Than, Hoi}"""
        gio = get_gio_hoang_dao(1)
        chi_indices = {h["chi_idx"] for h in gio}
        assert chi_indices == GOOD_HOURS_ODD

    def test_even_day_hac_dao_complement(self):
        """Hac dao hours complement hoang dao hours."""
        good = get_gio_hoang_dao(0)
        bad = get_gio_hac_dao(0)
        good_set = {h["chi_idx"] for h in good}
        bad_set = {h["chi_idx"] for h in bad}
        assert len(good_set & bad_set) == 0  # No overlap
        assert good_set | bad_set == set(range(12))  # Cover all 12

    def test_odd_day_hac_dao_complement(self):
        good = get_gio_hoang_dao(1)
        bad = get_gio_hac_dao(1)
        good_set = {h["chi_idx"] for h in good}
        bad_set = {h["chi_idx"] for h in bad}
        assert len(good_set & bad_set) == 0
        assert good_set | bad_set == set(range(12))

    def test_gio_has_correct_keys(self):
        gio = get_gio_hoang_dao(0)
        for h in gio:
            assert "chi_idx" in h
            assert "chi_name" in h
            assert "start" in h
            assert "end" in h

    def test_all_12_chi_get_6_good_6_bad(self):
        for chi_idx in range(12):
            good = get_gio_hoang_dao(chi_idx)
            bad = get_gio_hac_dao(chi_idx)
            assert len(good) == 6, f"Chi {chi_idx}: expected 6 good, got {len(good)}"
            assert len(bad) == 6, f"Chi {chi_idx}: expected 6 bad, got {len(bad)}"
