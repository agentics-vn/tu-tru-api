"""
Bazi calendar helpers: Lập Xuân, solar month (Tiết) branches, 24 solar terms.

Built on engine.lich_hnd (Ho Ngoc Duc / Meeus).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from engine.lich_hnd import solar_apparent_longitude_deg

# Vietnam / default local TZ
DEFAULT_TZ = 7.0

# 五虎遁: first month's stem (寅月) from year stem group (year_can % 5)
YIN_MONTH_STEM_START: tuple[int, ...] = (2, 4, 6, 8, 0)  # 丙戊庚壬甲

# Default clock hour (local) for each birth_time dropdown slot
BIRTH_SLOT_HOUR: dict[int, int] = {
    0: 0,
    2: 1,
    4: 3,
    6: 5,
    8: 7,
    10: 9,
    11: 11,
    14: 13,
    16: 15,
    18: 17,
    20: 19,
    22: 21,
    23: 23,
}


def _lichun_date(solar_year: int, tz: float = DEFAULT_TZ) -> date:
    """First calendar day of solar_year where sun longitude ≥ 315° (立春)."""
    d = date(solar_year, 1, 1)
    end = date(solar_year, 3, 20)
    while d <= end:
        lam = solar_apparent_longitude_deg(d.day, d.month, d.year, tz)
        if lam >= 315.0:
            return d
        d += timedelta(days=1)
    raise RuntimeError(f"Could not find Lập Xuân for solar year {solar_year}")


def bazi_cycle_year(y: int, m: int, d: int, tz: float = DEFAULT_TZ) -> int:
    """
    Sexagenary year index for 年柱 (same convention as get_can_chi_year argument).

    Before Lập Xuân of calendar year y → use y-1; on/after → y.
    """
    birth = date(y, m, d)
    if birth < _lichun_date(y, tz):
        return y - 1
    return y


def bazi_month_chi_idx(longitude_deg: float) -> int:
    """
    Địa Chi of the Bazi month (寅卯…) from solar longitude (°).

    Month starts at each 节 (Jie): 立春 315°, 惊蛰 345°, 清明 15°, …
    Note: [345°, 360°) ∪ [0°, 15°) is 卯月 — must be checked before 寅 [315, 345).
    """
    lam = longitude_deg % 360.0
    if lam >= 345.0 or lam < 15.0:
        return 3  # 卯
    if lam < 45.0:
        return 4  # 辰
    if lam < 75.0:
        return 5  # 巳
    if lam < 105.0:
        return 6  # 午
    if lam < 135.0:
        return 7  # 未
    if lam < 165.0:
        return 8  # 申
    if lam < 195.0:
        return 9  # 酉
    if lam < 225.0:
        return 10  # 戌
    if lam < 255.0:
        return 11  # 亥
    if lam < 285.0:
        return 0  # 子
    if lam < 315.0:
        return 1  # 丑
    return 2  # 寅 [315, 345)


def bazi_month_can_idx(year_can_idx: int, month_chi_idx: int) -> int:
    """Thiên Can of month from year stem and month branch (五虎遁)."""
    base = YIN_MONTH_STEM_START[year_can_idx % 5]
    offset = (month_chi_idx - 2 + 12) % 12
    return (base + offset) % 10


def solar_term_bucket(longitude_deg: float) -> int:
    """Index 0..23 of the 24 solar terms (each 15°)."""
    lam = longitude_deg % 360.0
    b = int(lam // 15.0)
    return b % 24


def has_jie_qi(y: int, m: int, d: int, tz: float = DEFAULT_TZ) -> bool:
    """True if local midnight crosses into a new 15° solar-term segment vs previous day."""
    cur = solar_apparent_longitude_deg(d, m, y, tz)
    prev_d = date(y, m, d) - timedelta(days=1)
    prev = solar_apparent_longitude_deg(prev_d.day, prev_d.month, prev_d.year, tz)
    return solar_term_bucket(cur) != solar_term_bucket(prev)


def is_jie_bucket(bucket: int) -> bool:
    """节 (month boundary) terms have odd bucket index in our 0-based scheme."""
    return bucket % 2 == 1


def _longitude_at_local_dt(dt: datetime, tz: float = DEFAULT_TZ) -> float:
    """Solar apparent longitude (deg) at local civil datetime (tz hours east of UTC)."""
    utc_hour = dt.hour - tz + dt.minute / 60.0 + dt.second / 3600.0
    day_frac = utc_hour / 24.0
    d = dt.day + day_frac
    return solar_apparent_longitude_deg(d, dt.month, dt.year, 0.0)


def _next_jie_boundary_deg(lam: float) -> float:
    """Next 节 boundary longitude (odd bucket start) strictly after lam."""
    lam = lam % 360.0
    b = int(lam // 15.0)
    if lam % 15.0 < 1e-9 and is_jie_bucket(b):
        b = (b + 2) % 24
    else:
        b = b + 1 if (lam % 15.0) > 1e-9 else b
        if not is_jie_bucket(b):
            b += 1
    return (b % 24) * 15.0


def _prev_jie_boundary_deg(lam: float) -> float:
    """Previous 节 boundary longitude strictly before lam."""
    lam = lam % 360.0
    b = int(lam // 15.0)
    if lam % 15.0 < 1e-9 and is_jie_bucket(b):
        target_b = (b - 2) % 24
    else:
        target_b = b if is_jie_bucket(b) else b - 1
        if not is_jie_bucket(target_b):
            target_b -= 1
    return (target_b % 24) * 15.0


def _find_bucket_crossing(
    start: datetime,
    target_bucket: int,
    forward: bool,
    tz: float = DEFAULT_TZ,
    max_hours: int = 24 * 90,
) -> datetime:
    """Hour-step search for solar-term bucket boundary."""
    step = timedelta(hours=1 if forward else -1)
    dt = start + step
    for _ in range(max_hours):
        cur_b = solar_term_bucket(_longitude_at_local_dt(dt, tz))
        prev_b = solar_term_bucket(_longitude_at_local_dt(dt - step, tz))
        if forward and prev_b != target_bucket and cur_b == target_bucket:
            return dt
        if not forward and prev_b == target_bucket and cur_b != target_bucket:
            return dt
        dt += step
    raise RuntimeError("Could not find jie boundary within search window")


def next_jie_datetime(
    birth_dt: datetime,
    tz: float = DEFAULT_TZ,
) -> datetime:
    """First 节 instant strictly after birth_dt (local TZ)."""
    lam = _longitude_at_local_dt(birth_dt, tz)
    target_deg = _next_jie_boundary_deg(lam)
    target_bucket = int(target_deg // 15) % 24
    return _find_bucket_crossing(birth_dt, target_bucket, forward=True, tz=tz)


def prev_jie_datetime(
    birth_dt: datetime,
    tz: float = DEFAULT_TZ,
) -> datetime:
    """Last 节 instant strictly before birth_dt."""
    lam = _longitude_at_local_dt(birth_dt, tz)
    target_deg = _prev_jie_boundary_deg(lam)
    target_bucket = int(target_deg // 15) % 24
    return _find_bucket_crossing(birth_dt, target_bucket, forward=False, tz=tz)


def birth_datetime_from_parts(
    iso_date: str,
    birth_time_slot: int,
    birth_minute: int = 0,
    tz: float = DEFAULT_TZ,
) -> datetime:
    """Build local birth datetime from date + dropdown slot."""
    y, m, d = (int(x) for x in iso_date.split("-"))
    hour = BIRTH_SLOT_HOUR.get(birth_time_slot, 12)
    return datetime(y, m, d, hour, birth_minute, 0)


def virtual_days_from_delta(delta: timedelta) -> float:
    """Solar-day span between birth and 节 (fractional days)."""
    return delta.total_seconds() / 86400.0


def add_calendar_offset(
    birth_dt: datetime,
    years: int,
    months: int,
    days: int,
) -> date:
    """Add years/months/days to datetime → date (handles month overflow)."""
    y = birth_dt.year + years
    m = birth_dt.month + months
    while m > 12:
        y += 1
        m -= 12
    while m < 1:
        y -= 1
        m += 12
    day = birth_dt.day + days
    # clamp day to month length
    for _ in range(12):
        try:
            return date(y, m, day)
        except ValueError:
            day -= 1
    return date(y, m, min(day, 28))
