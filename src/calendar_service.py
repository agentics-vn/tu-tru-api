"""
calendar_service.py — Layer 1 calendar engine facade.

Ported from calendar-service.js.
Composes engine sub-modules into the public API consumed by routes.
"""

from __future__ import annotations

import calendar
from typing import Optional

from engine.can_chi import (
    CAN_NAMES,
    CHI_NAMES,
    DUONG_THAN,
    KY_THAN,
    NAP_AM_HANH,
    NAP_AM_NAMES,
    get_can_chi_day,
    get_can_chi_year,
    get_menh_nap_am,
    get_nap_am_pair_idx,
    is_can_khac,
    is_xung,
)
from engine.lunar import solar_to_lunar
from engine.truc import TRUC_NAMES, TRUC_SCORES, get_truc_idx
from engine.sao_ngay import (
    check_nguyet_duc,
    check_nguyet_duc_hop,
    check_thien_duc,
    check_thien_duc_hop,
    check_thien_xa,
)
from engine.hung_ngay import (
    is_cohon,
    is_duong_cong_ky,
    is_nguyet_ky,
    is_tam_nuong,
)
from engine.pillars import get_tu_tru_optional
from engine.dung_than import find_dung_than
from engine.thap_than import analyze_thap_than
from engine.dai_van import get_current_dai_van
from cache.redis import (
    get_day_info_cached,
    set_day_info_cached,
    get_month_info_cached,
    set_month_info_cached,
)


# ─────────────────────────────────────────────────────────────────────────────
# get_day_info — primary entry point
# ─────────────────────────────────────────────────────────────────────────────

def get_day_info(iso_date: str) -> dict:
    """
    Compute all Layer-1 data for a single solar date.

    Args:
        iso_date: 'YYYY-MM-DD'

    Returns:
        Plain dict — safe to serialize to JSON.
        Keys use snake_case to match Python route expectations.
    """
    # Check cache first
    cached = get_day_info_cached(iso_date)
    if cached is not None:
        return cached

    y, m, d = (int(x) for x in iso_date.split("-"))

    # Lunar
    lunar = solar_to_lunar(iso_date)
    lm = lunar["lunar_month"]
    ld = lunar["lunar_day"]

    # Can Chi Day
    cc = get_can_chi_day(y, m, d)
    can_idx = cc["can_idx"]
    chi_idx = cc["chi_idx"]

    # Nạp Âm of the day
    pair_idx = get_nap_am_pair_idx(can_idx, chi_idx)
    day_nap_am_hanh = NAP_AM_HANH[pair_idx]

    # 12 Trực
    truc_idx = get_truc_idx(chi_idx, lm)
    truc_score = TRUC_SCORES[truc_idx]

    # Sao ngày
    has_thien_duc = check_thien_duc(lm, can_idx, chi_idx)
    has_thien_duc_hop = check_thien_duc_hop(lm, can_idx)
    has_nguyet_duc = check_nguyet_duc(lm, can_idx)
    has_nguyet_duc_hop = check_nguyet_duc_hop(lm, can_idx)
    has_thien_xa = check_thien_xa(lm, can_idx, chi_idx)

    # Hung ngày
    _is_nguyet_ky = is_nguyet_ky(ld)
    _is_tam_nuong = is_tam_nuong(ld)
    _is_duong_cong_ky = is_duong_cong_ky(lm, ld)
    is_truc_pha = truc_idx == 6
    is_truc_nguy = truc_idx == 7

    # Layer 1 pass
    is_layer1_pass = (
        not _is_nguyet_ky
        and not _is_tam_nuong
        and not _is_duong_cong_ky
        and not is_truc_pha
        and not is_truc_nguy
    )

    result = {
        "date": iso_date,
        # Solar
        "solar_day": d,
        "solar_month": m,
        "solar_year": y,
        # Can Chi Day
        "day_can_idx": can_idx,
        "day_chi_idx": chi_idx,
        "day_can_name": cc["can_name"],
        "day_chi_name": cc["chi_name"],
        "day_can_hanh": cc["can_hanh"],
        # Nạp Âm of day
        "day_nap_am_hanh": day_nap_am_hanh,
        # Lunar
        "lunar_day": ld,
        "lunar_month": lm,
        "lunar_year": lunar["lunar_year"],
        "is_leap_month": lunar["is_leap_month"],
        # 12 Trực
        "truc_idx": truc_idx,
        "truc_name": TRUC_NAMES[truc_idx],
        "truc_score": truc_score,
        # Sao ngày
        "has_thien_duc": has_thien_duc,
        "has_thien_duc_hop": has_thien_duc_hop,
        "has_nguyet_duc": has_nguyet_duc,
        "has_nguyet_duc_hop": has_nguyet_duc_hop,
        "has_thien_xa": has_thien_xa,
        # Hung ngày flags
        "is_nguyet_ky": _is_nguyet_ky,
        "is_tam_nuong": _is_tam_nuong,
        "is_duong_cong_ky": _is_duong_cong_ky,
        "is_truc_pha": is_truc_pha,
        "is_truc_nguy": is_truc_nguy,
        # Layer 1 summary
        "is_layer1_pass": is_layer1_pass,
        # Cô Hồn
        "is_cohon": is_cohon(lm),
    }

    # Cache result
    set_day_info_cached(iso_date, result)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# get_month_info
