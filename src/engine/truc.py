"""
truc.py — 12 Trực (Day Officers) calculation.

Ported from calendar-service.js §3.
Source of truth: docs/algorithm.md §4.
"""

from __future__ import annotations

# 12 Trực names and scores (index 0-11)
TRUC_NAMES: list[str] = [
    "Kiến", "Trừ", "Mãn", "Bình", "Định", "Chấp",
    "Phá", "Nguy", "Thành", "Thu", "Khai", "Bế",
]

TRUC_SCORES: list[int] = [1, 1, 2, 1, 2, 0, -2, -2, 2, 0, 2, -1]

# Lunar month → ruling Chi index
# Month 1→Dần(2), 2→Mão(3), ... 11→Tý(0), 12→Sửu(1)
MONTH_CHI_IDX: list[int] = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1]


def get_truc_idx(day_chi_idx: int, lunar_month: int) -> int:
    """
    Calculate Trực index (0-11) from day's Địa Chi and lunar month.

    Args:
        day_chi_idx: 0-11
        lunar_month: 1-12

    Returns:
        int 0-11
    """
    month_chi = MONTH_CHI_IDX[lunar_month - 1]
    return ((day_chi_idx - month_chi) % 12 + 12) % 12
