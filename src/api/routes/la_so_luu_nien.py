"""GET /v1/la-so/luu-nien — Annual luck (Lưu niên) MVP."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from api.errors import error_response
from api.schemas.direction_c import API_ERROR_RESPONSES, LuuNienResponse
from api.parse_date import parse_dmy
from api.version import get_engine_version, utc_now_iso
from engine.luu_nien import build_luu_nien
from engine.pillars import VALID_BIRTH_HOURS

logger = logging.getLogger("la_so_luu_nien")

router = APIRouter()


@router.get(
    "/luu-nien",
    response_model=LuuNienResponse,
    responses=API_ERROR_RESPONSES,
    summary="Lưu niên MVP — vận năm theo lá số",
)
async def la_so_luu_nien(
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: int = Query(..., description="Giờ sinh (bắt buộc)"),
    gender: int = Query(..., description="1 nam | -1 nữ"),
    year: int = Query(..., ge=1900, le=2100, description="Năm dương lịch cần xem"),
) -> LuuNienResponse:
    try:
        bd = parse_dmy(birth_date)
        if bd >= date.today():
            return error_response(400, "INVALID_INPUT", message_vi="birth_date phải là ngày quá khứ.")

        if birth_time not in VALID_BIRTH_HOURS:
            return error_response(
                400,
                "INVALID_INPUT",
                message_vi=f"birth_time phải là một trong {sorted(VALID_BIRTH_HOURS)}",
            )
        if gender not in (1, -1):
            return error_response(400, "INVALID_INPUT", message_vi="gender phải là 1 hoặc -1.")

        payload = build_luu_nien(
            birth_date_iso=bd.isoformat(),
            birth_time=birth_time,
            gender=gender,
            year=year,
        )
        return LuuNienResponse.model_validate({
            "status": "success",
            "birth_date": bd.isoformat(),
            "engine_version": get_engine_version(),
            "computed_at": utc_now_iso(),
            **payload,
        })

    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in la_so_luu_nien")
        return error_response(500, "INTERNAL_ERROR")
