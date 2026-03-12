"""
pillars.py — Tứ Trụ / Bát Tự (Four Pillars) Engine.

Wraps sxtwl library for astronomical-accurate pillar computation.
Handles: Lập Xuân boundary, Tiết Khí month boundaries.

Convention: Tảo Tý phái (早子派) — day boundary at midnight (00:00).
Giờ Tý Muộn (23:00–23:59) belongs to the CURRENT calendar day.
No day-pillar shift at 23h.

Source of truth: docs/algorithm.md §17
"""

from __future__ import annotations

from typing import Optional

import sxtwl

from engine.can_chi import CAN_NAMES, CHI_NAMES, CAN_HANH

# ─────────────────────────────────────────────────────────────────────────────
# Birth time dropdown → Chi mapping
# ─────────────────────────────────────────────────────────────────────────────

# Values from front-end dropdown (matching external Lập Lá Số API)
VALID_BIRTH_HOURS: frozenset[int] = frozenset({0, 2, 4, 6, 8, 10, 11, 14, 16, 18, 20, 22, 23})

BIRTH_HOUR_TO_CHI: dict[int, int] = {
    0: 0,    # Tý Sớm (0h-0h59)
    2: 1,    # Sửu (1h-2h59)
    4: 2,    # Dần (3h-4h59)
    6: 3,    # Mão (5h-6h59)
    8: 4,    # Thìn (7h-8h59)
    10: 5,   # Tỵ (9h-10h59)
    11: 6,   # Ngọ (11h-12h59)
    14: 7,   # Mùi (13h-14h59)
    16: 8,   # Thân (15h-16h59)
    18: 9,   # Dậu (17h-18h59)
    20: 10,  # Tuất (19h-20h59)
    22: 11,  # Hợi (21h-22h59)
    23: 0,   # Tý Muộn (23h-23h59) — same calendar day (Tảo Tý phái)
}

BIRTH_HOUR_LABELS: dict[int, str] = {
    0: "Giờ Tý Sớm (0h-0h59)",
    2: "Giờ Sửu (1h-2h59)",
    4: "Giờ Dần (3h-4h59)",
    6: "Giờ Mão (5h-6h59)",
    8: "Giờ Thìn (7h-8h59)",
    10: "Giờ Tỵ (9h-10h59)",
    11: "Giờ Ngọ (11h-12h59)",
    14: "Giờ Mùi (13h-14h59)",
    16: "Giờ Thân (15h-16h59)",
    18: "Giờ Dậu (17h-18h59)",
    20: "Giờ Tuất (19h-20h59)",
    22: "Giờ Hợi (21h-22h59)",
    23: "Giờ Tý Muộn (23h-23h59)",
}

# Hour Can start table: indexed by dayCanIdx % 5
# Giáp/Kỷ → Giáp(0), Ất/Canh → Bính(2), Bính/Tân → Mậu(4),
# Đinh/Nhâm → Canh(6), Mậu/Quý → Nhâm(8)
HOUR_CAN_START: list[int] = [0, 2, 4, 6, 8]


def is_ty_muon(birth_time: int) -> bool:
    """Tý Muộn (23h–23h59). Under Tảo Tý phái, day pillar does NOT shift."""
    return birth_time == 23


# ─────────────────────────────────────────────────────────────────────────────
# Helper to format a GZ object from sxtwl
# ─────────────────────────────────────────────────────────────────────────────

def _gz_to_dict(gz) -> dict:
    """Convert sxtwl GZ object to our standard pillar dict."""
    return {
        "can_idx": gz.tg,
        "chi_idx": gz.dz,
        "can_name": CAN_NAMES[gz.tg],
        "chi_name": CHI_NAMES[gz.dz],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main function: get_tu_tru
# ─────────────────────────────────────────────────────────────────────────────

def get_tu_tru(birth_date: str, birth_time: int) -> dict:
    """
    Compute all 4 pillars for a birth datetime.

    Args:
        birth_date: ISO date string 'YYYY-MM-DD'
        birth_time: integer from dropdown (0,2,4,6,8,10,11,14,16,18,20,22,23)

    Returns:
        dict with keys: year, month, day, hour (each a pillar dict),
        plus nhat_chu (Day Master info)

    Rules:
        - Year Pillar: changes at Lập Xuân (~Feb 4), handled by sxtwl
        - Month Pillar: changes at Tiết Khí boundaries, handled by sxtwl
        - Day Pillar: Tảo Tý phái — NO shift at 23h, day = calendar date
        - Hour Pillar: computed from day Can + hour Chi
    """
    if birth_time not in VALID_BIRTH_HOURS:
        raise ValueError(
            f"birth_time must be one of {sorted(VALID_BIRTH_HOURS)}, got {birth_time}"
        )

    parts = birth_date.split("-")
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])

    # Tảo Tý phái: day boundary at midnight (00:00).
    # 23:00–23:59 stays on the current calendar day — no shift needed.
    sxtwl_day = sxtwl.fromSolar(year, month, day)

    year_pillar = _gz_to_dict(sxtwl_day.getYearGZ())
    month_pillar = _gz_to_dict(sxtwl_day.getMonthGZ())
    day_pillar = _gz_to_dict(sxtwl_day.getDayGZ())

    # Hour pillar: compute from day Can + birth_time clock hour
    hour_chi_idx = BIRTH_HOUR_TO_CHI[birth_time]
    hour_can_start = HOUR_CAN_START[day_pillar["can_idx"] % 5]
    hour_can_idx = (hour_can_start + hour_chi_idx) % 10
    hour_pillar = {
        "can_idx": hour_can_idx,
        "chi_idx": hour_chi_idx,
        "can_name": CAN_NAMES[hour_can_idx],
        "chi_name": CHI_NAMES[hour_chi_idx],
    }

    # Nhật Chủ (Day Master)
    dm_can = day_pillar["can_idx"]
    nhat_chu = {
        "can_idx": dm_can,
        "can_name": CAN_NAMES[dm_can],
        "hanh": CAN_HANH[dm_can],
    }

    return {
        "year": year_pillar,
        "month": month_pillar,
        "day": day_pillar,
        "hour": hour_pillar,
        "nhat_chu": nhat_chu,
        "display": (
            f"{year_pillar['can_name']} {year_pillar['chi_name']} | "
            f"{month_pillar['can_name']} {month_pillar['chi_name']} | "
            f"{day_pillar['can_name']} {day_pillar['chi_name']} | "
            f"{hour_pillar['can_name']} {hour_pillar['chi_name']}"
        ),
    }


def get_tu_tru_optional(birth_date: str, birth_time: Optional[int] = None) -> Optional[dict]:
    """
    Get Tứ Trụ if birth_time is provided, otherwise return None.
    Used for backward compatibility — endpoints can call this and
    fall back to simplified year-only system when birth_time is absent.
    """
    if birth_time is None:
        return None
    return get_tu_tru(birth_date, birth_time)
