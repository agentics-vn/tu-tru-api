"""
hung_ngay.py — Universal bad-day checks (Layer 1 discard).

Ported from calendar-service.js §5.
Source of truth: docs/algorithm.md §5, §13.
"""

from __future__ import annotations

# Tam Nương days (lunar)
TAM_NUONG_DAYS: frozenset[int] = frozenset({3, 7, 13, 18, 22, 27})

# Dương Công Kỵ Nhật — 13 dates (lunar month → set of lunar days)
# NOTE (T4-01): This table is YEAR-INDEPENDENT.  The 13 Dương Công Kỵ Nhật
# recur on fixed lunar month/day positions every year, so no annual update or
# 2026–2030 expansion is needed.  Verified against Lịch Vạn Niên references.
DUONG_CONG_KY: dict[int, list[int]] = {
    1: [13], 2: [11], 3: [9], 4: [7],
    5: [5], 6: [3], 7: [1, 29], 8: [27],
    9: [25], 10: [23], 11: [21], 12: [19],
}


def is_nguyet_ky(lunar_day: int) -> bool:
    """Nguyệt Kỵ — lunar days 5, 14, 23."""
    return lunar_day in (5, 14, 23)


def is_tam_nuong(lunar_day: int) -> bool:
    """Tam Nương — lunar days 3, 7, 13, 18, 22, 27."""
    return lunar_day in TAM_NUONG_DAYS


def is_duong_cong_ky(lunar_month: int, lunar_day: int) -> bool:
    """Dương Công Kỵ Nhật — 13 specific dates per year."""
    return lunar_day in DUONG_CONG_KY.get(lunar_month, [])


def is_cohon(lunar_month: int) -> bool:
    """Tháng Cô Hồn — lunar month 7."""
    return lunar_month == 7
