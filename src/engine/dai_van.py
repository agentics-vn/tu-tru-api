"""
dai_van.py — Phase 5: Đại Vận (10-Year Luck Cycles / 大运).

Calculates the series of 10-year luck pillars that modulate a person's
overall fortune across their lifetime.

起运 (starting age) uses only the twelve 节 (month-boundary terms), not the
twelve 气 — see docs/algorithm.md §17.
"""

from __future__ import annotations

import math
from datetime import date as dt_date
from datetime import datetime, timedelta

from engine.bazi_solar import (
    DEFAULT_TZ,
    birth_datetime_from_parts,
    next_jie_datetime,
    prev_jie_datetime,
    solar_apparent_longitude_deg,
    solar_term_bucket,
    virtual_days_from_delta,
)
from engine.can_chi import CAN_NAMES, CHI_NAMES, CAN_HANH, NAP_AM_HANH, get_nap_am_pair_idx

# ─────────────────────────────────────────────────────────────────────────────
# Direction rule
# ─────────────────────────────────────────────────────────────────────────────

# Mean tropical year (days). Maps the "3 ngày = 1 năm" 节 gap onto the real
# calendar so 起运 lands on the exact day (§22.3).
TROPICAL_YEAR_DAYS = 365.2422


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

    return max(1, math.ceil(days_diff / 3))


def compute_khoi_van(
    birth_date: str,
    direction: int,
    birth_time_slot: int | None = None,
    birth_minute: int = 0,
    tz: float = DEFAULT_TZ,
) -> dict:
    """
    Compute 起运 date with hour/minute precision (§22.3).

    Returns: virtual_days, start_age, khoi_van_date (ISO), jie_datetime (ISO)
    """
    parts = birth_date.split("-")
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    if birth_time_slot is not None:
        birth_dt = birth_datetime_from_parts(
            birth_date, birth_time_slot, birth_minute, tz,
        )
    else:
        birth_dt = datetime(y, m, d, 12, 0, 0)

    if direction == 1:
        jie_dt = next_jie_datetime(birth_dt, tz)
        delta = jie_dt - birth_dt
    else:
        jie_dt = prev_jie_datetime(birth_dt, tz)
        delta = birth_dt - jie_dt

    solar_days = virtual_days_from_delta(delta)
    birth_d = birth_dt.date()
    if direction == 1:
        civil_end = _next_jie_date(birth_d, tz) or jie_dt.date()
        civil_days = (civil_end - birth_d).days
    else:
        civil_start = _prev_jie_date(birth_d, tz) or jie_dt.date()
        civil_days = (birth_d - civil_start).days
    start_age = max(1, math.ceil(civil_days / 3))

    # Exact 起运 day: scale the (time-aware) 节 gap by 3 days ≈ 1 năm onto the
    # real calendar. Matches tuvivietnam to the day (golden 13/6/2032).
    khoi_dt = birth_dt + timedelta(days=solar_days / 3.0 * TROPICAL_YEAR_DAYS)
    khoi_date = khoi_dt.date()

    return {
        "virtual_days": round(solar_days, 4),
        "civil_days_to_jie": civil_days,
        "start_age": start_age,
        "khoi_van_date": khoi_date.isoformat(),
        "jie_datetime": jie_dt.isoformat(sep=" ", timespec="minutes"),
        "direction": direction,
    }


def get_dai_van_with_dates(
    tu_tru: dict,
    gender: int,
    birth_date: str,
    birth_time_slot: int | None = None,
    birth_minute: int = 0,
    num_cycles: int = 10,
) -> dict:
    """Đại vận cycles with khoi_van_date and start_year per cycle."""
    year_can_idx = tu_tru["year"]["can_idx"]
    direction = get_dai_van_direction(year_can_idx, gender)
    khoi = compute_khoi_van(
        birth_date, direction, birth_time_slot, birth_minute,
    )
    start_age = khoi["start_age"]
    cycles_raw = get_dai_van(
        tu_tru, gender, birth_date, num_cycles, start_age=start_age,
    )
    birth_y = int(birth_date.split("-")[0])
    cycles = []
    for c in cycles_raw:
        # c["start_age"] already includes the per-cycle +10 offset.
        start_year = birth_y + c["start_age"] - 1
        cycles.append({
            **c,
            "start_year": start_year,
            "age_label": f"{c['start_age']}-{c['end_age']}t",
        })
    return {
        "direction": "thuận" if direction == 1 else "nghịch",
        "direction_step": direction,
        **khoi,
        "cycles": cycles,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Đại Vận cycle generation
# ─────────────────────────────────────────────────────────────────────────────

def get_dai_van(
    tu_tru: dict,
    gender: int,
    birth_date: str,
    num_cycles: int = 8,
    start_age: int | None = None,
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
    if start_age is None:
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


def get_next_dai_van(
    tu_tru: dict,
    gender: int,
    birth_date: str,
    current_date: str | None = None,
) -> dict | None:
    """Return the Đại Vận cycle after the active one (or first cycle if not yet started)."""
    cycles = get_dai_van(tu_tru, gender, birth_date)
    if not cycles:
        return None

    current = get_current_dai_van(tu_tru, gender, birth_date, current_date)
    if current is None:
        return cycles[0]

    next_num = current["cycle_num"] + 1
    for cycle in cycles:
        if cycle["cycle_num"] == next_num:
            return cycle
    return None
