"""
Bazi calendar helpers: Lập Xuân, solar month (Tiết) branches, 24 solar terms.

Built on engine.lich_hnd (Ho Ngoc Duc / Meeus).
"""

from __future__ import annotations

from datetime import date, timedelta

from engine.lich_hnd import solar_apparent_longitude_deg

# Vietnam / default local TZ for tiết calculations (matches lich_hnd defaults)
DEFAULT_TZ = 7.0

# 五虎遁: first month's stem (寅月) from year stem group (year_can % 5)
YIN_MONTH_STEM_START: tuple[int, ...] = (2, 4, 6, 8, 0)  # 丙戊庚壬甲


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
