"""
test_engine.py — Unit tests for the Python engine port.

Vectors ported 1:1 from src/calendar-service.test.js.
Run with: python3 -m pytest tests/unit/test_engine.py -v
"""

import sys
import os

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from engine.can_chi import (
    get_can_chi_day,
    get_can_chi_year,
    get_menh_nap_am,
    get_nap_am_pair_idx,
    is_can_khac,
    is_xung,
)
from engine.truc import get_truc_idx, TRUC_NAMES, TRUC_SCORES
from engine.sao_ngay import (
    check_thien_duc,
    check_thien_duc_hop,
    check_nguyet_duc,
    check_nguyet_duc_hop,
)
from engine.hung_ngay import is_nguyet_ky, is_tam_nuong, is_duong_cong_ky, is_cohon
from engine.lunar import solar_to_lunar
from calendar_service import get_day_info, get_user_chart, get_month_info


# ─────────────────────────────────────────────────────────────────────────────
# 1. getCanChiDay — anchored at 1900-01-31 = Giap Ty
# ─────────────────────────────────────────────────────────────────────────────

class TestGetCanChiDay:

    @staticmethod
    def _cc_day(y, m, d) -> str:
        r = get_can_chi_day(y, m, d)
        return f"{r['can_name']} {r['chi_name']}"

    def test_anchor_1900_01_31(self):
        assert self._cc_day(1900, 1, 31) == "Giáp Tý"

    def test_2000_01_01(self):
        assert self._cc_day(2000, 1, 1) == "Mậu Dần"

    def test_2024_01_01(self):
        assert self._cc_day(2024, 1, 1) == "Giáp Thân"

    def test_2024_02_10_tet(self):
        assert self._cc_day(2024, 2, 10) == "Giáp Tý"

    def test_2025_01_29_tet(self):
        assert self._cc_day(2025, 1, 29) == "Mậu Ngọ"

    def test_2026_01_17_tet(self):
        assert self._cc_day(2026, 1, 17) == "Tân Hợi"

    def test_2026_03_11(self):
        # JS test had "Mậu Dần" but JDN math gives Giáp Thìn
        # (offset=46060, can=0→Giáp, chi=4→Thìn). All other 6 vectors match.
        assert self._cc_day(2026, 3, 11) == "Giáp Thìn"

    def test_returns_all_keys(self):
        r = get_can_chi_day(2026, 3, 11)
        assert set(r.keys()) == {
            "can_idx", "chi_idx", "can_name", "chi_name", "can_hanh", "chi_hanh"
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. getCanChiYear
# ─────────────────────────────────────────────────────────────────────────────

class TestGetCanChiYear:

    @staticmethod
    def _cc_year(y) -> str:
        r = get_can_chi_year(y)
        return f"{r['can_name']} {r['chi_name']}"

    def test_1900(self):
        assert self._cc_year(1900) == "Canh Tý"

    def test_1984(self):
        assert self._cc_year(1984) == "Giáp Tý"

    def test_1990(self):
        assert self._cc_year(1990) == "Canh Ngọ"

    def test_2024(self):
        assert self._cc_year(2024) == "Giáp Thìn"

    def test_2025(self):
        assert self._cc_year(2025) == "Ất Tỵ"

    def test_2026(self):
        assert self._cc_year(2026) == "Bính Ngọ"


# ─────────────────────────────────────────────────────────────────────────────
# 3. getMenhNapAm
# ─────────────────────────────────────────────────────────────────────────────

class TestGetMenhNapAm:

    def test_1984_hanh(self):
        assert get_menh_nap_am(1984)["hanh"] == "Kim"

    def test_1984_name(self):
        assert get_menh_nap_am(1984)["name"] == "Hải Trung Kim"

    def test_1985_hanh(self):
        assert get_menh_nap_am(1985)["hanh"] == "Kim"

    def test_1986_hanh(self):
        assert get_menh_nap_am(1986)["hanh"] == "Hỏa"

    def test_1986_name(self):
        assert get_menh_nap_am(1986)["name"] == "Lò Trung Hỏa"

    def test_1990_hanh(self):
        assert get_menh_nap_am(1990)["hanh"] == "Thổ"

    def test_1990_name(self):
        assert get_menh_nap_am(1990)["name"] == "Lộ Bàng Thổ"

    def test_1975_hanh(self):
        assert get_menh_nap_am(1975)["hanh"] == "Thủy"

    def test_1975_name(self):
        assert get_menh_nap_am(1975)["name"] == "Đại Khê Thủy"

    def test_2024_hanh(self):
        assert get_menh_nap_am(2024)["hanh"] == "Hỏa"

    def test_2024_name(self):
        assert get_menh_nap_am(2024)["name"] == "Phú Đăng Hỏa"

    def test_2026_hanh(self):
        assert get_menh_nap_am(2026)["hanh"] == "Thủy"

    def test_2026_name(self):
        assert get_menh_nap_am(2026)["name"] == "Thiên Hà Thủy"

    # Duong Than / Ky Than
    def test_1984_duong_than(self):
        assert get_menh_nap_am(1984)["duong_than"] == "Thổ"

    def test_1984_ky_than(self):
        assert get_menh_nap_am(1984)["ky_than"] == "Hỏa"

    def test_2026_duong_than(self):
        assert get_menh_nap_am(2026)["duong_than"] == "Kim"

    def test_2026_ky_than(self):
        assert get_menh_nap_am(2026)["ky_than"] == "Thổ"


# ─────────────────────────────────────────────────────────────────────────────
# 4. 12 Truc
# ─────────────────────────────────────────────────────────────────────────────

class TestGetTrucIdx:

    def test_month1_chi_dan_kien(self):
        """Thang 1, ngay Dan -> Kien(0)"""
        assert get_truc_idx(2, 1) == 0

    def test_month1_chi_thin_man(self):
        """Thang 1, ngay Thin -> Man(2)"""
        assert get_truc_idx(4, 1) == 2

    def test_month1_chi_than_pha(self):
        """Thang 1, ngay Than -> Pha(6)"""
        assert get_truc_idx(8, 1) == 6

    def test_month1_chi_dau_nguy(self):
        """Thang 1, ngay Dau -> Nguy(7)"""
        assert get_truc_idx(9, 1) == 7

    def test_month7_chi_than_kien(self):
        """Thang 7, ngay Than -> Kien(0)"""
        assert get_truc_idx(8, 7) == 0

    def test_month11_chi_ty_kien(self):
        """Thang 11, ngay Ty -> Kien(0)"""
        assert get_truc_idx(0, 11) == 0

    def test_truc_scores_correct_count(self):
        assert len(TRUC_SCORES) == 12

    def test_truc_names_correct_count(self):
        assert len(TRUC_NAMES) == 12


# ─────────────────────────────────────────────────────────────────────────────
# 5. Thien Duc & Thien Duc Hop
# ─────────────────────────────────────────────────────────────────────────────

class TestThienDuc:

    def test_month1_can_dinh(self):
        assert check_thien_duc(1, 3, 0) is True

    def test_month1_can_giap_no(self):
        assert check_thien_duc(1, 0, 0) is False

    def test_month2_chi_than(self):
        # Month 2: chi idx = 8 (Thân), not 7 (Mùi) — fixed per sao-ngay.json
        assert check_thien_duc(2, 0, 8) is True

    def test_month2_chi_dan_no(self):
        assert check_thien_duc(2, 0, 2) is False

    def test_month5_chi_hoi(self):
        assert check_thien_duc(5, 0, 11) is True

    def test_month6_can_giap(self):
        assert check_thien_duc(6, 0, 0) is True

    def test_month9_can_binh(self):
        assert check_thien_duc(9, 2, 0) is True

    def test_month12_can_canh(self):
        assert check_thien_duc(12, 6, 0) is True


class TestThienDucHop:

    def test_month1_can_nham(self):
        assert check_thien_duc_hop(1, 8) is True

    def test_month1_can_giap_no(self):
        assert check_thien_duc_hop(1, 0) is False

    def test_month2_tu_trong_no(self):
        assert check_thien_duc_hop(2, 0) is False

    def test_month5_tu_trong_no(self):
        assert check_thien_duc_hop(5, 0) is False

    def test_month8_tu_trong_no(self):
        assert check_thien_duc_hop(8, 0) is False

    def test_month11_tu_trong_no(self):
        assert check_thien_duc_hop(11, 0) is False


# ─────────────────────────────────────────────────────────────────────────────
# 6. Nguyet Duc & Hop
# ─────────────────────────────────────────────────────────────────────────────

class TestNguyetDuc:

    def test_month1_binh(self):
        assert check_nguyet_duc(1, 2) is True

    def test_month5_binh(self):
        assert check_nguyet_duc(5, 2) is True

    def test_month9_binh(self):
        assert check_nguyet_duc(9, 2) is True

    def test_month3_nham(self):
        assert check_nguyet_duc(3, 8) is True

    def test_month7_nham(self):
        assert check_nguyet_duc(7, 8) is True

    def test_month2_giap(self):
        assert check_nguyet_duc(2, 0) is True

    def test_month4_canh(self):
        assert check_nguyet_duc(4, 6) is True

    def test_month4_giap_no(self):
        assert check_nguyet_duc(4, 0) is False


class TestNguyetDucHop:

    def test_month1_tan(self):
        assert check_nguyet_duc_hop(1, 7) is True

    def test_month7_dinh(self):
        assert check_nguyet_duc_hop(7, 3) is True

    def test_month6_ky(self):
        assert check_nguyet_duc_hop(6, 5) is True

    def test_month12_at(self):
        assert check_nguyet_duc_hop(12, 1) is True


# ─────────────────────────────────────────────────────────────────────────────
# 7. Hung Ngay
# ─────────────────────────────────────────────────────────────────────────────

class TestNguyetKy:

    def test_day5(self):
        assert is_nguyet_ky(5) is True

    def test_day14(self):
        assert is_nguyet_ky(14) is True

    def test_day23(self):
        assert is_nguyet_ky(23) is True

    def test_day1_no(self):
        assert is_nguyet_ky(1) is False

    def test_day15_no(self):
        assert is_nguyet_ky(15) is False


class TestTamNuong:

    @pytest.mark.parametrize("day", [3, 7, 13, 18, 22, 27])
    def test_tam_nuong_days(self, day):
        assert is_tam_nuong(day) is True

    @pytest.mark.parametrize("day", [1, 5, 10, 20, 28])
    def test_not_tam_nuong_days(self, day):
        assert is_tam_nuong(day) is False


class TestDuongCongKy:

    def test_month1_day13(self):
        assert is_duong_cong_ky(1, 13) is True

    def test_month7_day1(self):
        # Month 7: day 1 (not 8) — fixed per hung-ngay.json and algorithm.md §5
        assert is_duong_cong_ky(7, 1) is True

    def test_month7_day29(self):
        assert is_duong_cong_ky(7, 29) is True

    def test_month7_day15_no(self):
        assert is_duong_cong_ky(7, 15) is False

    def test_month12_day19(self):
        assert is_duong_cong_ky(12, 19) is True

    def test_month12_day18_no(self):
        assert is_duong_cong_ky(12, 18) is False


class TestCohon:

    def test_month7_cohon(self):
        assert is_cohon(7) is True

    def test_month1_no_cohon(self):
        assert is_cohon(1) is False


# ─────────────────────────────────────────────────────────────────────────────
# 8. isXung & isCanKhac
# ─────────────────────────────────────────────────────────────────────────────

class TestIsXung:

    @pytest.mark.parametrize("a,b", [(0, 6), (1, 7), (2, 8), (3, 9), (4, 10), (5, 11)])
    def test_xung_pairs(self, a, b):
        assert is_xung(a, b) is True

    def test_no_xung_01(self):
        assert is_xung(0, 1) is False

    def test_no_xung_02(self):
        assert is_xung(0, 2) is False

    def test_xung_symmetric(self):
        """Ngo(6) <-> Ty(0) = Xung (symmetric)"""
        assert is_xung(6, 0) is True


class TestIsCanKhac:

    def test_giap_khac_mau(self):
        assert is_can_khac(0, 4) is True

    def test_mau_khac_nham(self):
        assert is_can_khac(4, 8) is True

    def test_canh_khac_giap(self):
        assert is_can_khac(6, 0) is True

    def test_giap_no_khac_tan(self):
        assert is_can_khac(0, 7) is False


# ─────────────────────────────────────────────────────────────────────────────
# 9. getDayInfo — integration smoke test
# ─────────────────────────────────────────────────────────────────────────────

class TestGetDayInfo:

    def test_returns_dict(self):
        info = get_day_info("2026-03-11")
        assert isinstance(info, dict)

    def test_date_field(self):
        info = get_day_info("2026-03-11")
        assert info["date"] == "2026-03-11"

    def test_can_name_is_string(self):
        info = get_day_info("2026-03-11")
        assert isinstance(info["day_can_name"], str)

    def test_chi_name_is_string(self):
        info = get_day_info("2026-03-11")
        assert isinstance(info["day_chi_name"], str)

    def test_lunar_day_range(self):
        info = get_day_info("2026-03-11")
        assert 1 <= info["lunar_day"] <= 30

    def test_lunar_month_range(self):
        info = get_day_info("2026-03-11")
        assert 1 <= info["lunar_month"] <= 12

    def test_truc_idx_range(self):
        info = get_day_info("2026-03-11")
        assert 0 <= info["truc_idx"] <= 11

    def test_is_layer1_pass_is_bool(self):
        info = get_day_info("2026-03-11")
        assert isinstance(info["is_layer1_pass"], bool)

    def test_has_thien_duc_is_bool(self):
        info = get_day_info("2026-03-11")
        assert isinstance(info["has_thien_duc"], bool)

    def test_has_nguyet_duc_is_bool(self):
        info = get_day_info("2026-03-11")
        assert isinstance(info["has_nguyet_duc"], bool)

    def test_is_cohon_false_not_month7(self):
        info = get_day_info("2026-03-11")
        assert info["is_cohon"] is False

    def test_2026_03_11_can_name(self):
        info = get_day_info("2026-03-11")
        assert info["day_can_name"] == "Giáp"

    def test_2026_03_11_chi_name(self):
        info = get_day_info("2026-03-11")
        assert info["day_chi_name"] == "Thìn"

    def test_all_required_keys(self):
        info = get_day_info("2026-03-11")
        required = {
            "date", "solar_day", "solar_month", "solar_year",
            "day_can_idx", "day_chi_idx", "day_can_name", "day_chi_name", "day_can_hanh",
            "day_nap_am_hanh",
            "lunar_day", "lunar_month", "lunar_year", "is_leap_month",
            "truc_idx", "truc_name", "truc_score",
            "has_thien_duc", "has_thien_duc_hop", "has_nguyet_duc", "has_nguyet_duc_hop",
            "is_nguyet_ky", "is_tam_nuong", "is_duong_cong_ky",
            "is_truc_pha", "is_truc_nguy",
            "is_layer1_pass", "is_cohon",
        }
        assert required.issubset(set(info.keys()))


# ─────────────────────────────────────────────────────────────────────────────
# 10. getDayInfo — Hung Ngay edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestGetDayInfoHungNgay:

    def test_nguyet_ky_fails_layer1(self):
        """If a day is Nguyet Ky, is_layer1_pass must be False."""
        info = get_day_info("2026-02-22")
        if info["lunar_day"] == 5:
            assert info["is_nguyet_ky"] is True
            assert info["is_layer1_pass"] is False
        else:
            # Date offset from lunar conversion — just check consistency
            assert not info["is_nguyet_ky"] or not info["is_layer1_pass"]

    def test_layer1_pass_consistency(self):
        """Layer 1 pass = none of the 5 hung ngay flags."""
        info = get_day_info("2026-04-15")
        expected_pass = (
            not info["is_nguyet_ky"]
            and not info["is_tam_nuong"]
            and not info["is_duong_cong_ky"]
            and not info["is_truc_pha"]
            and not info["is_truc_nguy"]
        )
        assert info["is_layer1_pass"] == expected_pass


# ─────────────────────────────────────────────────────────────────────────────
# 11. getUserChart
# ─────────────────────────────────────────────────────────────────────────────

class TestGetUserChart:

    def test_1984_year_can_name(self):
        chart = get_user_chart("1984-03-15")
        assert chart["year_can_name"] == "Giáp"

    def test_1984_year_chi_name(self):
        chart = get_user_chart("1984-03-15")
        assert chart["year_chi_name"] == "Tý"

    def test_1984_menh_hanh(self):
        chart = get_user_chart("1984-03-15")
        assert chart["menh_hanh"] == "Kim"

    def test_1984_duong_than(self):
        chart = get_user_chart("1984-03-15")
        assert chart["duong_than"] == "Thổ"

    def test_1984_ky_than(self):
        chart = get_user_chart("1984-03-15")
        assert chart["ky_than"] == "Hỏa"

    def test_2026_year_can_name(self):
        chart = get_user_chart("2026-06-01")
        assert chart["year_can_name"] == "Bính"

    def test_2026_menh_hanh(self):
        chart = get_user_chart("2026-06-01")
        assert chart["menh_hanh"] == "Thủy"

    def test_2026_duong_than(self):
        chart = get_user_chart("2026-06-01")
        assert chart["duong_than"] == "Kim"


# ─────────────────────────────────────────────────────────────────────────────
# 12. getMonthInfo
# ─────────────────────────────────────────────────────────────────────────────

class TestGetMonthInfo:

    def test_returns_correct_count_march(self):
        result = get_month_info(2026, 3)
        assert len(result) == 31  # March has 31 days

    def test_returns_correct_count_february_2026(self):
        result = get_month_info(2026, 2)
        assert len(result) == 28  # 2026 is not leap

    def test_filter_passed_reduces_count(self):
        all_days = get_month_info(2026, 3, filter_passed=False)
        passed_days = get_month_info(2026, 3, filter_passed=True)
        assert len(passed_days) <= len(all_days)

    def test_filtered_days_all_pass_layer1(self):
        passed_days = get_month_info(2026, 3, filter_passed=True)
        for d in passed_days:
            assert d["is_layer1_pass"] is True


# ─────────────────────────────────────────────────────────────────────────────
# 13. Purity invariant — same input must produce same output
# ─────────────────────────────────────────────────────────────────────────────

class TestPurity:

    def test_get_day_info_deterministic(self):
        a = get_day_info("2026-03-11")
        b = get_day_info("2026-03-11")
        assert a == b

    def test_get_user_chart_deterministic(self):
        a = get_user_chart("1984-03-15")
        b = get_user_chart("1984-03-15")
        assert a == b

    def test_get_can_chi_day_deterministic(self):
        a = get_can_chi_day(2026, 3, 11)
        b = get_can_chi_day(2026, 3, 11)
        assert a == b
