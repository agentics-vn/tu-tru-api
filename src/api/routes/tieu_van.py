"""
GET /v1/tieu-van — Monthly fortune (Tiểu Vận) endpoint.

Returns the transiting month pillar, its element relationship to the user's
mệnh, and a stub reading. ⚠️ Full reading text needs SME input.
"""

from __future__ import annotations

import logging

from api.errors import error_response
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from api.parse_date import parse_dmy
from calendar_service import get_user_chart
from engine.luu_nguyet import element_relation_menh, get_luu_nguyet_pillar

logger = logging.getLogger("tieu_van")

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Reading templates (stub — needs SME input)
# ─────────────────────────────────────────────────────────────────────────────

_READING_TEMPLATES: dict[str, dict] = {
    "bi_sinh": {
        "reading": (
            "Tháng này vận trình khá thuận lợi. Ngũ Hành tháng sinh "
            "mệnh chủ, mang lại năng lượng tích cực. Phù hợp để bắt đầu "
            "việc mới, đàm phán kinh doanh, hoặc mở rộng quan hệ."
        ),
        "tags": ["Thuận lợi", "Tài lộc", "Cơ hội"],
    },
    "tuong_sinh": {
        "reading": (
            "Tháng này vận trình ổn định nhưng tiêu hao năng lượng. "
            "Mệnh chủ sinh cho tháng, nghĩa là bạn cho đi nhiều hơn nhận. "
            "Nên tập trung giữ sức khỏe, tránh phung phí tài chính."
        ),
        "tags": ["Trung bình", "Tiêu hao", "Cẩn trọng tài chính"],
    },
    "bi_khac": {
        "reading": (
            "Tháng này cần đặc biệt cẩn trọng. Ngũ Hành tháng khắc "
            "mệnh chủ, có thể gặp trở ngại hoặc xung đột. Nên tránh "
            "đầu tư lớn, kiện tụng, hoặc quyết định quan trọng."
        ),
        "tags": ["Khó khăn", "Cẩn trọng", "Hạn chế rủi ro"],
    },
    "tuong_khac": {
        "reading": (
            "Tháng này bạn có ưu thế nhất định. Mệnh chủ khắc được "
            "Ngũ Hành tháng, nghĩa là bạn làm chủ tình huống. Tuy nhiên "
            "đừng quá tự tin — vẫn cần cân nhắc kỹ trước mọi quyết định."
        ),
        "tags": ["Khá tốt", "Chủ động", "Quyết đoán"],
    },
    "binh_hoa": {
        "reading": (
            "Tháng này vận trình ổn định, bình hòa. Ngũ Hành tháng "
            "cùng mệnh chủ, không có xung khắc đặc biệt. Phù hợp để "
            "duy trì hiện trạng, hoàn tất công việc dang dở."
        ),
        "tags": ["Ổn định", "Bình hòa", "Duy trì"],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/tieu-van
# ─────────────────────────────────────────────────────────────────────────────

@router.get("", deprecated=True, summary="[Deprecated] Tiểu vận tháng — dùng /v1/luu-nien/luan-context")
@router.get("/", include_in_schema=False, deprecated=True)
async def tieu_van(
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: Optional[int] = Query(None, description="Giờ sinh: 0,2,4,6,8,10,11,14,16,18,20,22,23"),
    gender: Optional[int] = Query(None, description="Giới tính: 1 (nam) hoặc -1 (nữ)"),
    month: str = Query(..., description="Tháng mục tiêu, định dạng YYYY-MM"),
    tz: Optional[str] = Query(None, description="IANA timezone, e.g. Asia/Ho_Chi_Minh (default)"),
) -> JSONResponse:
    try:
        from api.tz import today_in_tz

        _today = today_in_tz(tz)

        # Parse birth_date
        bd = parse_dmy(birth_date)
        if bd.year < 1900 or bd >= _today:
            return error_response(400, "INVALID_INPUT", message_vi="birth_date phải là ngày quá khứ (năm >= 1900).")

        # Parse month
        parts = month.split("-")
        if len(parts) != 2:
            raise ValueError("Tháng phải có định dạng YYYY-MM")
        year = int(parts[0])
        month_num = int(parts[1])
        if not (1 <= month_num <= 12):
            raise ValueError("Tháng phải từ 01 đến 12")

        # Validate birth_time if provided
        if birth_time is not None:
            from engine.pillars import VALID_BIRTH_HOURS
            if birth_time not in VALID_BIRTH_HOURS:
                raise ValueError(
                    f"birth_time phải là một trong {sorted(VALID_BIRTH_HOURS)}"
                )

        # User chart
        user_chart = get_user_chart(bd.isoformat(), birth_time, gender)

        # Month pillar
        month_pillar = get_luu_nguyet_pillar(year, month_num)

        # Element relationship
        relation = element_relation_menh(month_pillar["nap_am_hanh"], user_chart["menh_hanh"])

        # Reading template
        template = _READING_TEMPLATES.get(relation, _READING_TEMPLATES["binh_hoa"])

        # Build response content
        content: dict = {
            "status": "success",
            "month": month,
            "tieu_van_pillar": {
                "can_name": month_pillar["can_name"],
                "chi_name": month_pillar["chi_name"],
                "display": f"{month_pillar['can_name']} {month_pillar['chi_name']}",
                "nap_am_hanh": month_pillar["nap_am_hanh"],
                "nap_am_name": month_pillar["nap_am_name"],
            },
            "user_menh": {
                "hanh": user_chart["menh_hanh"],
                "name": user_chart["menh_name"],
            },
            "element_relation": relation,
            "reading": template["reading"],
            "tags": template["tags"],
        }

        # Enrich with Tứ Trụ data when available
        if user_chart.get("tu_tru"):
            tu_tru = user_chart["tu_tru"]
            content["nhat_chu"] = {
                "can_name": tu_tru["nhat_chu"]["can_name"],
                "hanh": tu_tru["nhat_chu"]["hanh"],
            }
            if user_chart.get("dung_than"):
                content["dung_than"] = user_chart["dung_than"]
            if user_chart.get("chart_strength"):
                content["chart_strength"] = user_chart["chart_strength"]

            # Thập Thần of the month pillar against Day Master
            if user_chart.get("thap_than"):
                content["thap_than_of_month"] = user_chart["thap_than"]["month_god"]["name"]

            # Đại Vận context
            if user_chart.get("current_dai_van"):
                dv = user_chart["current_dai_van"]
                dv_hanh = dv.get("can_hanh", "")
                dung_than = user_chart.get("dung_than", "")
                dv_relation = ""
                if dv_hanh == dung_than:
                    dv_relation = f"hỗ trợ Dụng Thần {dung_than}"
                elif dv_hanh == user_chart.get("ky_than_v2"):
                    dv_relation = f"là Kỵ Thần — cần cẩn trọng"
                else:
                    dv_relation = f"trung tính"

                content["dai_van_context"] = (
                    f"Đang trong vận {dv['display']} ({dv_hanh}) — {dv_relation}"
                )

        return JSONResponse(status_code=200, content=content)

    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except HTTPException:
        raise
    except Exception:
        logger.exception("Internal error in tieu_van")
        return error_response(500, "INTERNAL_ERROR")
