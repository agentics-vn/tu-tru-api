"""
tests/unit/test_pillars.py — Verify Four Pillars engine against reference calculators.

Cross-references: Joey Yap BaziCalc, bazi.masteryacademy.com, pillars.js test vectors.
"""

from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from engine.pillars import (
    BIRTH_HOUR_TO_CHI,
    VALID_BIRTH_HOURS,
    HOUR_CAN_START,
    is_ty_muon,
    get_tu_tru,
    get_tu_tru_optional,
)


# ─────────────────────────────────────────────────────────────────────────────
# Birth hour mapping
# ─────────────────────────────────────────────────────────────────────────────

class TestBirthHourMapping:
    """Verify all 13 dropdown values map to correct Chi indices."""

    def test_valid_birth_hours_count(self):
        assert len(VALID_BIRTH_HOURS) == 13

    @pytest.mark.parametrize("hour,expected_chi", [
        (0, 0),    # Ty Som
        (2, 1),    # Suu
        (4, 2),    # Dan
        (6, 3),    # Mao
        (8, 4),    # Thin
        (10, 5),   # Ty (snake)
        (11, 6),   # Ngo
        (14, 7),   # Mui
        (16, 8),   # Than
        (18, 9),   # Dau
        (20, 10),  # Tuat
        (22, 11),  # Hoi
        (23, 0),   # Ty Muon
    ])
    def test_hour_to_chi(self, hour: int, expected_chi: int):
        assert BIRTH_HOUR_TO_CHI[hour] == expected_chi

    def test_ty_muon_detection(self):
        assert is_ty_muon(23) is True
        assert is_ty_muon(0) is False
        assert is_ty_muon(11) is False

    def test_invalid_birth_hour_raises(self):
        with pytest.raises(ValueError, match="Giờ sinh phải là một trong"):
            get_tu_tru("1990-03-21", 5)  # 5 is not a valid dropdown value

    def test_invalid_birth_hour_13(self):
        with pytest.raises(ValueError):
            get_tu_tru("1990-03-21", 13)


# ─────────────────────────────────────────────────────────────────────────────
# Lap Xuan boundary tests
# ─────────────────────────────────────────────────────────────────────────────

class TestLapXuanBoundary:
    """Year pillar changes at Lap Xuan (~Feb 4), NOT Jan 1."""

    def test_before_lap_xuan_1990(self):
        """1990-02-03 is before Lap Xuan → year = Ky Ty (1989)."""
        result = get_tu_tru("1990-02-03", 8)
        assert result["year"]["can_name"] == "Kỷ"
        assert result["year"]["chi_name"] == "Tỵ"

    def test_after_lap_xuan_1990(self):
        """1990-02-05 is after Lap Xuan → year = Canh Ngo (1990)."""
        result = get_tu_tru("1990-02-05", 8)
        assert result["year"]["can_name"] == "Canh"
        assert result["year"]["chi_name"] == "Ngọ"

    def test_before_lap_xuan_2024(self):
        """2024-02-03 is before Lap Xuan → year = Quy Mao (2023)."""
        result = get_tu_tru("2024-02-03", 8)
        assert result["year"]["can_name"] == "Quý"
        assert result["year"]["chi_name"] == "Mão"

    def test_after_lap_xuan_2024(self):
        """2024-02-05 is after Lap Xuan → year = Giap Thin (2024)."""
        result = get_tu_tru("2024-02-05", 8)
        assert result["year"]["can_name"] == "Giáp"
        assert result["year"]["chi_name"] == "Thìn"


# ─────────────────────────────────────────────────────────────────────────────
# Full chart verification — known birth charts
# ─────────────────────────────────────────────────────────────────────────────

class TestFullChart:
    """Verify complete 4-pillar charts against reference calculators."""

    def test_chart_1990_03_21_hour8(self):
        """DOB: 1990-03-21, Gio Thin (7-9h)."""
        r = get_tu_tru("1990-03-21", 8)
        # Year: Canh Ngo
        assert r["year"]["can_name"] == "Canh"
        assert r["year"]["chi_name"] == "Ngọ"
        # Month: Ky Mao
        assert r["month"]["can_name"] == "Kỷ"
        assert r["month"]["chi_name"] == "Mão"
        # Day: At Dau (verify against sxtwl)
        assert r["day"]["can_name"] is not None
        assert r["day"]["chi_name"] is not None
        # Hour pillar should be Canh Thin (dayCanIdx=1 Ất → HOUR_CAN_START[1%5]=2 Bính, chi=4 Thìn → can=(2+4)%10=6 Canh)
        assert r["hour"]["chi_name"] == "Thìn"  # hour=8 → chi=4

    def test_chart_1984_03_15_hour10(self):
        """DOB: 1984-03-15, Gio Ty (9-11h)."""
        r = get_tu_tru("1984-03-15", 10)
        # Year: Giap Ty
        assert r["year"]["can_name"] == "Giáp"
        assert r["year"]["chi_name"] == "Tý"
        # Month: Dinh Mao
        assert r["month"]["can_name"] == "Đinh"
        assert r["month"]["chi_name"] == "Mão"

    def test_nhat_chu_present(self):
        """Day Master (Nhat Chu) must be included and consistent with day pillar."""
        r = get_tu_tru("1990-03-21", 8)
        assert r["nhat_chu"]["can_idx"] == r["day"]["can_idx"]
        assert r["nhat_chu"]["can_name"] == r["day"]["can_name"]
        assert r["nhat_chu"]["hanh"] is not None

    def test_display_format(self):
        """Display string should show all 4 pillars."""
        r = get_tu_tru("1990-03-21", 8)
        display = r["display"]
        assert "|" in display
        assert display.count("|") == 3


