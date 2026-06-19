"""
cung_menh.py — Mệnh cung & Thai nguyên.

Source: docs/algorithm.md §22.5–22.6
"""

from __future__ import annotations

from engine.bazi_solar import YIN_MONTH_STEM_START
from engine.can_chi import CAN_NAMES, CHI_NAMES


def _chi_num_from_yin(chi_idx: int) -> int:
    """寅=1 … 丑=12 numbering for 命宫 formula."""
    return ((chi_idx - 2 + 12) % 12) + 1


def _chi_idx_from_num(num: int) -> int:
    """Convert 1-based 寅=1 back to 0-based chi index."""
    return (num + 1) % 12


def get_thai_nguyen(month_can_idx: int, month_chi_idx: int) -> dict:
    can_idx = (month_can_idx + 1) % 10
    chi_idx = (month_chi_idx + 3) % 12
    return {
        "can_idx": can_idx,
        "chi_idx": chi_idx,
        "can_name": CAN_NAMES[can_idx],
        "chi_name": CHI_NAMES[chi_idx],
        "display": f"{CAN_NAMES[can_idx]} {CHI_NAMES[chi_idx]}",
    }


def get_menh_cung(
    year_can_idx: int,
    month_chi_idx: int,
    hour_chi_idx: int,
) -> dict:
    month_num = _chi_num_from_yin(month_chi_idx)
    hour_num = _chi_num_from_yin(hour_chi_idx)
    total = month_num + hour_num
    ming_num = (14 - total) if total < 14 else (26 - total)
    if ming_num > 12:
        ming_num -= 12

    ming_chi_idx = _chi_idx_from_num(ming_num)
    base = YIN_MONTH_STEM_START[year_can_idx % 5]
    offset = (ming_chi_idx - 2 + 12) % 12
    ming_can_idx = (base + offset) % 10

    return {
        "can_idx": ming_can_idx,
        "chi_idx": ming_chi_idx,
        "can_name": CAN_NAMES[ming_can_idx],
        "chi_name": CHI_NAMES[ming_chi_idx],
        "display": f"{CAN_NAMES[ming_can_idx]} {CHI_NAMES[ming_chi_idx]}",
    }


def analyze_cung_menh(tu_tru: dict) -> dict:
    return {
        "menh_cung": get_menh_cung(
            tu_tru["year"]["can_idx"],
            tu_tru["month"]["chi_idx"],
            tu_tru["hour"]["chi_idx"],
        ),
        "thai_nguyen": get_thai_nguyen(
            tu_tru["month"]["can_idx"],
            tu_tru["month"]["chi_idx"],
        ),
    }
