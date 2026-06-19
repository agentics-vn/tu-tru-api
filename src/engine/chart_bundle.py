"""
chart_bundle.py — Single-pass Tứ Trụ chart analysis (hóa hợp + cường nhược + Thập Thần).

Avoids recomputing detect_stem_transformations() across la_so / tu_tru / dung_than.
"""

from __future__ import annotations

from typing import Any

from engine.chart_contract import merge_chart_contract_into_result
from engine.cung_menh import analyze_cung_menh
from engine.dai_van import get_dai_van_with_dates
from engine.luu_nien_list import build_luu_nien_list
from engine.than_sat import analyze_than_sat
from engine.thap_than import (
    analyze_pho_tinh,
    analyze_tang_can_display,
    analyze_thap_than,
    short_thap_than_label,
)
from engine.tiet_khi_meta import build_calendar_header
from engine.truong_sinh import analyze_truong_sinh
from engine.tuan_khong import analyze_tuan_khong
from engine.can_chi import (
    CAN_HANH,
    CHI_HANH,
    NAP_AM_HANH,
    NAP_AM_NAMES,
    get_nap_am_pair_idx,
)
from engine.hoa_hop import effective_stem_hanh
from engine.pillars import BIRTH_HOUR_LABELS
from engine.cuong_nhuoc import analyze_chart_strength
from engine.dung_than import find_dung_than
from engine.hoa_hop import build_stem_transformations_payload, detect_stem_transformations


def build_chart_analysis(tu_tru: dict) -> dict[str, Any]:
    """
    Compute transforms, strength, dụng thần, thập thần once per request.

    Returns dict with keys: transforms, strength_info, dung_than_info, thap_than,
    stem_transformations (API payload).
    """
    transforms = detect_stem_transformations(tu_tru)
    strength_info = analyze_chart_strength(tu_tru, transforms)
    dung_than_info = find_dung_than(tu_tru, analysis=strength_info)
    thap_than = analyze_thap_than(tu_tru, transforms)
    stem_payload = build_stem_transformations_payload(tu_tru, transforms)
    return {
        "transforms": transforms,
        "strength_info": strength_info,
        "dung_than_info": dung_than_info,
        "thap_than": thap_than,
        "stem_transformations": stem_payload,
    }


def _pillar_surface_thap_than(pillar_key: str, thap_than: dict) -> dict:
    if pillar_key == "day":
        return {"key": "nhat_chu", "name": "NHẬT CHỦ", "short_label": "NHẬT CHỦ"}
    g = thap_than[f"{pillar_key}_god"]
    return {
        "key": g["key"],
        "name": g["name"],
        "short_label": short_thap_than_label(g["key"]),
    }


def _build_pillar_row(
    tu_tru: dict,
    pillar_key: str,
    transforms: list[dict],
    thap_than: dict,
    pho_tinh: dict,
    tang_can: dict,
    truong_sinh: dict,
    than_sat: dict,
) -> dict:
    p = tu_tru[pillar_key]
    pair_idx = get_nap_am_pair_idx(p["can_idx"], p["chi_idx"])
    eff_hanh, transformed = effective_stem_hanh(
        pillar_key, p["can_idx"], transforms,
    )
    return {
        "key": pillar_key,
        "can": {
            "idx": p["can_idx"],
            "name": p["can_name"],
            "hanh": CAN_HANH[p["can_idx"]],
            "effective_hanh": eff_hanh,
            "transformed": transformed,
        },
        "chi": {
            "idx": p["chi_idx"],
            "name": p["chi_name"],
            "hanh": CHI_HANH[p["chi_idx"]],
        },
        "display": f"{p['can_name']} {p['chi_name']}",
        "nap_am": {
            "name": NAP_AM_NAMES[pair_idx],
            "hanh": NAP_AM_HANH[pair_idx],
        },
        "thap_than": _pillar_surface_thap_than(pillar_key, thap_than),
        "tang_can": tang_can[pillar_key],
        "pho_tinh": pho_tinh[pillar_key],
        "truong_sinh": truong_sinh[pillar_key],
        "than_sat": than_sat[pillar_key],
    }


def build_full_chart(
    tu_tru: dict,
    birth_date: str,
    gender: int,
    birth_time_slot: int,
    birth_minute: int = 0,
    name: str | None = None,
    num_dai_van: int = 10,
    num_luu_nien: int = 10,
    view_year: int | None = None,
) -> dict[str, Any]:
    """
    Full Mệnh Bàn Tứ Trụ payload for POST /v1/la-so-full.
    """
    analysis = build_chart_analysis(tu_tru)
    transforms = analysis["transforms"]
    thap_than = analysis["thap_than"]
    pho_tinh = analyze_pho_tinh(tu_tru)
    tang_can = analyze_tang_can_display(tu_tru)
    truong_sinh = analyze_truong_sinh(tu_tru)
    than_sat = analyze_than_sat(tu_tru)
    cung = analyze_cung_menh(tu_tru)
    tuan = analyze_tuan_khong(tu_tru)
    dai_van = get_dai_van_with_dates(
        tu_tru,
        gender,
        birth_date,
        birth_time_slot,
        birth_minute,
        num_dai_van,
    )
    luu_nien = build_luu_nien_list(
        birth_date, num_luu_nien, start_year=view_year,
    )
    if view_year is not None:
        for row in luu_nien:
            row["selected"] = row["year"] == view_year
    header = build_calendar_header(
        birth_date,
        tu_tru["month"]["chi_name"],
        BIRTH_HOUR_LABELS.get(birth_time_slot),
        birth_time_slot=birth_time_slot,
        birth_minute=birth_minute,
    )
    gender_label = "Dương Càn tạo" if gender == 1 else "Âm Khôn tạo"

    pillars = {
        pk: _build_pillar_row(
            tu_tru, pk, transforms, thap_than, pho_tinh, tang_can,
            truong_sinh, than_sat,
        )
        for pk in ("year", "month", "day", "hour")
    }

    result: dict[str, Any] = {
        "tu_tru_display": tu_tru["display"],
        "nhat_chu": tu_tru["nhat_chu"],
        "header": {
            **header,
            "name": name,
            "gender": gender,
            "gender_label": gender_label,
            "khoi_van_date": dai_van["khoi_van_date"],
        },
        "pillars": pillars,
        "dai_van": dai_van,
        "luu_nien": luu_nien,
        "menh_cung": cung["menh_cung"],
        "thai_nguyen": cung["thai_nguyen"],
        "tuan_khong": tuan,
        "chart_analysis": {
            "stem_transformations": analysis["stem_transformations"],
            "strength_info": analysis["strength_info"],
            "dung_than_info": analysis["dung_than_info"],
            "thap_than": analysis["thap_than"],
        },
    }
    # Lazy import avoids chart_bundle ↔ la_so cycle
    from engine.la_so import build_la_so_chart_contract

    chart_contract = build_la_so_chart_contract(tu_tru, gender, birth_date)
    merge_chart_contract_into_result(result, chart_contract)
    return result
