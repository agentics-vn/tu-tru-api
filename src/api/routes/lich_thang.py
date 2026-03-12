"""
GET /v1/lich-thang — Calendar month view endpoint.

Returns all days in a month with hoàng đạo/hắc đạo badges,
layer-1 pass status, and basic astrology info for calendar rendering.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from calendar_service import get_day_info, get_user_chart, get_month_info
from engine.hoang_dao import get_day_star

logger = logging.getLogger("lich_thang")

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/lich-thang
# ─────────────────────────────────────────────────────────────────────────────

@router.get("")
@router.get("/")
async def lich_thang(
    birth_date: str = Query(..., description="Birth date in ISO format YYYY-MM-DD"),
    birth_time: Optional[int] = Query(None, description="Birth hour from dropdown: 0,2,4,6,8,10,11,14,16,18,20,22,23"),
    gender: Optional[str] = Query(None, description="Gender: male or female"),
    month: str = Query(..., description="Target month in YYYY-MM format"),
) -> JSONResponse:
    try:
        # Parse birth_date
        bd = date.fromisoformat(birth_date)
        if bd.year < 1900 or bd >= date.today():
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error_code": "INVALID_INPUT",
                    "message": "birth_date phải là ngày quá khứ (năm >= 1900).",
                },
            )

        # Parse month
        parts = month.split("-")
        if len(parts) != 2:
            raise ValueError("month must be in YYYY-MM format")
        year = int(parts[0])
        month_num = int(parts[1])
        if not (1 <= month_num <= 12):
            raise ValueError("month must be between 01 and 12")

        # Validate birth_time if provided
        if birth_time is not None:
            from engine.pillars import VALID_BIRTH_HOURS
            if birth_time not in VALID_BIRTH_HOURS:
                raise ValueError(
                    f"birth_time phải là một trong {sorted(VALID_BIRTH_HOURS)}"
                )

        # Get user chart
        user_chart = get_user_chart(birth_date, birth_time, gender)

        # Get all days in the month
        all_days = get_month_info(year, month_num, filter_passed=False)

        days_response: list[dict] = []
        for d in all_days:
            star_info = get_day_star(d["lunar_month"], d["day_chi_idx"])

            days_response.append({
                "date": d["date"],
                "lunar_day": d["lunar_day"],
                "lunar_month": d["lunar_month"],
                "can_chi_name": f"{d['day_can_name']} {d['day_chi_name']}",
                "is_hoang_dao": star_info["is_hoang_dao"],
                "star_name": star_info["star_name"],
                "truc_name": d["truc_name"],
                "truc_score": d["truc_score"],
                "is_layer1_pass": d["is_layer1_pass"],
                "badge": "hoang_dao" if star_info["is_hoang_dao"] else "hac_dao",
            })

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "month": month,
                "user_menh": {
                    "hanh": user_chart["menh_hanh"],
                    "name": user_chart["menh_name"],
                },
                "days": days_response,
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
    except HTTPException:
        raise
    except Exception:
        logger.exception("Internal error in lich_thang")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": "Đã có lỗi xảy ra. Vui lòng thử lại sau.",
            },
        )
