"""
sao_ngay.py — Day Star checks (Thiên Đức, Nguyệt Đức, etc.).

Ported from calendar-service.js §4.
Source of truth: docs/algorithm.md §12.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Thiên Đức — one per lunar month, matches either Can or Chi
# ─────────────────────────────────────────────────────────────────────────────

THIEN_DUC: list[dict] = [
    {"type": "can", "idx": 3},   # month 1:  Đinh
    {"type": "chi", "idx": 7},   # month 2:  Thân
    {"type": "can", "idx": 8},   # month 3:  Nhâm
    {"type": "can", "idx": 7},   # month 4:  Tân
    {"type": "chi", "idx": 11},  # month 5:  Hợi
    {"type": "can", "idx": 0},   # month 6:  Giáp
    {"type": "can", "idx": 9},   # month 7:  Quý
    {"type": "chi", "idx": 2},   # month 8:  Dần
    {"type": "can", "idx": 2},   # month 9:  Bính
    {"type": "can", "idx": 1},   # month 10: Ất
    {"type": "chi", "idx": 5},   # month 11: Tỵ
    {"type": "can", "idx": 6},   # month 12: Canh
]

# Thiên Đức Hợp — Can index, None = tháng tứ trọng
THIEN_DUC_HOP: list[int | None] = [8, None, 3, 2, None, 5, 4, None, 7, 6, None, 1]

# Nguyệt Đức — Can index per month
NGUYET_DUC_CAN: list[int] = [2, 0, 8, 6, 2, 0, 8, 6, 2, 0, 8, 6]

# Nguyệt Đức Hợp — Can index per month
NGUYET_DUC_HOP_CAN: list[int] = [7, 5, 3, 1, 7, 5, 3, 1, 7, 5, 3, 1]


def check_thien_duc(lunar_month: int, day_can_idx: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Đức for the given lunar month."""
    td = THIEN_DUC[lunar_month - 1]
    if td["type"] == "can":
        return day_can_idx == td["idx"]
    return day_chi_idx == td["idx"]


def check_thien_duc_hop(lunar_month: int, day_can_idx: int) -> bool:
    """Check if day has Thiên Đức Hợp for the given lunar month."""
    tdh = THIEN_DUC_HOP[lunar_month - 1]
    return tdh is not None and day_can_idx == tdh


def check_nguyet_duc(lunar_month: int, day_can_idx: int) -> bool:
    """Check if day has Nguyệt Đức for the given lunar month."""
    return day_can_idx == NGUYET_DUC_CAN[lunar_month - 1]


def check_nguyet_duc_hop(lunar_month: int, day_can_idx: int) -> bool:
    """Check if day has Nguyệt Đức Hợp for the given lunar month."""
    return day_can_idx == NGUYET_DUC_HOP_CAN[lunar_month - 1]
