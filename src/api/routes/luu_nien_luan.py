"""
GET /v1/luu-nien/luan-context — Vận trình năm facts for NLTT/LLM.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.errors import error_response
from api.parse_date import parse_dmy
from api.schemas.direction_c import API_ERROR_RESPONSES
from api.schemas.van_trinh_nam import VanTrinhNamLuanContextResponse
from api.van_trinh_nam_luan_context import (
    VanTrinhNamLuanContextError,
    build_van_trinh_nam_luan_context,
)
from engine.pillars import VALID_BIRTH_HOURS

logger = logging.getLogger("luu_nien_luan")

router = APIRouter()


@router.get(
    "/luan-context",
    response_model=VanTrinhNamLuanContextResponse,
    responses=API_ERROR_RESPONSES,
    summary="Vận trình năm — facts + signals cho LLM",
)
async def luu_nien_luan_context(
    year: int = Query(..., ge=1900, le=2100),
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: int = Query(..., description="Giờ sinh (0,2,4,...)"),
    gender: int = Query(..., description="1 nam, -1 nữ"),
    tz: Optional[str] = Query(None, description="IANA timezone"),
) -> JSONResponse:
    try:
        from api.tz import today_in_tz

        _today = today_in_tz(tz)
        bd = parse_dmy(birth_date)
        if bd.year < 1900 or bd >= _today:
            return error_response(
                400, "INVALID_INPUT",
                message_vi="birth_date phải là ngày quá khứ (năm >= 1900).",
            )
        if birth_time not in VALID_BIRTH_HOURS:
            return error_response(
                400, "INVALID_INPUT",
                message_vi=f"birth_time phải là một trong {sorted(VALID_BIRTH_HOURS)}",
            )
        if gender not in (1, -1):
            return error_response(400, "INVALID_INPUT", message_vi="gender phải là 1 hoặc -1")

        payload = build_van_trinh_nam_luan_context(
            year=year,
            birth_date_iso=bd.isoformat(),
            birth_time=birth_time,
            gender=gender,
        )
        return VanTrinhNamLuanContextResponse.model_validate(payload)

    except VanTrinhNamLuanContextError as e:
        logger.error("luan-context invariant: %s", e)
        return error_response(500, "INTERNAL_ERROR", message_vi=str(e))
    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in luu_nien_luan_context")
        return error_response(500, "INTERNAL_ERROR")
