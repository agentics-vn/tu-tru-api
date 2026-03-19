"""
GET /v1/tieu-van — Monthly fortune (Tiểu Vận) endpoint.

Returns the transiting month pillar, its element relationship to the user's
mệnh, and a stub reading. ⚠️ Full reading text needs SME input.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from engine.can_chi import (
    CAN_NAMES,
    CHI_NAMES,
    CAN_HANH,
    NAP_AM_HANH,
    NAP_AM_NAMES,
    get_can_chi_year,
    get_nap_am_pair_idx,
)
from api.parse_date import parse_dmy
from calendar_service import get_user_chart

logger = logging.getLogger("tieu_van")

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Ngũ Hành interaction tables
# ─────────────────────────────────────────────────────────────────────────────

# A sinh B  (A nurtures B)
TUONG_SINH: dict[str, str] = {
    "Kim": "Thủy", "Thủy": "Mộc", "Mộc": "Hỏa",
    "Hỏa": "Thổ", "Thổ": "Kim",
}

# A khắc B  (A overcomes B)
TUONG_KHAC: dict[str, str] = {
    "Kim": "Mộc", "Mộc": "Thổ", "Thổ": "Thủy",
    "Thủy": "Hỏa", "Hỏa": "Kim",
}


def _element_relation(month_hanh: str, menh_hanh: str) -> str:
    """
    Determine the Ngũ Hành relationship between month pillar element
    and user's mệnh element.

    Returns one of: 'tuong_sinh', 'bi_sinh', 'tuong_khac', 'bi_khac', 'binh_hoa'
    """
    if month_hanh == menh_hanh:
        return "binh_hoa"  # Same element
    if TUONG_SINH.get(month_hanh) == menh_hanh:
        return "bi_sinh"  # Month nurtures user → good
    if TUONG_SINH.get(menh_hanh) == month_hanh:
        return "tuong_sinh"  # User nurtures month → mediocre (leaking energy)
    if TUONG_KHAC.get(month_hanh) == menh_hanh:
        return "bi_khac"  # Month overcomes user → bad
    if TUONG_KHAC.get(menh_hanh) == month_hanh:
        return "tuong_khac"  # User overcomes month → ok-ish
    return "binh_hoa"  # Fallback


# ─────────────────────────────────────────────────────────────────────────────
# Month pillar calculation (simplified solar-term approach)
#
# ⚠️ This is a simplified version using the "year-month" rule:
#   month_can = (year_can * 2 + month_index) % 10
#   month_chi = month_index + 2  (month 1→Dần(2), …, 12→Sửu(1))
#
# A proper implementation would use exact solar terms (tiết khí).
# This is good enough for monthly fortune overview.
# ─────────────────────────────────────────────────────────────────────────────

def _get_month_pillar(year: int, month: int) -> dict:
    """
    Get the Can Chi pillar for a solar month (simplified).

    Uses the classical rule:
      month_chi: month 1→Dần(2), 2→Mão(3), ..., 11→Tý(0), 12→Sửu(1)
      month_can: derived from year's Thiên Can.
        year_can_idx 0(Giáp)/5(Kỷ): month 1 starts with Bính(2)
        year_can_idx 1(Ất)/6(Canh): month 1 starts with Mậu(4)
        year_can_idx 2(Bính)/7(Tân): month 1 starts with Canh(6)
        year_can_idx 3(Đinh)/8(Nhâm): month 1 starts with Nhâm(8)
        year_can_idx 4(Mậu)/9(Quý): month 1 starts with Giáp(0)

    Args:
        year: solar year
        month: 1-12

    Returns:
        dict with: can_idx, chi_idx, can_name, chi_name, nap_am_hanh, nap_am_name
    """
    year_cc = get_can_chi_year(year)
    year_can = year_cc["can_idx"]

    # Month chi: 1→Dần(2), 2→Mão(3), ..., 11→Tý(0), 12→Sửu(1)
    month_chi = (month + 1) % 12

    # Month can from the classical "Ngũ Hổ Độn Nguyệt" rule
    # Starting can for month 1 (Dần):
    start_can = ((year_can % 5) * 2 + 2) % 10
    month_can = (start_can + month - 1) % 10

    pair_idx = get_nap_am_pair_idx(month_can, month_chi)

    return {
        "can_idx": month_can,
        "chi_idx": month_chi,
        "can_name": CAN_NAMES[month_can],
        "chi_name": CHI_NAMES[month_chi],
        "nap_am_hanh": NAP_AM_HANH[pair_idx],
        "nap_am_name": NAP_AM_NAMES[pair_idx],
    }


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

@router.get("")
@router.get("/")
async def tieu_van(
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: Optional[int] = Query(None, description="Giờ sinh: 0,2,4,6,8,10,11,14,16,18,20,22,23"),
    gender: Optional[int] = Query(None, description="Giới tính: 1 (nam) hoặc -1 (nữ)"),
    month: str = Query(..., description="Tháng mục tiêu, định dạng YYYY-MM"),
) -> JSONResponse:
    try:
        # Parse birth_date
        bd = parse_dmy(birth_date)
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
        month_pillar = _get_month_pillar(year, month_num)

        # Element relationship
        relation = _element_relation(month_pillar["nap_am_hanh"], user_chart["menh_hanh"])

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
        logger.exception("Internal error in tieu_van")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": "Đã có lỗi xảy ra. Vui lòng thử lại sau.",
            },
        )
