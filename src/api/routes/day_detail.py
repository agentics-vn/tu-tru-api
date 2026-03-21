"""
GET /v1/day-detail — Single day detailed analysis.

Returns the full astrological breakdown for a specific date,
personalized to the user's birth chart. Used by the So Sanh (compare) feature.
"""

from __future__ import annotations

import json

from api.errors import error_response
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.parse_date import parse_dmy
from calendar_service import get_day_info, get_user_chart
from engine.hoang_dao import get_day_star, get_gio_hoang_dao, get_gio_hac_dao
from engine.can_chi import get_can_chi_year
from engine.nhi_thap_bat_tu import get_nhi_thap_bat_tu
from filter import apply_layer2_filter
from scoring import compute_score_breakdown, GRADE_THRESHOLDS

logger = logging.getLogger("day_detail")

router = APIRouter()


# Load intent rules for good_for / avoid_for
_INTENT_RULES_PATH = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "seed" / "intent-rules.json"
with open(_INTENT_RULES_PATH, encoding="utf-8") as f:
    INTENT_RULES: dict = json.load(f)

_INTENT_KEYS = [k for k in INTENT_RULES if not k.startswith("_") and k != "MAC_DINH"]

LUNAR_MONTH_NAMES = [
    "", "Giêng", "Hai", "Ba", "Tư", "Năm", "Sáu",
    "Bảy", "Tám", "Chín", "Mười", "Một", "Chạp",
]


def _format_lunar(day_info: dict) -> str:
    lm = day_info["lunar_month"]
    month_name = LUNAR_MONTH_NAMES[lm] if 1 <= lm <= 12 else str(lm)
    year_cc = get_can_chi_year(day_info["lunar_year"])
    return f"Ngày {day_info['lunar_day']} tháng {month_name} năm {year_cc['can_name']} {year_cc['chi_name']}"


def _get_good_and_avoid(day_info: dict, user_chart: dict) -> tuple[list[str], list[str]]:
    """Determine what this day is good/bad for."""
    good_for: list[str] = []
    avoid_for: list[str] = []
    truc_idx = day_info["truc_idx"]

    for intent_key in _INTENT_KEYS:
        rule = INTENT_RULES[intent_key]
        label = rule.get("_label_vi", intent_key)
        short_label = label.split("/")[0].strip()

        preferred = rule.get("preferred_truc", [])
        forbidden = rule.get("forbidden_truc", [])

        l2 = apply_layer2_filter(day_info, user_chart, intent_key)

        if l2["severity"] == 3:
            avoid_for.append(short_label)
        elif truc_idx in forbidden:
            avoid_for.append(short_label)
        elif truc_idx in preferred and l2["pass"]:
            good_for.append(short_label)

    return good_for, avoid_for


@router.get("")
@router.get("/")
async def day_detail_endpoint(
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: Optional[int] = Query(None),
    gender: Optional[int] = Query(None),
    target_date: str = Query(..., alias="date", description="Ngày mục tiêu YYYY-MM-DD"),
) -> JSONResponse:
    try:
        bd = parse_dmy(birth_date)
        if bd.year < 1900 or bd >= date.today():
            return error_response(400, "INVALID_INPUT", message_vi="birth_date phải là ngày quá khứ.")

        if birth_time is not None:
            from engine.pillars import VALID_BIRTH_HOURS
            if birth_time not in VALID_BIRTH_HOURS:
                return error_response(400, "INVALID_INPUT", message_vi=f"birth_time phải là một trong {sorted(VALID_BIRTH_HOURS)}")

        td = date.fromisoformat(target_date)
        td_str = td.isoformat()

        day_info = get_day_info(td_str)
        user_chart = get_user_chart(bd.isoformat(), birth_time, gender)
        star_info = get_day_star(day_info["lunar_month"], day_info["day_chi_idx"])

        gio_tot = get_gio_hoang_dao(day_info["day_chi_idx"])
        gio_xau = get_gio_hac_dao(day_info["day_chi_idx"])

        good_for, avoid_for = _get_good_and_avoid(day_info, user_chart)

        # Sao 28 Tú — compute from solar date
        sao_28 = get_nhi_thap_bat_tu(td.year, td.month, td.day)
        sao_name = sao_28.get("name", "")
        sao_element = sao_28.get("hanh", "")

        # Hung ngay
        hung_ngay = day_info.get("hung_ngay", [])

        # Compute score using standard engine (MAC_DINH intent for general overview)
        intent = "MAC_DINH"
        intent_rule = INTENT_RULES.get(intent, {})
        l2 = apply_layer2_filter(day_info, user_chart, intent)
        scoring_result = compute_score_breakdown(day_info, user_chart, intent, intent_rule, l2)
        score = scoring_result["score"]
        grade = scoring_result["grade"]

        reason_parts = []
        if star_info["is_hoang_dao"]:
            reason_parts.append(f"Hoàng Đạo ({star_info['star_name']})")
        else:
            reason_parts.append(f"Hắc Đạo ({star_info['star_name']})")
        reason_parts.append(f"Trực {day_info['truc_name']}")
        if sao_name:
            reason_parts.append(f"Sao {sao_name}")
        reason = " — ".join(reason_parts)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "date": td_str,
                "lunar_date": _format_lunar(day_info),
                "can_chi": f"{day_info['day_can_name']} {day_info['day_chi_name']}",
                "hoang_dao": star_info["is_hoang_dao"],
                "star_name": star_info["star_name"],
                "truc_name": day_info["truc_name"],
                "truc_score": day_info["truc_score"],
                "sao_28": sao_name,
                "sao_element": sao_element,
                "score": score,
                "grade": grade,
                "good_for": good_for,
                "avoid_for": avoid_for,
                "gio_tot": [f"{g['chi_name']} ({g['start']}-{g['end']})" for g in gio_tot],
                "gio_xau": [f"{g['chi_name']} ({g['start']}-{g['end']})" for g in gio_xau],
                "reason_vi": reason,
                "breakdown": scoring_result.get("breakdown", []),
                "hung_ngay": [h["name"] if isinstance(h, dict) else str(h) for h in hung_ngay],
            },
        )

    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in day_detail")
        return error_response(500, "INTERNAL_ERROR")
