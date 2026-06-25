"""
tiet_khi_meta.py — Solar term name and calendar header metadata.

Source: docs/algorithm.md §22.9, docs/seed/tiet-khi.json
"""

from __future__ import annotations

from datetime import datetime

from engine.bazi_solar import (
    BIRTH_SLOT_HOUR,
    DEFAULT_TZ,
    _longitude_at_local_dt,
    solar_apparent_longitude_deg,
    solar_term_bucket,
)
from engine.lunar import solar_to_lunar
from engine.seed_loader import load_seed_json

# Loại tiết khí (节/气) bằng tiếng Việt cho output API.
_TIET_KHI_LOAI_VI: dict[str, str] = {"tiet": "Tiết", "khi": "Khí"}


def get_tiet_khi_at_date(
    year: int,
    month: int,
    day: int,
    hour: int | None = None,
    minute: int = 0,
    tz: float = DEFAULT_TZ,
) -> dict:
    # Time-aware when an hour is given: a term that begins on the birth day only
    # counts once its exact instant has passed (e.g. 21/3/1990 05:15 → Xuân Phân).
    if hour is None:
        lam = solar_apparent_longitude_deg(day, month, year, tz)
    else:
        lam = _longitude_at_local_dt(datetime(year, month, day, hour, minute), tz)
    bucket = solar_term_bucket(lam)
    data = load_seed_json("tiet-khi.json")
    idx = (bucket - 21) % 24
    entry = data["data"][idx]
    return {
        "key": entry["key"],
        "name": entry["name"],
        "loai": _TIET_KHI_LOAI_VI.get(entry["type"], entry["type"]),
        "bucket": bucket,
        "longitude_deg": round(lam % 360, 3),
    }


def get_am_lich(iso_date: str) -> dict:
    lunar = solar_to_lunar(iso_date)
    return {
        "day": lunar["lunar_day"],
        "month": lunar["lunar_month"],
        "year": lunar["lunar_year"],
        "is_leap_month": lunar["is_leap_month"],
        "display": f"{lunar['lunar_day']}/{lunar['lunar_month']}/{lunar['lunar_year']}",
    }


def build_calendar_header(
    iso_date: str,
    nguyet_lenh_chi: str,
    birth_time_label: str | None = None,
    birth_time_slot: int | None = None,
    birth_minute: int = 0,
    tz: float = DEFAULT_TZ,
) -> dict:
    parts = iso_date.split("-")
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    hour = (
        BIRTH_SLOT_HOUR.get(birth_time_slot, 12)
        if birth_time_slot is not None
        else None
    )
    tiet = get_tiet_khi_at_date(y, m, d, hour, birth_minute, tz)
    am = get_am_lich(iso_date)
    header = {
        "duong_lich": iso_date,
        "duong_lich_display": _format_solar_display(
            y, m, d, birth_time_slot, birth_minute, tz,
        ),
        "am_lich": am,
        "tiet_khi": tiet,
        "nguyet_lenh": nguyet_lenh_chi,
    }
    if birth_time_label:
        header["birth_time_label"] = birth_time_label
    return header


def _format_solar_display(
    year: int,
    month: int,
    day: int,
    birth_time_slot: int | None,
    birth_minute: int,
    tz: float,
) -> str:
    """e.g. '19/6/2026 - 9:57 (GMT+7)'. Hour from the slot's starting clock hour."""
    base = f"{day}/{month}/{year}"
    gmt = f"GMT{'+' if tz >= 0 else '-'}{int(abs(tz))}"
    if birth_time_slot is None:
        return f"{base} ({gmt})"
    hour = BIRTH_SLOT_HOUR.get(birth_time_slot, 12)
    return f"{base} - {hour}:{birth_minute:02d} ({gmt})"