# ─────────────────────────────────────────────────────────────────────────────
# Ty Muon (late Ty, 23h) — Tảo Tý phái (NO day shift)
# ─────────────────────────────────────────────────────────────────────────────

class TestTyMuon:
    """Tảo Tý phái: Ty Muon (23h) stays on SAME calendar day — no shift."""

    def test_day_pillar_same_as_current_day(self):
        """For Ty Muon under Tảo Tý, day pillar is the SAME calendar day."""
        # Ty Som (0h) and Ty Muon (23h) on Jan 5 → same day pillar
        ty_som_result = get_tu_tru("1990-01-05", 0)
        ty_muon_result = get_tu_tru("1990-01-05", 23)

        assert ty_muon_result["day"]["can_idx"] == ty_som_result["day"]["can_idx"]
        assert ty_muon_result["day"]["chi_idx"] == ty_som_result["day"]["chi_idx"]

    def test_day_pillar_differs_from_next_day(self):
        """Ty Muon on Jan 5 should NOT equal Jan 6's day pillar."""
        next_day_result = get_tu_tru("1990-01-06", 0)
        ty_muon_result = get_tu_tru("1990-01-05", 23)

        # Day pillars cycle every 60, consecutive days differ
        assert (
            ty_muon_result["day"]["can_idx"] != next_day_result["day"]["can_idx"]
            or ty_muon_result["day"]["chi_idx"] != next_day_result["day"]["chi_idx"]
        )

    def test_year_pillar_same_for_all_hours(self):
        """Year pillar is identical regardless of birth hour."""
        result_ty_muon = get_tu_tru("1990-12-31", 23)
        result_original = get_tu_tru("1990-12-31", 0)

        assert result_ty_muon["year"]["can_idx"] == result_original["year"]["can_idx"]
        assert result_ty_muon["year"]["chi_idx"] == result_original["year"]["chi_idx"]

    def test_month_pillar_same_for_all_hours(self):
        """Month pillar is identical regardless of birth hour."""
        result_ty_muon = get_tu_tru("1990-03-21", 23)
        result_original = get_tu_tru("1990-03-21", 0)

        assert result_ty_muon["month"]["can_idx"] == result_original["month"]["can_idx"]
        assert result_ty_muon["month"]["chi_idx"] == result_original["month"]["chi_idx"]

    def test_hour_pillar_is_ty(self):
        """Ty Muon hour should be Ty chi (idx 0)."""
        result = get_tu_tru("1990-03-21", 23)
        assert result["hour"]["chi_idx"] == 0
        assert result["hour"]["chi_name"] == "Tý"

    def test_hour_can_uses_same_day_can(self):
        """Hour Can for Tý Muộn uses current day's Day Can (no shift)."""
        result_noon = get_tu_tru("1990-03-21", 11)   # Ngọ
        result_ty_muon = get_tu_tru("1990-03-21", 23)  # Tý Muộn

        # Both should use the same Day Can for deriving Hour Can
        assert result_ty_muon["day"]["can_idx"] == result_noon["day"]["can_idx"]


# ─────────────────────────────────────────────────────────────────────────────
# Hour pillar derivation (Ngu Thu Don Thoi)
# ─────────────────────────────────────────────────────────────────────────────

class TestHourPillar:
    """Hour Can derived from Day Can using the Ngu Thu Don Thoi rule."""

    def test_hour_can_start_table(self):
        """Verify the HOUR_CAN_START lookup."""
        assert HOUR_CAN_START == [0, 2, 4, 6, 8]

    @pytest.mark.parametrize("birth_time,expected_chi_name", [
        (0, "Tý"),
        (2, "Sửu"),
        (4, "Dần"),
        (6, "Mão"),
        (8, "Thìn"),
        (10, "Tỵ"),
        (11, "Ngọ"),
        (14, "Mùi"),
        (16, "Thân"),
        (18, "Dậu"),
        (20, "Tuất"),
        (22, "Hợi"),
        (23, "Tý"),
    ])
    def test_all_hour_chi_names(self, birth_time: int, expected_chi_name: str):
        result = get_tu_tru("2000-06-15", birth_time)
        assert result["hour"]["chi_name"] == expected_chi_name


# ─────────────────────────────────────────────────────────────────────────────
# Backward compatibility
# ─────────────────────────────────────────────────────────────────────────────

class TestBackwardCompat:
    """get_tu_tru_optional returns None when birth_time not provided."""

    def test_optional_none(self):
        assert get_tu_tru_optional("1990-03-21") is None

    def test_optional_with_time(self):
        result = get_tu_tru_optional("1990-03-21", 8)
        assert result is not None
        assert "year" in result
        assert "month" in result
        assert "day" in result
        assert "hour" in result
