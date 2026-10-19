"""
POST /v1/la-so-full — Full Mệnh Bàn Tứ Trụ chart (grid data + analysis).
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, StrictBool, field_validator, model_validator

from api.errors import error_response
from api.parse_date import parse_dmy
from api.schemas.direction_c import API_ERROR_RESPONSES
from api.version import get_engine_version, utc_now_iso
from engine.chart_bundle import build_full_chart
from engine.dung_than import RULE_V1, RULE_V2
from engine.menh_ban_html import render_menh_ban_html
from engine.pillars import VALID_BIRTH_HOURS, get_tu_tru

logger = logging.getLogger("la_so_full")

router = APIRouter()

# Hợp đồng thiếu giờ ở gốc thân phản hồi (``menh_ban``: ``chart_bundle.THIEU_GIO_MENH_BAN``).
THIEU_GIO_GOC: dict[str, str] = {
    "birth_time": "null",   # giờ giữ chỗ của yêu cầu, không phải giờ sinh: không trả lại
    "html": "null",         # lưới HTML cần trụ giờ; format="html" + co_gio=false là 422
}

# "Đường mới" của route: thân yêu cầu có một trong hai khoá này (kể cả giá trị v1 tường minh).
# Đầu vào sai trên đường mới trả 422 (``app.validation_exception_handler`` và ``ValueError`` của
# route); lời gọi không có hai khoá giữ nguyên hợp đồng lỗi cũ (400), golden v1 canh.
KHOA_DUONG_MOI = frozenset({"dung_than_rule", "co_gio"})


def la_duong_moi(body) -> bool:
    return isinstance(body, dict) and not KHOA_DUONG_MOI.isdisjoint(body)


class LaSoFullRequest(BaseModel):
    birth_date: str
    birth_time: int
    gender: int
    name: Optional[str] = None
    num_dai_van: int = 10
    num_luu_nien: int = 10
    view_year: Optional[int] = None
    format: Literal["json", "html"] = "json"
    # Luật dụng–kỵ (đặc tả 8.1): vắng = "v1", hành vi cũ từng byte.
    dung_than_rule: Literal["v1", "2026-10.1"] = "v1"
    # False = khách không khai giờ: ``birth_time`` vẫn bắt buộc nhưng chỉ GIỮ CHỖ (hợp đồng
    # THIEU_GIO_GOC / chart_bundle.THIEU_GIO_MENH_BAN). StrictBool: "false", 0, null là 422.
    co_gio: StrictBool = True

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

    @model_validator(mode="after")
    def thieu_gio_hop_le(self) -> "LaSoFullRequest":
        if not self.co_gio and self.dung_than_rule != RULE_V2:
            raise ValueError(
                f"co_gio=false chỉ dùng với dung_than_rule='{RULE_V2}' "
                f"(luật '{RULE_V1}' không có nhánh thiếu giờ)",
            )
        if not self.co_gio and self.format == "html":
            raise ValueError("format='html' cần trụ giờ; co_gio=false chỉ trả json")
        return self


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
            dung_than_rule=req.dung_than_rule,
            co_gio=req.co_gio,
        )
        chart_html = render_menh_ban_html(chart) if req.co_gio else None
        if req.format == "html":
            return HTMLResponse(
                content=chart_html,
                media_type="text/html; charset=utf-8",
            )
        return {
            "status": "success",
            "birth_date": birth_date_str,
            "birth_time": req.birth_time if req.co_gio else None,
            "engine_version": get_engine_version(),
            "computed_at": utc_now_iso(),
            "menh_ban": chart,
            "html": chart_html,
        }
    except ValueError as e:
        ma = 422 if not KHOA_DUONG_MOI.isdisjoint(req.model_fields_set) else 400
        return error_response(ma, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in la_so_full")
        return error_response(500, "INTERNAL_ERROR")
