"""
GET /v1/day-detail — Single day detailed analysis (Direction C).

Supports personalized (birth required) and generic (anonymous) modes.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.day_score_response import (
    build_generic_day_payload,
    build_luan_context_payload,
    build_personalized_day_payload,
    build_purpose_rows,
    good_and_avoid_from_purpose_rows,
)
from api.schemas.direction_c import (
    validate_day_detail_response,
    validate_luan_context_response,
)
from api.gio_slots import format_gio_tot_slots, format_gio_xau_slots
from api.errors import error_response
from api.intent_rules_loader import get_intent_rule, resolve_intent_key
from api.parse_date import parse_dmy
from calendar_service import get_day_info, get_user_chart
from engine.can_chi import get_can_chi_year
from engine.hoang_dao import get_day_star
from engine.nhi_thap_bat_tu import get_nhi_thap_bat_tu
logger = logging.getLogger("day_detail")

router = APIRouter()

LUNAR_MONTH_NAMES = [
    "", "Giêng", "Hai", "Ba", "Tư", "Năm", "Sáu",
    "Bảy", "Tám", "Chín", "Mười", "Một", "Chạp",
]


def _format_lunar(day_info: dict) -> str:
    lm = day_info["lunar_month"]
    month_name = LUNAR_MONTH_NAMES[lm] if 1 <= lm <= 12 else str(lm)
    year_cc = get_can_chi_year(day_info["lunar_year"])
    return f"Ngày {day_info['lunar_day']} tháng {month_name} năm {year_cc['can_name']} {year_cc['chi_name']}"


def _resolve_intent(intent: str) -> tuple[str, dict]:
    rule_key = resolve_intent_key(intent)
    return rule_key, get_intent_rule(intent)


@router.get("")
@router.get("/", include_in_schema=False)
async def day_detail_endpoint(
    target_date: str = Query(..., alias="date", description="Ngày mục tiêu YYYY-MM-DD"),
    tz: Optional[str] = Query(None, description="IANA timezone, e.g. Asia/Ho_Chi_Minh (default)"),
    mode: Literal["generic", "personalized"] = Query(
        "personalized",
        description="generic = không cần birth; personalized = cá nhân hoá lá số",
    ),
    intent: str = Query("MAC_DINH", description="Mục đích việc (personalized mode)"),
    birth_date: Optional[str] = Query(None, description="Ngày sinh dd/mm/yyyy (bắt buộc nếu personalized)"),
    birth_time: Optional[int] = Query(None),
    gender: Optional[int] = Query(None),
) -> JSONResponse:
    try:
        from api.tz import today_in_tz

        _today = today_in_tz(tz)
        td = date.fromisoformat(target_date)
        td_str = td.isoformat()
        day_info = get_day_info(td_str)
        star_info = get_day_star(day_info["lunar_month"], day_info["day_chi_idx"])
        sao_28 = get_nhi_thap_bat_tu(td.year, td.month, td.day)
        gio_tot = format_gio_tot_slots(day_info["day_chi_idx"])
        gio_xau = format_gio_xau_slots(day_info["day_chi_idx"])
        hung_ngay = day_info.get("hung_ngay", [])

        base = {
            "status": "success",
            "date": td_str,
            "lunar_date": _format_lunar(day_info),
            "lunar_label": _format_lunar(day_info),
            "can_chi": f"{day_info['day_can_name']} {day_info['day_chi_name']}",
            "can_chi_day": f"{day_info['day_can_name']} {day_info['day_chi_name']}",
            "hoang_dao": star_info["is_hoang_dao"],
            "star_name": star_info["star_name"],
            "truc_name": day_info["truc_name"],
            "truc_score": day_info["truc_score"],
            "sao_28": sao_28.get("name", ""),
            "sao_element": sao_28.get("hanh", ""),
            "gio_tot": gio_tot,
            "gio_xau": gio_xau,
            "hung_ngay": [h["name"] if isinstance(h, dict) else str(h) for h in hung_ngay],
        }

        if mode == "generic":
            generic = build_generic_day_payload(
                day_info=day_info,
                user_chart={},
                target=td,
            )
            content = {**base, **generic}
            validate_day_detail_response(content, personalized=False)
            return JSONResponse(status_code=200, content=content)

        if not birth_date:
            return error_response(
                400,
                "INVALID_INPUT",
                message_vi="birth_date bắt buộc khi mode=personalized.",
            )

        bd = parse_dmy(birth_date)
        if bd.year < 1900 or bd >= _today:
            return error_response(400, "INVALID_INPUT", message_vi="birth_date phải là ngày quá khứ.")

        if birth_time is not None:
            from engine.pillars import VALID_BIRTH_HOURS
            if birth_time not in VALID_BIRTH_HOURS:
                return error_response(
                    400,
                    "INVALID_INPUT",
                    message_vi=f"birth_time phải là một trong {sorted(VALID_BIRTH_HOURS)}",
                )

        rule_key, intent_rule = _resolve_intent(intent)
        user_chart = get_user_chart(bd.isoformat(), birth_time, gender)
        purpose_rows = build_purpose_rows(day_info, user_chart)
        good_for, avoid_for = good_and_avoid_from_purpose_rows(purpose_rows)

        payload = build_personalized_day_payload(
            day_info=day_info,
            user_chart=user_chart,
            intent=rule_key,
            intent_rule=intent_rule,
            target=td,
        )

        content = {
            **base,
            **payload,
            "intent": rule_key,
            "good_for": good_for,
            "avoid_for": avoid_for,
            "purpose_rows": purpose_rows,
        }
        validate_day_detail_response(content, personalized=True)
        return JSONResponse(status_code=200, content=content)

    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in day_detail")
        return error_response(500, "INTERNAL_ERROR")


@router.get("/luan-context")
async def day_detail_luan_context(
    target_date: str = Query(..., alias="date", description="Ngày mục tiêu YYYY-MM-DD"),
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: Optional[int] = Query(None),
    gender: Optional[int] = Query(None),
    intent: str = Query("MAC_DINH"),
    tz: Optional[str] = Query(None),
) -> JSONResponse:
    try:
        from api.tz import today_in_tz

        _today = today_in_tz(tz)
        bd = parse_dmy(birth_date)
        if bd.year < 1900 or bd >= _today:
            return error_response(400, "INVALID_INPUT", message_vi="birth_date phải là ngày quá khứ.")

        td = date.fromisoformat(target_date)
        day_info = get_day_info(td.isoformat())
        user_chart = get_user_chart(bd.isoformat(), birth_time, gender)
        rule_key, intent_rule = _resolve_intent(intent)

        content = build_luan_context_payload(
            day_info=day_info,
            user_chart=user_chart,
            intent=rule_key,
            intent_rule=intent_rule,
            target=td,
        )
        full = {"status": "success", **content}
        validate_luan_context_response(full)
        return JSONResponse(status_code=200, content=full)

    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in day_detail luan-context")
        return error_response(500, "INTERNAL_ERROR")
