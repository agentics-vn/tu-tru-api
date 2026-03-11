"""
lunar.py — Solar-to-Lunar date conversion.

Ported from calendar-service.js solarToLunar().
Uses the ``lunardate`` Python package as the conversion backend.

Install: pip install lunardate
"""

from __future__ import annotations

import lunardate


def solar_to_lunar(iso_date: str) -> dict:
    """
    Convert ISO solar date string to lunar date components.

    Args:
        iso_date: 'YYYY-MM-DD'

    Returns:
        dict with keys: lunar_day, lunar_month, lunar_year, is_leap_month
    """
    y, m, d = (int(x) for x in iso_date.split("-"))
    ld = lunardate.LunarDate.fromSolarDate(y, m, d)
    return {
        "lunar_day": ld.day,
        "lunar_month": ld.month,
        "lunar_year": ld.year,
        "is_leap_month": ld.isLeapMonth,
    }