# ─────────────────────────────────────────────────────────────────────────────

def get_month_info(
    year: int, month: int, filter_passed: bool = False
) -> list[dict]:
    """
    Compute Layer 1 data for every day in a solar month.

    Args:
        year: solar year
        month: 1-12
        filter_passed: if True, returns only days that pass Layer 1

    Returns:
        list of day_info dicts
    """
    # Check cache (only for unfiltered results)
    if not filter_passed:
        cached = get_month_info_cached(year, month)
        if cached is not None:
            return cached

    days_in_month = calendar.monthrange(year, month)[1]
    results: list[dict] = []

    for d in range(1, days_in_month + 1):
        iso = f"{year}-{month:02d}-{d:02d}"
        info = get_day_info(iso)
        if not filter_passed or info["is_layer1_pass"]:
            results.append(info)

    # Cache unfiltered month results
    if not filter_passed:
        set_month_info_cached(year, month, results)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# get_user_chart
# ─────────────────────────────────────────────────────────────────────────────

def get_user_chart(
    birth_date: str,
    birth_time: Optional[int] = None,
    gender: Optional[str] = None,
) -> dict:
    """
    Derive personal chart from birth date.

    When birth_time is provided, computes full Tứ Trụ (Four Pillars) with:
    - Dụng Thần (chart-aware favorable element)
    - Thập Thần (Ten Gods profile)
    - Đại Vận (10-year luck cycle, requires gender)

    When birth_time is omitted, falls back to simplified year-only system
    (backward compatible with existing behavior).

    Args:
        birth_date: 'YYYY-MM-DD'
        birth_time: int from dropdown (0,2,4,...,23) or None
        gender: 'male' | 'female' or None

    Returns:
        dict with keys matching what chon_ngay.py consumes.
    """
    y = int(birth_date.split("-")[0])
    year_cc = get_can_chi_year(y)
    menh = get_menh_nap_am(y)

    chart = {
        "birth_year": y,
        "year_can_idx": year_cc["can_idx"],
        "year_chi_idx": year_cc["chi_idx"],
        "year_can_name": year_cc["can_name"],
        "year_chi_name": year_cc["chi_name"],
        "menh_hanh": menh["hanh"],
        "menh_name": menh["name"],
        "duong_than": menh["duong_than"],
        "ky_than": menh["ky_than"],
    }

    # ── Full Tứ Trụ (when birth_time provided) ─────────────────────────
    tu_tru = get_tu_tru_optional(birth_date, birth_time)

    if tu_tru is not None:
        chart["tu_tru"] = tu_tru
        chart["nhat_chu"] = tu_tru["nhat_chu"]

        # Dụng Thần analysis (replaces simplified duong_than/ky_than)
        dung_than_result = find_dung_than(tu_tru)
        chart["dung_than"] = dung_than_result["dung_than"]
        chart["hi_than"] = dung_than_result["hi_than"]
        chart["ky_than_v2"] = dung_than_result["ky_than"]
        chart["cuu_than"] = dung_than_result["cuu_than"]
        chart["chart_strength"] = dung_than_result["strength"]

        # Thập Thần profile
        chart["thap_than"] = analyze_thap_than(tu_tru)

        # Đại Vận (requires gender)
        if gender:
            chart["gender"] = gender
            current_dv = get_current_dai_van(tu_tru, gender, birth_date)
            chart["current_dai_van"] = current_dv

    return chart
