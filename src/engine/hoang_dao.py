"""
hoang_dao.py — Hoàng Đạo / Hắc Đạo day classification and Giờ Hoàng Đạo.

Source of truth: docs/algorithm.md §15, §16.
⚠️ SME verify: formulas sourced from traditional lịch vạn niên.
"""

from __future__ import annotations

from .can_chi import CHI_NAMES

# ─────────────────────────────────────────────────────────────────────────────
# §15 — 12 Hoàng Đạo / Hắc Đạo Stars
# ─────────────────────────────────────────────────────────────────────────────

STARS_12: list[dict] = [
    {"name": "Thanh Long",  "type": "hoang_dao"},   # 0
    {"name": "Minh Đường",  "type": "hoang_dao"},   # 1
    {"name": "Thiên Hình",  "type": "hac_dao"},     # 2
    {"name": "Chu Tước",    "type": "hac_dao"},     # 3
    {"name": "Kim Quỹ",     "type": "hoang_dao"},   # 4
    {"name": "Thiên Đức",   "type": "hoang_dao"},   # 5  (star, not sao §12)
    {"name": "Bạch Hổ",     "type": "hac_dao"},     # 6
    {"name": "Ngọc Đường",  "type": "hoang_dao"},   # 7
    {"name": "Thiên Lao",   "type": "hac_dao"},     # 8
    {"name": "Huyền Vũ",    "type": "hac_dao"},     # 9
    {"name": "Tư Mệnh",    "type": "hoang_dao"},   # 10
    {"name": "Câu Trận",   "type": "hac_dao"},     # 11
]

HOANG_DAO_INDICES: frozenset[int] = frozenset({0, 1, 4, 5, 7, 10})


def get_day_star(lunar_month: int, day_chi_idx: int) -> dict:
    """
    Return the governing star for a day.

    Args:
        lunar_month: 1-12
        day_chi_idx: 0-11

    Returns:
        dict with keys: star_idx, star_name, star_type, is_hoang_dao
    """
    start_chi = ((lunar_month - 1) % 6) * 2
    star_idx = ((day_chi_idx - start_chi) % 12 + 12) % 12
    star = STARS_12[star_idx]
    return {
        "star_idx": star_idx,
        "star_name": star["name"],
        "star_type": star["type"],
        "is_hoang_dao": star_idx in HOANG_DAO_INDICES,
    }


def is_hoang_dao(lunar_month: int, day_chi_idx: int) -> bool:
    """Quick check: is this day Hoàng Đạo?"""
    start_chi = ((lunar_month - 1) % 6) * 2
    star_idx = ((day_chi_idx - start_chi) % 12 + 12) % 12
    return star_idx in HOANG_DAO_INDICES


# ─────────────────────────────────────────────────────────────────────────────
# §16 — Giờ Hoàng Đạo (Good Hours per Day)
# ─────────────────────────────────────────────────────────────────────────────

# Time ranges for each Chi hour
CHI_HOUR_RANGES: list[dict] = [
    {"chi_idx": 0,  "chi_name": "Tý",   "start": "23:00", "end": "01:00"},
    {"chi_idx": 1,  "chi_name": "Sửu",  "start": "01:00", "end": "03:00"},
    {"chi_idx": 2,  "chi_name": "Dần",  "start": "03:00", "end": "05:00"},
    {"chi_idx": 3,  "chi_name": "Mão",  "start": "05:00", "end": "07:00"},
    {"chi_idx": 4,  "chi_name": "Thìn", "start": "07:00", "end": "09:00"},
    {"chi_idx": 5,  "chi_name": "Tỵ",   "start": "09:00", "end": "11:00"},
    {"chi_idx": 6,  "chi_name": "Ngọ",  "start": "11:00", "end": "13:00"},
    {"chi_idx": 7,  "chi_name": "Mùi",  "start": "13:00", "end": "15:00"},
    {"chi_idx": 8,  "chi_name": "Thân", "start": "15:00", "end": "17:00"},
    {"chi_idx": 9,  "chi_name": "Dậu",  "start": "17:00", "end": "19:00"},
    {"chi_idx": 10, "chi_name": "Tuất", "start": "19:00", "end": "21:00"},
    {"chi_idx": 11, "chi_name": "Hợi",  "start": "21:00", "end": "23:00"},
]

# Even day Chi → good hour set
GOOD_HOURS_EVEN: frozenset[int] = frozenset({0, 1, 4, 5, 7, 10})

# Odd day Chi → good hour set
GOOD_HOURS_ODD: frozenset[int] = frozenset({2, 3, 5, 6, 8, 11})


def get_gio_hoang_dao(day_chi_idx: int) -> list[dict]:
    """
    Return the 6 good (Hoàng Đạo) hours for a day.

    Args:
        day_chi_idx: 0-11 (the day's Địa Chi index)

    Returns:
        list of 6 dicts, each with: chi_idx, chi_name, start, end
    """
    good = GOOD_HOURS_EVEN if day_chi_idx % 2 == 0 else GOOD_HOURS_ODD
    return [
        {
            "chi_idx": h["chi_idx"],
            "chi_name": h["chi_name"],
            "start": h["start"],
            "end": h["end"],
        }
        for h in CHI_HOUR_RANGES
        if h["chi_idx"] in good
    ]


def get_gio_hac_dao(day_chi_idx: int) -> list[dict]:
    """
    Return the 6 bad (Hắc Đạo) hours for a day.

    Args:
        day_chi_idx: 0-11 (the day's Địa Chi index)

    Returns:
        list of 6 dicts, each with: chi_idx, chi_name, start, end
    """
    good = GOOD_HOURS_EVEN if day_chi_idx % 2 == 0 else GOOD_HOURS_ODD
    return [
        {
            "chi_idx": h["chi_idx"],
            "chi_name": h["chi_name"],
            "start": h["start"],
            "end": h["end"],
        }
        for h in CHI_HOUR_RANGES
        if h["chi_idx"] not in good
    ]
