"""
tests/unit/test_tu_tru_engine.py — Unit tests for Phase 2-5 Tứ Trụ engine modules.

Tests: Tàng Can, Cường Nhược, Dụng Thần, Thập Thần, Đại Vận.
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from engine.pillars import get_tu_tru
from engine.tang_can import get_tang_can, get_all_elements, get_day_master_support
from engine.cuong_nhuoc import analyze_chart_strength, SEASONAL_ELEMENT
from engine.dung_than import find_dung_than
from engine.thap_than import get_thap_than, analyze_thap_than, get_day_god_for_intent
from engine.dai_van import get_dai_van, get_current_dai_van, get_dai_van_direction


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Tàng Can (Hidden Stems)
# ─────────────────────────────────────────────────────────────────────────────

class TestTangCan:
    """Verify hidden stems table and element counting."""

    def test_ty_hidden_stems(self):
        """Tý (0) → [Quý]"""
        stems = get_tang_can(0)
        assert len(stems) == 1
        assert stems[0]["can_name"] == "Quý"
        assert stems[0]["hanh"] == "Thủy"
        assert stems[0]["role"] == "chu_khi"

    def test_dan_hidden_stems(self):
        """Dần (2) → [Giáp, Bính, Mậu]"""
        stems = get_tang_can(2)
        assert len(stems) == 3
        assert stems[0]["can_name"] == "Giáp"
        assert stems[1]["can_name"] == "Bính"
        assert stems[2]["can_name"] == "Mậu"
        assert stems[0]["role"] == "chu_khi"
        assert stems[1]["role"] == "trung_khi"
        assert stems[2]["role"] == "du_khi"

    def test_dau_hidden_stems(self):
        """Dậu (9) → [Tân]"""
        stems = get_tang_can(9)
        assert len(stems) == 1
        assert stems[0]["can_name"] == "Tân"
        assert stems[0]["hanh"] == "Kim"

    def test_element_counting(self):
        """Element counts should sum to a positive total for any chart."""
        tu_tru = get_tu_tru("1990-03-21", 8)
        elements = get_all_elements(tu_tru)
        assert sum(elements.values()) > 0
        assert all(v >= 0 for v in elements.values())
        # All 5 elements should be present as keys
        assert set(elements.keys()) == {"Kim", "Mộc", "Thủy", "Hỏa", "Thổ"}

    def test_day_master_support(self):
        """Support + opposition should sum to total elements."""
        tu_tru = get_tu_tru("1990-03-21", 8)
        dm_hanh = tu_tru["nhat_chu"]["hanh"]
        support, opposition = get_day_master_support(tu_tru, dm_hanh)
        elements = get_all_elements(tu_tru)
        total = sum(elements.values())
        assert abs(support + opposition - total) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3: Cường Nhược + Dụng Thần
# ─────────────────────────────────────────────────────────────────────────────

class TestCuongNhuoc:
    """Verify chart strength analysis."""

    def test_strength_is_valid(self):
        """Strength must be strong, weak, or balanced."""
        tu_tru = get_tu_tru("1990-03-21", 8)
        result = analyze_chart_strength(tu_tru)
        assert result["strength"] in ("vượng", "nhược", "cân bằng")

    def test_seasonal_element_spring(self):
        """Spring months (Dần=2, Mão=3) → Mộc."""
        assert SEASONAL_ELEMENT[2] == "Mộc"
        assert SEASONAL_ELEMENT[3] == "Mộc"

    def test_seasonal_element_summer(self):
        """Summer months (Tỵ=5, Ngọ=6) → Hỏa."""
        assert SEASONAL_ELEMENT[5] == "Hỏa"
        assert SEASONAL_ELEMENT[6] == "Hỏa"

    def test_support_ratio_in_range(self):
        """Support ratio must be between 0 and 1."""
        tu_tru = get_tu_tru("1990-03-21", 8)
        result = analyze_chart_strength(tu_tru)
        assert 0.0 <= result["support_ratio"] <= 1.0

    def test_element_counts_present(self):
        tu_tru = get_tu_tru("1990-03-21", 8)
        result = analyze_chart_strength(tu_tru)
        assert "element_counts" in result
        assert len(result["element_counts"]) == 5


class TestDungThan:
    """Verify Dụng Thần identification."""

    def test_dung_than_is_valid_element(self):
        """Dụng Thần must be one of the 5 elements."""
        tu_tru = get_tu_tru("1990-03-21", 8)
        result = find_dung_than(tu_tru)
        valid_elements = {"Kim", "Mộc", "Thủy", "Hỏa", "Thổ"}
        assert result["dung_than"] in valid_elements
        assert result["hi_than"] in valid_elements
        assert result["ky_than"] in valid_elements
        assert result["cuu_than"] in valid_elements

    def test_dung_than_differs_from_ky_than(self):
        """Dụng Thần and Kỵ Thần should never be the same."""
        tu_tru = get_tu_tru("1990-03-21", 8)
        result = find_dung_than(tu_tru)
        assert result["dung_than"] != result["ky_than"]

    def test_different_birth_times_may_differ(self):
        """Same date, different times should potentially give different charts."""
        r1 = find_dung_than(get_tu_tru("1990-03-21", 0))
        r2 = find_dung_than(get_tu_tru("1990-03-21", 11))
        # They may or may not differ, but the function should work for both
        assert r1["dung_than"] is not None
        assert r2["dung_than"] is not None

    def test_strength_included(self):
        tu_tru = get_tu_tru("1990-03-21", 8)
        result = find_dung_than(tu_tru)
        assert result["strength"] in ("vượng", "nhược", "cân bằng")
        assert "analysis" in result


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4: Thập Thần (Ten Gods)
# ─────────────────────────────────────────────────────────────────────────────

class TestThapThan:
    """Verify Ten Gods derivation."""

    def test_same_element_same_polarity_is_ty_kien(self):
        """Giáp(0) vs Giáp(0) → Tỷ Kiên."""
        result = get_thap_than(0, 0)
        assert result["key"] == "ty_kien"

    def test_same_element_diff_polarity_is_kiep_tai(self):
        """Giáp(0) vs Ất(1) → Kiếp Tài."""
        result = get_thap_than(0, 1)
        assert result["key"] == "kiep_tai"

    def test_dm_generates_same_pol_is_thuc_than(self):
        """Giáp(0, Mộc) generates Hỏa: Bính(2, Hỏa, Dương) → Thực Thần."""
        result = get_thap_than(0, 2)
        assert result["key"] == "thuc_than"

    def test_dm_generates_diff_pol_is_thuong_quan(self):
        """Giáp(0, Mộc) generates Hỏa: Đinh(3, Hỏa, Âm) → Thương Quan."""
        result = get_thap_than(0, 3)
        assert result["key"] == "thuong_quan"

    def test_parent_generates_dm_same_pol_is_thien_an(self):
        """Giáp(0, Mộc) generated by Thủy: Nhâm(8, Thủy, Dương) → Thiên Ấn."""
        result = get_thap_than(0, 8)
        assert result["key"] == "thien_an"

    def test_parent_generates_dm_diff_pol_is_chinh_an(self):
        """Giáp(0, Mộc) generated by Thủy: Quý(9, Thủy, Âm) → Chính Ấn."""
        result = get_thap_than(0, 9)
        assert result["key"] == "chinh_an"

    def test_dm_destroys_same_pol_is_thien_tai(self):
        """Giáp(0, Mộc) destroys Thổ: Mậu(4, Thổ, Dương) → Thiên Tài."""
        result = get_thap_than(0, 4)
        assert result["key"] == "thien_tai"

    def test_dm_destroys_diff_pol_is_chinh_tai(self):
        """Giáp(0, Mộc) destroys Thổ: Kỷ(5, Thổ, Âm) → Chính Tài."""
        result = get_thap_than(0, 5)
        assert result["key"] == "chinh_tai"

    def test_destroys_dm_same_pol_is_that_sat(self):
        """Giáp(0, Mộc) destroyed by Kim: Canh(6, Kim, Dương) → Thất Sát."""
        result = get_thap_than(0, 6)
        assert result["key"] == "that_sat"

    def test_destroys_dm_diff_pol_is_chinh_quan(self):
        """Giáp(0, Mộc) destroyed by Kim: Tân(7, Kim, Âm) → Chính Quan."""
        result = get_thap_than(0, 7)
        assert result["key"] == "chinh_quan"

    def test_analyze_thap_than_returns_3_gods(self):
        """Analysis returns year, month, hour gods."""
        tu_tru = get_tu_tru("1990-03-21", 8)
        result = analyze_thap_than(tu_tru)
        assert "year_god" in result
        assert "month_god" in result
        assert "hour_god" in result
        assert "dominant_god" in result

    def test_intent_god_alignment(self):
        """Day god alignment should return matching god or None."""
        tu_tru = get_tu_tru("1990-03-21", 8)
        dm_can = tu_tru["day"]["can_idx"]
        # Test with some day can — result should be dict or None
        result = get_day_god_for_intent(0, dm_can, "CAU_TAI")
        assert result is None or isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5: Đại Vận (10-Year Luck Cycles)
# ─────────────────────────────────────────────────────────────────────────────

class TestDaiVan:
    """Verify 10-year luck cycle computation."""

    def test_direction_male_yang(self):
        """Male + Yang stem (Canh=6) → forward."""
        assert get_dai_van_direction(6, 1) == 1

    def test_direction_male_yin(self):
        """Male + Yin stem (Kỷ=5) → backward."""
        assert get_dai_van_direction(5, 1) == -1

    def test_direction_female_yang(self):
        """Female + Yang stem → backward (opposite of male)."""
        assert get_dai_van_direction(6, -1) == -1

    def test_direction_female_yin(self):
        """Female + Yin stem → forward (opposite of male)."""
        assert get_dai_van_direction(5, -1) == 1

    def test_cycles_count(self):
        """Should return the requested number of cycles."""
        tu_tru = get_tu_tru("1990-03-21", 8)
        cycles = get_dai_van(tu_tru, 1, "1990-03-21", num_cycles=6)
        assert len(cycles) == 6

    def test_cycles_10_year_intervals(self):
        """Each cycle should span 10 years."""
        tu_tru = get_tu_tru("1990-03-21", 8)
        cycles = get_dai_van(tu_tru, 1, "1990-03-21")
        for c in cycles:
            assert c["end_age"] - c["start_age"] == 9

    def test_cycles_have_required_keys(self):
        tu_tru = get_tu_tru("1990-03-21", 8)
        cycles = get_dai_van(tu_tru, 1, "1990-03-21", num_cycles=2)
        for c in cycles:
            assert "can_name" in c
            assert "chi_name" in c
            assert "display" in c
            assert "nap_am_hanh" in c
            assert "start_age" in c
            assert "end_age" in c

    def test_current_dai_van_found(self):
        """Should find the current cycle for a 36-year-old."""
        tu_tru = get_tu_tru("1990-03-21", 8)
        current = get_current_dai_van(tu_tru, 1, "1990-03-21", "2026-03-11")
        assert current is not None
        assert current["start_age"] <= 36 <= current["end_age"]

    def test_current_dai_van_none_for_infant(self):
        """Very young person might not have entered first cycle yet."""
        tu_tru = get_tu_tru("2025-01-15", 8)
        current = get_current_dai_van(tu_tru, 1, "2025-01-15", "2025-02-01")
        # For an infant, current cycle might be None (before first cycle start)
        # or could be in first cycle if start_age is low enough
        # Either way, function should not crash
        assert current is None or isinstance(current, dict)


# ─────────────────────────────────────────────────────────────────────────────
# Integration: calendar_service with full Tứ Trụ
# ─────────────────────────────────────────────────────────────────────────────

class TestCalendarServiceTuTru:
    """Verify get_user_chart with birth_time enrichment."""

    def test_without_birth_time_backward_compat(self):
        """Without birth_time, response matches old shape exactly."""
        from calendar_service import get_user_chart
        chart = get_user_chart("1990-03-21")
        assert "menh_hanh" in chart
        assert "duong_than" in chart
        assert "ky_than" in chart
        assert "tu_tru" not in chart
        assert "dung_than" not in chart

    def test_with_birth_time_enriched(self):
        """With birth_time, response includes Tứ Trụ data."""
        from calendar_service import get_user_chart
        chart = get_user_chart("1990-03-21", birth_time=8)
        # Old fields still present
        assert "menh_hanh" in chart
        assert "duong_than" in chart
        assert "ky_than" in chart
        # New fields
        assert "tu_tru" in chart
        assert "nhat_chu" in chart
        assert "dung_than" in chart
        assert "hi_than" in chart
        assert "ky_than_v2" in chart
        assert "chart_strength" in chart
        assert "thap_than" in chart

    def test_with_gender_includes_dai_van(self):
        """With birth_time + gender, includes Đại Vận."""
        from calendar_service import get_user_chart
        chart = get_user_chart("1990-03-21", birth_time=8, gender=1)
        assert "current_dai_van" in chart
        assert chart["current_dai_van"] is not None
        assert "gender" in chart

    def test_without_gender_no_dai_van(self):
        """With birth_time but no gender, no Đại Vận."""
        from calendar_service import get_user_chart
        chart = get_user_chart("1990-03-21", birth_time=8)
        assert "current_dai_van" not in chart
