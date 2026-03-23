"""
dai_van.py — Phase 5: Đại Vận (10-Year Luck Cycles / 大运).

Calculates the series of 10-year luck pillars that modulate a person's
overall fortune across their lifetime.

Source of truth: docs/algorithm.md §21
"""

from __future__ import annotations

from datetime import date as dt_date
from datetime import timedelta

from engine.bazi_solar import DEFAULT_TZ, has_jie_qi
from engine.can_chi import CAN_NAMES, CHI_NAMES, CAN_HANH, NAP_AM_HANH, get_nap_am_pair_idx

# ─────────────────────────────────────────────────────────────────────────────
# Direction rule
# ─────────────────────────────────────────────────────────────────────────────

def _is_yang_stem(can_idx: int) -> bool:
    """Dương (Yang) stems: Giáp(0), Bính(2), Mậu(4), Canh(6), Nhâm(8)."""
    return can_idx % 2 == 0


def get_dai_van_direction(year_can_idx: int, gender: int) -> int:
    """
    Determine forward (+1) or backward (-1) counting direction.

    Rules:
    - Male (1) + Dương year stem → forward
    - Male + Âm year stem → backward
    - Female (-1) → opposite of male

    Args:
        year_can_idx: 0-9
        gender: 1 (male) or -1 (female)
    """
    is_yang = _is_yang_stem(year_can_idx)

    if gender == 1:
        return 1 if is_yang else -1
    else:
        return -1 if is_yang else 1


# ─────────────────────────────────────────────────────────────────────────────
# Starting age calculation
# ─────────────────────────────────────────────────────────────────────────────

def _get_start_age(birth_date: str, direction: int) -> float:
    """
    Calculate the starting age of the first Đại Vận.

    Rules:
    - Forward direction: count days from birth to NEXT Tiết Khí (solar term)
    - Backward direction: count days from PREVIOUS Tiết Khí to birth
    - Divide by 3 = starting age (in years)
    - Round to nearest integer, minimum 1

    Uses lich_hnd-based solar longitude (24 tiết, 15° steps).
    """
    parts = birth_date.split("-")
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])

    birth = dt_date(y, m, d)
    tz = DEFAULT_TZ

    prev_jq_date = None
    next_jq_date = None

    for delta in range(-45, 46):
        try:
            check_date = birth + timedelta(days=delta)
        except OverflowError:
            continue

        if has_jie_qi(check_date.year, check_date.month, check_date.day, tz):
            jq_date = check_date
            if jq_date < birth:
                prev_jq_date = jq_date
            elif jq_date > birth:
                if next_jq_date is None:
                    next_jq_date = jq_date
            # Birth date itself on a Jie Qi
            elif jq_date == birth:
                if direction == 1:
                    # Forward: this counts as 0 days to next term
                    # But we should find the NEXT term after this one
                    continue
                else:
                    prev_jq_date = jq_date

    if direction == 1:
        # Forward: days from birth to next Jie Qi
        if next_jq_date:
            days_diff = (next_jq_date - birth).days
        else:
            days_diff = 15  # fallback
    else:
        # Backward: days from previous Jie Qi to birth
        if prev_jq_date:
            days_diff = (birth - prev_jq_date).days
        else:
            days_diff = 15  # fallback

    # Divide by 3, round to nearest integer, minimum 1
    start_age = max(1, round(days_diff / 3))
    return start_age


# ─────────────────────────────────────────────────────────────────────────────
# Đại Vận cycle generation
# ─────────────────────────────────────────────────────────────────────────────

def get_dai_van(
    tu_tru: dict,
    gender: int,
    birth_date: str,
    num_cycles: int = 8,
) -> list[dict]:
    """
    Calculate 10-year luck pillars.

    Starting from the month pillar, count forward or backward through
    the 60 Jiazi cycle to derive each Đại Vận pillar.

    Args:
        tu_tru: from get_tu_tru()
        gender: 1 (male) | -1 (female)
        birth_date: ISO date string
        num_cycles: how many 10-year cycles to compute (default 8 = 80 years)

    Returns:
        list of dicts: [{start_age, end_age, can_idx, chi_idx, can_name,
                         chi_name, nap_am_hanh, thap_than_key}]
    """
    year_can_idx = tu_tru["year"]["can_idx"]
    month_can_idx = tu_tru["month"]["can_idx"]
    month_chi_idx = tu_tru["month"]["chi_idx"]

    direction = get_dai_van_direction(year_can_idx, gender)
    start_age = _get_start_age(birth_date, direction)

    cycles: list[dict] = []

    for i in range(1, num_cycles + 1):
        # Each cycle is 1 step forward/backward from month pillar in the 60 Jiazi
        can_idx = (month_can_idx + direction * i) % 10
        chi_idx = (month_chi_idx + direction * i) % 12

        cycle_start_age = start_age + (i - 1) * 10
        cycle_end_age = cycle_start_age + 9

        pair_idx = get_nap_am_pair_idx(can_idx, chi_idx)

        cycles.append({
            "cycle_num": i,
            "start_age": cycle_start_age,
            "end_age": cycle_end_age,
            "can_idx": can_idx,
            "chi_idx": chi_idx,
            "can_name": CAN_NAMES[can_idx],
            "chi_name": CHI_NAMES[chi_idx],
            "display": f"{CAN_NAMES[can_idx]} {CHI_NAMES[chi_idx]}",
            "nap_am_hanh": NAP_AM_HANH[pair_idx],
            "can_hanh": CAN_HANH[can_idx],
        })

    return cycles


def get_current_dai_van(
    tu_tru: dict,
    gender: int,
    birth_date: str,
    current_date: str | None = None,
) -> dict | None:
    """
    Find the current active Đại Vận cycle.

    Args:
        tu_tru: from get_tu_tru()
        gender: 1 (male) | -1 (female)
        birth_date: ISO date string
        current_date: ISO date string (default: today)

    Returns:
        The current cycle dict, or None if age is before first cycle
    """
    if current_date is None:
        current_date = dt_date.today().isoformat()

    # Calculate current age
    birth_parts = birth_date.split("-")
    birth_y = int(birth_parts[0])
    cur_parts = current_date.split("-")
    cur_y = int(cur_parts[0])
    cur_m = int(cur_parts[1])
    birth_m = int(birth_parts[1])

    # Approximate age
    age = cur_y - birth_y
    if cur_m < birth_m:
        age -= 1

    cycles = get_dai_van(tu_tru, gender, birth_date)

    for cycle in cycles:
        if cycle["start_age"] <= age <= cycle["end_age"]:
            return cycle

    return None
