"""
GET /v1/day-compare — Compare two dates for the same birth profile (Direction C).
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.day_score_response import score_day_context
from api.errors import error_response
from api.intent_rules_loader import get_intent_rule, resolve_intent_key
from api.parse_date import parse_dmy
from calendar_service import get_day_info, get_user_chart
from engine.day_score import build_compare_copy
from api.schemas.direction_c import (
    API_ERROR_RESPONSES,
    DayCompareResponse,
    validate_day_compare_response,
)
from engine.score_methodology import DIRECTION_C_SOURCES

logger = logging.getLogger("day_compare")

router = APIRouter()


@router.get(
    "",
    response_model=DayCompareResponse,
    responses=API_ERROR_RESPONSES,
    summary="So sánh điểm hai ngày cho cùng lá số",
)
@router.get("/", include_in_schema=False, response_model=DayCompareResponse)
async def day_compare(
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    date_a: str = Query(..., description="Ngày A YYYY-MM-DD"),
    date_b: str = Query(..., description="Ngày B YYYY-MM-DD"),
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

        da = date.fromisoformat(date_a)
        db = date.fromisoformat(date_b)
        user_chart = get_user_chart(bd.isoformat(), birth_time, gender)
        try:
            rule_key = resolve_intent_key(intent)
        except ValueError as e:
            return error_response(400, "INVALID_INPUT", message_vi=str(e))
        intent_rule = get_intent_rule(intent)

        day_a = get_day_info(da.isoformat())
        day_b = get_day_info(db.isoformat())

        scored_a = score_day_context(
            day_info=day_a,
            user_chart=user_chart,
            intent=rule_key,
            intent_rule=intent_rule,
            target=da,
        )
        scored_b = score_day_context(
            day_info=day_b,
            user_chart=user_chart,
            intent=rule_key,
            intent_rule=intent_rule,
            target=db,
        )

        score_a = scored_a["score"]
        score_b = scored_b["score"]
        delta = score_b - score_a
        comparison_vi, better_for = build_compare_copy(score_a, score_b, date_a, date_b, rule_key)

        content = {
            "status": "success",
            "date_a": date_a,
            "date_b": date_b,
            "score_a": score_a,
            "score_b": score_b,
            "delta_score": delta,
            "comparison_vi": comparison_vi,
            "better_for": better_for,
            "sources": DIRECTION_C_SOURCES,
        }
        return validate_day_compare_response(content)

    except ValueError as e:
        from pydantic import ValidationError

        if isinstance(e, ValidationError):
            logger.exception("day_compare response validation failed")
            return error_response(500, "INTERNAL_ERROR")
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in day_compare")
        return error_response(500, "INTERNAL_ERROR")
