"""
GET /v1/ngay-hom-nay — Today's auspicious card endpoint.

Returns the full astrology card for a given date (defaults to today),
including hoàng đạo/hắc đạo badge, giờ tốt/xấu, and daily advice.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.parse_date import parse_dmy
from calendar_service import get_day_info, get_user_chart, get_can_chi_year
from engine.hoang_dao import get_day_star, get_gio_hoang_dao, get_gio_hac_dao
from engine.can_chi import CAN_NAMES, CHI_NAMES, NAP_AM_NAMES, get_can_chi_day, get_nap_am_pair_idx
from filter import apply_layer2_filter

logger = logging.getLogger("ngay_hom_nay")

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Load intent rules
# ─────────────────────────────────────────────────────────────────────────────

_INTENT_RULES_PATH = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "seed" / "intent-rules.json"
with open(_INTENT_RULES_PATH, encoding="utf-8") as f:
    INTENT_RULES: dict = json.load(f)

LUNAR_MONTH_NAMES = [
    "", "Giêng", "Hai", "Ba", "Tư", "Năm", "Sáu",
    "Bảy", "Tám", "Chín", "Mười", "Một", "Chạp",
]

# Intents to check for good_for / avoid_for
_INTENT_KEYS = [
    k for k in INTENT_RULES if not k.startswith("_") and k != "MAC_DINH"
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _format_lunar_display(day_info: dict) -> str:
    lm = day_info["lunar_month"]
    month_name = LUNAR_MONTH_NAMES[lm] if 1 <= lm <= 12 else str(lm)
    year_cc = get_can_chi_year(day_info["lunar_year"])
    return (
        f"Ngày {day_info['lunar_day']} tháng {month_name} "
        f"năm {year_cc['can_name']} {year_cc['chi_name']}"
    )


def _build_tu_tru_section(day_info: dict, user_chart: dict) -> dict:
    """Build optional Tứ Trụ section for the response (only when birth_time provided)."""
    result: dict = {}

    if user_chart.get("tu_tru"):
        tu_tru = user_chart["tu_tru"]
        result["bat_tu"] = {
            "tu_tru_display": tu_tru["display"],
            "nhat_chu": {
                "can_name": tu_tru["nhat_chu"]["can_name"],
                "hanh": tu_tru["nhat_chu"]["hanh"],
            },
            "dung_than": user_chart.get("dung_than"),
            "chart_strength": user_chart.get("chart_strength"),
        }

        # Show the day's Ten God relationship to user's Day Master
        if user_chart.get("nhat_chu"):
            from engine.thap_than import get_thap_than
            dm_can = user_chart["nhat_chu"]["can_idx"]
            day_god = get_thap_than(dm_can, day_info["day_can_idx"])
            result["bat_tu"]["day_thap_than"] = day_god["name"]

        # Đại Vận context
        if user_chart.get("current_dai_van"):
            dv = user_chart["current_dai_van"]
            result["bat_tu"]["dai_van"] = {
                "display": dv["display"],
                "hanh": dv["can_hanh"],
                "age_range": f"{dv['start_age']}-{dv['end_age']}",
            }

    return result


def _get_good_and_avoid(day_info: dict, user_chart: dict) -> tuple[list[str], list[str]]:
    """
    Determine what this day is good/bad for based on truc and layer-2 compatibility.

    Returns (good_for, avoid_for) — lists of Vietnamese intent labels.
    """
    good_for: list[str] = []
    avoid_for: list[str] = []
    truc_idx = day_info["truc_idx"]

    for intent_key in _INTENT_KEYS:
        rule = INTENT_RULES[intent_key]
        label = rule.get("_label_vi", intent_key)
        # Extract short label (before /)
        short_label = label.split("/")[0].strip()

        preferred = rule.get("preferred_truc", [])
        forbidden = rule.get("forbidden_truc", [])

        # Check layer 2 (xung, khắc) for this intent
        l2 = apply_layer2_filter(day_info, user_chart, intent_key)

        if l2["severity"] == 3:
            # Absolute avoid
            avoid_for.append(short_label)
        elif truc_idx in forbidden:
            avoid_for.append(short_label)
        elif truc_idx in preferred and l2["pass"]:
            good_for.append(short_label)

    return good_for, avoid_for


def _build_daily_advice(day_info: dict, star_info: dict, good_for: list[str], avoid_for: list[str]) -> dict:
    """Generate simple daily advice based on the day's characteristics."""
    nen_lam_parts: list[str] = []
    nen_tranh_parts: list[str] = []

    # Star-based advice
    if star_info["is_hoang_dao"]:
        nen_lam_parts.append(
            f"Ngày Hoàng Đạo ({star_info['star_name']}) — thuận lợi cho nhiều việc"
        )
    else:
        nen_tranh_parts.append(
            f"Ngày Hắc Đạo ({star_info['star_name']}) — nên cẩn trọng"
        )

    # Truc-based advice
    truc_score = day_info["truc_score"]
    if truc_score >= 2:
        nen_lam_parts.append(f"Trực {day_info['truc_name']} — ngày đẹp")
    elif truc_score < 0:
        nen_tranh_parts.append(f"Trực {day_info['truc_name']} — không tốt")

    # Good/avoid summary
    if good_for:
        nen_lam_parts.append("Phù hợp: " + ", ".join(good_for[:5]))
    if avoid_for:
        nen_tranh_parts.append("Nên tránh: " + ", ".join(avoid_for[:5]))

    return {
        "nen_lam": ". ".join(nen_lam_parts) if nen_lam_parts else "Không có gì đặc biệt.",
        "nen_tranh": ". ".join(nen_tranh_parts) if nen_tranh_parts else "Không có gì đặc biệt.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/ngay-hom-nay
# ─────────────────────────────────────────────────────────────────────────────

@router.get("")
@router.get("/")
async def ngay_hom_nay(
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: Optional[int] = Query(None, description="Giờ sinh: 0,2,4,6,8,10,11,14,16,18,20,22,23"),
    gender: Optional[int] = Query(None, description="Giới tính: 1 (nam) hoặc -1 (nữ)"),
    target_date: Optional[str] = Query(None, alias="date", description="Ngày mục tiêu YYYY-MM-DD (mặc định: hôm nay)"),
) -> JSONResponse:
    try:
        # Parse and validate birth_date (dd/mm/yyyy)
        bd = parse_dmy(birth_date)
        if bd.year < 1900 or bd >= date.today():
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error_code": "INVALID_INPUT",
                    "message": "birth_date phải là ngày quá khứ (năm >= 1900).",
                },
            )

        # Target date
        td = date.fromisoformat(target_date) if target_date else date.today()
        td_str = td.isoformat()

        # Validate birth_time if provided
        if birth_time is not None:
            from engine.pillars import VALID_BIRTH_HOURS
            if birth_time not in VALID_BIRTH_HOURS:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "error_code": "INVALID_INPUT",
                        "message": f"birth_time phải là một trong {sorted(VALID_BIRTH_HOURS)}",
                    },
                )

        # ── Engine calls ────────────────────────────────────────────────
        day_info = get_day_info(td_str)
        user_chart = get_user_chart(bd.isoformat(), birth_time, gender)
        star_info = get_day_star(day_info["lunar_month"], day_info["day_chi_idx"])

        # Giờ tốt / xấu
        gio_tot = get_gio_hoang_dao(day_info["day_chi_idx"])
        gio_xau = get_gio_hac_dao(day_info["day_chi_idx"])

        # Nạp Âm name for the day
        pair_idx = get_nap_am_pair_idx(day_info["day_can_idx"], day_info["day_chi_idx"])

        # Good for / avoid for
        good_for, avoid_for = _get_good_and_avoid(day_info, user_chart)

        # Daily advice
        advice = _build_daily_advice(day_info, star_info, good_for, avoid_for)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "date": td_str,
                "can_chi": {
                    "name": f"{day_info['day_can_name']} {day_info['day_chi_name']}",
                    "can_name": day_info["day_can_name"],
                    "chi_name": day_info["day_chi_name"],
                    "nap_am_hanh": day_info["day_nap_am_hanh"],
                },
                "lunar": {
                    "day": day_info["lunar_day"],
                    "month": day_info["lunar_month"],
                    "year": day_info["lunar_year"],
                    "display": _format_lunar_display(day_info),
                },
                "hoang_dao": {
                    "is_hoang_dao": star_info["is_hoang_dao"],
                    "star_name": star_info["star_name"],
                    "badge": "HOÀNG ĐẠO" if star_info["is_hoang_dao"] else "HẮC ĐẠO",
                },
                "truc": {
                    "name": day_info["truc_name"],
                    "score": day_info["truc_score"],
                },
                "good_for": good_for,
                "avoid_for": avoid_for,
                "gio_tot": [
                    {"chi_name": g["chi_name"], "range": f"{g['start']}-{g['end']}"}
                    for g in gio_tot
                ],
                "gio_xau": [
                    {"chi_name": g["chi_name"], "range": f"{g['start']}-{g['end']}"}
                    for g in gio_xau
                ],
                "daily_advice": advice,
                **(_build_tu_tru_section(day_info, user_chart)),
            },
        )

    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_code": "INVALID_INPUT",
                "message": str(e),
            },
        )
    except Exception:
        logger.exception("Internal error in ngay_hom_nay")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": "Đã có lỗi xảy ra. Vui lòng thử lại sau.",
            },
        )
