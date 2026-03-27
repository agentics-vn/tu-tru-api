"""
GET /v1/la-so — Lá số diễn giải (structured reading cho App / Supabase EF).

Cùng logic Tứ Trụ với POST /v1/tu-tru nhưng bắt buộc birth_time; trả object có nhãn ngữ nghĩa.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.errors import error_response
from api.parse_date import parse_dmy
from engine.la_so import build_la_so
from engine.pillars import VALID_BIRTH_HOURS, get_tu_tru

logger = logging.getLogger("la_so")

router = APIRouter()


@router.get("")
@router.get("/", include_in_schema=False)
async def la_so_endpoint(
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: int = Query(..., description="Giờ sinh (dropdown engine) — bắt buộc"),
    gender: Optional[int] = Query(
        None,
        description="1 nam | -1 nữ — có thì thêm tinh_duyen và dai_van_current",
    ),
) -> JSONResponse:
    try:
        bd = parse_dmy(birth_date)
        if bd.year < 1900 or bd >= date.today():
            return error_response(
                400,
                "INVALID_INPUT",
                message_vi="birth_date phải là ngày quá khứ (năm >= 1900).",
            )

        if birth_time not in VALID_BIRTH_HOURS:
            return error_response(
                400,
                "INVALID_INPUT",
                message_vi=f"birth_time phải là một trong {sorted(VALID_BIRTH_HOURS)}",
            )

        if gender is not None and gender not in (1, -1):
            return error_response(
                400,
                "INVALID_INPUT",
                message_vi="gender phải là 1 (nam) hoặc -1 (nữ).",
            )

        birth_iso = bd.isoformat()
        tu_tru = get_tu_tru(birth_iso, birth_time)
        la_so = build_la_so(tu_tru, gender, birth_iso)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "birth_date": birth_iso,
                "birth_time": birth_time,
                **({"gender": gender} if gender is not None else {}),
                **la_so,
            },
        )

    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in la_so")
        return error_response(500, "INTERNAL_ERROR")
