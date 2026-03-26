"""
dai_van.py — Phase 5: Đại Vận (10-Year Luck Cycles / 大运).

Calculates the series of 10-year luck pillars that modulate a person's
overall fortune across their lifetime.

起运 (starting age) uses only the twelve 节 (month-boundary terms), not the
twelve 气 — see docs/algorithm.md §17.
"""

from __future__ import annotations

from datetime import date as dt_date
from datetime import timedelta

from engine.bazi_solar import DEFAULT_TZ, solar_apparent_longitude_deg, solar_term_bucket
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
# Starting age calculation (节 only — not 气)
# ─────────────────────────────────────────────────────────────────────────────

def _term_bucket_on_date(day: dt_date, tz: float = DEFAULT_TZ) -> int:
    lam = solar_apparent_longitude_deg(day.day, day.month, day.year, tz)
    return solar_term_bucket(lam)


def _is_first_calendar_day_of_jie(day: dt_date, tz: float = DEFAULT_TZ) -> bool:
    """
    True if `day` is the first civil day of a new 15° segment that is 节.

    24 terms alternate 节 / 气. With bucket = int((λ mod 360) / 15) % 24,
    节 correspond to odd buckets (立春=21, 惊蛰=23, 清明=1, …), 气 to even.
    """
    prev = day - timedelta(days=1)
    b0 = _term_bucket_on_date(prev, tz)
    b1 = _term_bucket_on_date(day, tz)
    if b0 == b1:
        return False
    return b1 % 2 == 1


def _next_jie_date(birth: dt_date, tz: float = DEFAULT_TZ) -> dt_date | None:
    """Strictly after birth: first 节 boundary day."""
    for delta in range(1, 400):
        d = birth + timedelta(days=delta)
        if _is_first_calendar_day_of_jie(d, tz):
            return d
    return None


def _prev_jie_date(birth: dt_date, tz: float = DEFAULT_TZ) -> dt_date | None:
    """Strictly before birth: nearest prior 节 boundary day."""
    for delta in range(1, 500):
        d = birth - timedelta(days=delta)
        if _is_first_calendar_day_of_jie(d, tz):
            return d
    return None


def _get_start_age(birth_date: str, direction: int) -> float:
    """
    Calculate the starting age of the first Đại Vận (起运岁数).

    Rules:
    - Forward (顺): days from birth to the **next** 节 (exclusive of same-day 节)
    - Backward (逆): days from the **previous** 节 to birth
    - Three days ≈ one year of virtual age → round(days / 3), minimum 1

    Uses solar longitude (lich_hnd); only 节 count — not mid-month 气.
    """
    parts = birth_date.split("-")
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    birth = dt_date(y, m, d)
    tz = DEFAULT_TZ

    if direction == 1:
        nxt = _next_jie_date(birth, tz)
        days_diff = (nxt - birth).days if nxt else 15
    else:
        prv = _prev_jie_date(birth, tz)
        days_diff = (birth - prv).days if prv else 15

    return max(1, round(days_diff / 3))


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

    birth_parts = birth_date.split("-")
    cur_parts = current_date.split("-")
    birth_d = dt_date(
        int(birth_parts[0]), int(birth_parts[1]), int(birth_parts[2])
    )
    cur_d = dt_date(int(cur_parts[0]), int(cur_parts[1]), int(cur_parts[2]))

    age = cur_d.year - birth_d.year
    if (cur_d.month, cur_d.day) < (birth_d.month, birth_d.day):
        age -= 1

    cycles = get_dai_van(tu_tru, gender, birth_date)

    for cycle in cycles:
        if cycle["start_age"] <= age <= cycle["end_age"]:
            return cycle

    return None
