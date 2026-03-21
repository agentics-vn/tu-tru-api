"""
GET /v1/convert-date — Gregorian ↔ Lunar conversion utility (T4-05).

Provides bidirectional conversion between solar (Gregorian) and Vietnamese
lunar calendar dates, useful for diaspora users and external integrations.
"""

from __future__ import annotations

import logging
from typing import Optional

import lunardate
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.errors import error_response
from engine.lunar import solar_to_lunar

logger = logging.getLogger(__name__)

router = APIRouter(tags=["convert-date"])

# Vietnamese lunar month names (1-indexed)
LUNAR_MONTH_NAMES = [
    "", "Giêng", "Hai", "Ba", "Tư", "Năm", "Sáu",
    "Bảy", "Tám", "Chín", "Mười", "Một", "Chạp",
]


@router.get("")
@router.get("/")
async def convert_date(
    solar: Optional[str] = Query(
        None,
        description="Solar date YYYY-MM-DD → converts to lunar. Mutually exclusive with lunar_* params.",
    ),
    lunar_year: Optional[int] = Query(None, description="Lunar year (e.g. 2026)"),
    lunar_month: Optional[int] = Query(None, ge=1, le=12, description="Lunar month 1–12"),
    lunar_day: Optional[int] = Query(None, ge=1, le=30, description="Lunar day 1–30"),
    is_leap_month: bool = Query(False, description="True if the lunar month is a leap month"),
) -> JSONResponse:
    """Convert between Gregorian and Vietnamese lunar calendar dates."""
    try:
        has_solar = solar is not None
        has_lunar = any(v is not None for v in (lunar_year, lunar_month, lunar_day))

        if has_solar and has_lunar:
            return error_response(
                400, "INVALID_INPUT",
                message_vi="Chỉ dùng 'solar' HOẶC 'lunar_year/lunar_month/lunar_day', không dùng cả hai.",
                message_en="Use 'solar' OR 'lunar_year/lunar_month/lunar_day', not both.",
            )

        if not has_solar and not has_lunar:
            return error_response(
                400, "INVALID_INPUT",
                message_vi="Phải truyền 'solar' hoặc 'lunar_year/lunar_month/lunar_day'.",
                message_en="Provide either 'solar' or 'lunar_year/lunar_month/lunar_day'.",
            )

        # ── Solar → Lunar ────────────────────────────────────────────────
        if has_solar:
            lunar = solar_to_lunar(solar)
            mn = LUNAR_MONTH_NAMES[lunar["lunar_month"]] if 1 <= lunar["lunar_month"] <= 12 else str(lunar["lunar_month"])
            lunar_display = f"Ngày {lunar['lunar_day']} tháng {mn}"
            if lunar["is_leap_month"]:
                lunar_display += " (nhuận)"

            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "direction": "solar_to_lunar",
                    "input": {"solar": solar},
                    "result": {
                        "lunar_year": lunar["lunar_year"],
                        "lunar_month": lunar["lunar_month"],
                        "lunar_day": lunar["lunar_day"],
                        "is_leap_month": lunar["is_leap_month"],
                        "display_vi": lunar_display,
                    },
                },
            )

        # ── Lunar → Solar ────────────────────────────────────────────────
        if lunar_year is None or lunar_month is None or lunar_day is None:
            return error_response(
                400, "INVALID_INPUT",
                message_vi="Phải truyền đủ lunar_year, lunar_month, lunar_day.",
                message_en="All of lunar_year, lunar_month, lunar_day are required.",
            )

        ld = lunardate.LunarDate(lunar_year, lunar_month, lunar_day, isLeapMonth=is_leap_month)
        sd = ld.toSolarDate()
        solar_iso = sd.isoformat()

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "direction": "lunar_to_solar",
                "input": {
                    "lunar_year": lunar_year,
                    "lunar_month": lunar_month,
                    "lunar_day": lunar_day,
                    "is_leap_month": is_leap_month,
                },
                "result": {
                    "solar": solar_iso,
                },
            },
        )

    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in convert_date")
        return error_response(500, "INTERNAL_ERROR")
