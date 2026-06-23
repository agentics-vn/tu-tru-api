"""
POST /v1/la-so-full — Full Mệnh Bàn Tứ Trụ chart (grid data + analysis).
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator

from api.errors import error_response
from api.parse_date import parse_dmy
from api.schemas.direction_c import API_ERROR_RESPONSES
from api.version import get_engine_version, utc_now_iso
from engine.chart_bundle import build_full_chart
from engine.menh_ban_html import render_menh_ban_html
from engine.pillars import VALID_BIRTH_HOURS, get_tu_tru

logger = logging.getLogger("la_so_full")

router = APIRouter()


class LaSoFullRequest(BaseModel):
    birth_date: str
    birth_time: int
    gender: int
    name: Optional[str] = None
    num_dai_van: int = 10
    num_luu_nien: int = 10
    view_year: Optional[int] = None
    format: Literal["json", "html"] = "json"

    @field_validator("birth_date")
    @classmethod
    def birth_date_valid(cls, v: str) -> str:
        d = parse_dmy(v)
        if d.year < 1900:
            raise ValueError("birth_date phải có năm >= 1900")
        if d > date.today():
            raise ValueError("birth_date không được ở tương lai")
        return v

    @field_validator("birth_time")
    @classmethod
    def birth_time_valid(cls, v: int) -> int:
        if v not in VALID_BIRTH_HOURS:
            raise ValueError(
                f"birth_time phải là một trong {sorted(VALID_BIRTH_HOURS)}",
            )
        return v

    @field_validator("gender")
    @classmethod
    def gender_valid(cls, v: int) -> int:
        if v not in (1, -1):
            raise ValueError("gender phải là 1 (nam) hoặc -1 (nữ)")
        return v


@router.post(
    "",
    responses=API_ERROR_RESPONSES,
    summary="Lá số Mệnh Bàn Tứ Trụ đầy đủ (grid + phân tích)",
)
@router.post("/", include_in_schema=False, responses=API_ERROR_RESPONSES)
async def la_so_full_endpoint(req: LaSoFullRequest):
    try:
        bd = parse_dmy(req.birth_date)
        birth_date_str = bd.isoformat()
        tu_tru = get_tu_tru(birth_date_str, req.birth_time)
        chart = build_full_chart(
            tu_tru,
            birth_date_str,
            req.gender,
            req.birth_time,
            0,
            name=req.name,
            num_dai_van=req.num_dai_van,
            num_luu_nien=req.num_luu_nien,
            view_year=req.view_year,
        )
        chart_html = render_menh_ban_html(chart)
        if req.format == "html":
            return HTMLResponse(
                content=chart_html,
                media_type="text/html; charset=utf-8",
            )
        return {
            "status": "success",
            "birth_date": birth_date_str,
            "birth_time": req.birth_time,
            "engine_version": get_engine_version(),
            "computed_at": utc_now_iso(),
            "menh_ban": chart,
            "html": chart_html,
        }
    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in la_so_full")
        return error_response(500, "INTERNAL_ERROR")
