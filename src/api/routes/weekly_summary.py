"""
GET /v1/weekly-summary — Top 1–3 dates in the next 7 days (T5-04).

Returns the best auspicious dates in the coming week with a one-line
reason for each, designed for push notifications and dashboard widgets.
"""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.errors import error_response
from api.parse_date import parse_dmy
from api.tz import today_in_tz
from calendar_service import get_day_info, get_user_chart
from engine.hoang_dao import get_gio_hoang_dao
from filter import apply_layer2_filter
from scoring import compute_score

logger = logging.getLogger(__name__)

router = APIRouter(tags=["weekly-summary"])

# Load intent rules once
_RULES_PATH = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "seed" / "intent-rules.json"
with open(_RULES_PATH) as _f:
    _INTENT_RULES = json.load(_f)

_DEFAULT_RULE = _INTENT_RULES.get("MAC_DINH", {"bonus_sao": [], "forbidden_sao": []})


@router.get("")
@router.get("/", include_in_schema=False)
async def weekly_summary(
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: Optional[int] = Query(None, description="Giờ sinh"),
    gender: Optional[int] = Query(None, description="Giới tính: 1 (nam) hoặc -1 (nữ)"),
    intent: str = Query("MAC_DINH", description="Mục đích (e.g. KHAI_TRUONG, CUOI_HOI)"),
    profile_id: Optional[str] = Query(None, description="Saved profile ID (alternative to birth_date)"),
    tz: Optional[str] = Query(None, description="IANA timezone, e.g. Asia/Ho_Chi_Minh"),
) -> JSONResponse:
    try:
        _today = today_in_tz(tz)

        # T5-03: Resolve profile
        if profile_id and not birth_date:
            from api.routes.profile import get_profile
            profile = get_profile(profile_id)
            if profile is None:
                return error_response(400, "INVALID_INPUT", message_vi="Không tìm thấy hồ sơ.")
            birth_date = profile["birth_date"]
            birth_time = birth_time if birth_time is not None else profile["birth_time"]
            gender = gender if gender is not None else profile["gender"]

        bd = parse_dmy(birth_date)
        if bd.year < 1900 or bd >= _today:
            return error_response(400, "INVALID_INPUT", message_vi="birth_date phải là ngày quá khứ (năm >= 1900).")

        birth_date_str = bd.isoformat()
        user_chart = get_user_chart(birth_date_str, birth_time, gender)

        intent_rule = _INTENT_RULES.get(intent, _DEFAULT_RULE)
        rule_key = intent

        # Scan next 7 days (today + 6)
        scored_days: list[dict] = []
        for offset in range(7):
            d = _today + timedelta(days=offset)
            ds = d.isoformat()

            day_info = get_day_info(ds)
            if not day_info["is_layer1_pass"]:
                continue

            filter_result = apply_layer2_filter(day_info, user_chart, rule_key)
            if not filter_result["pass"]:
                continue

            score_result = compute_score(day_info, user_chart, rule_key, intent_rule, filter_result)
            scored_days.append({"day_info": day_info, "score_result": score_result})

        # Sort by score, pick top 3
        scored_days.sort(key=lambda x: x["score_result"]["score"], reverse=True)
        top_days = scored_days[:3]

        results = [
            {
                "date": d["day_info"]["date"],
                "score": d["score_result"]["score"],
                "grade": d["score_result"]["grade"],
                "one_liner": d["score_result"]["summary_vi"],
                "best_hours": [
                    {"chi_name": g["chi_name"], "range": f"{g['start']}-{g['end']}"}
                    for g in get_gio_hoang_dao(d["day_info"]["day_chi_idx"])
                ][:3],
            }
            for d in top_days
        ]

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "week_start": _today.isoformat(),
                "week_end": (_today + timedelta(days=6)).isoformat(),
                "intent": intent,
                "top_dates": results,
                "count": len(results),
            },
        )

    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in weekly_summary")
        return error_response(500, "INTERNAL_ERROR")
