"""
GET /v1/phong-thuy — Personalized feng shui recommendations.

Returns directions, colors, numbers, and items based on the user's
Dụng Thần / Kỵ Thần elements.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.parse_date import parse_dmy
from engine.can_chi import get_menh_nap_am, CAN_HANH
from engine.pillars import get_tu_tru, VALID_BIRTH_HOURS
from engine.dung_than import find_dung_than, SINH_BY, KHAC_BY

logger = logging.getLogger("phong_thuy")

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Static lookup tables
# ─────────────────────────────────────────────────────────────────────────────

HUONG_BY_HANH: dict[str, list[dict]] = {
    "Kim": [
        {"direction": "Tây", "element": "Kim", "reason": "Chính Tây thuộc Kim — hành Dụng Thần."},
        {"direction": "Tây Bắc", "element": "Kim", "reason": "Tây Bắc thuộc Kim — hỗ trợ sự nghiệp."},
        {"direction": "Đông Bắc", "element": "Thổ", "reason": "Thổ sinh Kim — gián tiếp hỗ trợ."},
    ],
    "Mộc": [
        {"direction": "Đông", "element": "Mộc", "reason": "Chính Đông thuộc Mộc — hành Dụng Thần."},
        {"direction": "Đông Nam", "element": "Mộc", "reason": "Đông Nam thuộc Mộc — hỗ trợ sự nghiệp."},
        {"direction": "Bắc", "element": "Thủy", "reason": "Thủy sinh Mộc — gián tiếp hỗ trợ."},
    ],
    "Thủy": [
        {"direction": "Bắc", "element": "Thủy", "reason": "Chính Bắc thuộc Thủy — hành Dụng Thần."},
        {"direction": "Tây", "element": "Kim", "reason": "Kim sinh Thủy — gián tiếp hỗ trợ."},
        {"direction": "Tây Bắc", "element": "Kim", "reason": "Tây Bắc thuộc Kim — sinh Thủy."},
    ],
    "Hỏa": [
        {"direction": "Nam", "element": "Hỏa", "reason": "Chính Nam thuộc Hỏa — hành Dụng Thần."},
        {"direction": "Đông", "element": "Mộc", "reason": "Mộc sinh Hỏa — gián tiếp hỗ trợ."},
        {"direction": "Đông Nam", "element": "Mộc", "reason": "Đông Nam thuộc Mộc — sinh Hỏa."},
    ],
    "Thổ": [
        {"direction": "Trung Tâm", "element": "Thổ", "reason": "Trung Tâm thuộc Thổ — hành Dụng Thần."},
        {"direction": "Đông Bắc", "element": "Thổ", "reason": "Đông Bắc thuộc Thổ — hỗ trợ ổn định."},
        {"direction": "Nam", "element": "Hỏa", "reason": "Hỏa sinh Thổ — gián tiếp hỗ trợ."},
    ],
}

MAU_BY_HANH: dict[str, list[dict]] = {
    "Kim": [
        {"color": "Trắng", "hex": "#F5F5F5", "element": "Kim"},
        {"color": "Bạc", "hex": "#C0C0C0", "element": "Kim"},
        {"color": "Vàng nhạt", "hex": "#F0E68C", "element": "Thổ"},
    ],
    "Mộc": [
        {"color": "Xanh lá", "hex": "#3A6B35", "element": "Mộc"},
        {"color": "Xanh dương", "hex": "#2B6CB0", "element": "Thủy"},
        {"color": "Đen", "hex": "#1A1A1A", "element": "Thủy"},
    ],
    "Thủy": [
        {"color": "Đen", "hex": "#1A1A1A", "element": "Thủy"},
        {"color": "Xanh dương", "hex": "#2B6CB0", "element": "Thủy"},
        {"color": "Trắng", "hex": "#F5F5F5", "element": "Kim"},
    ],
    "Hỏa": [
        {"color": "Đỏ", "hex": "#C53030", "element": "Hỏa"},
        {"color": "Tím", "hex": "#6B46C1", "element": "Hỏa"},
        {"color": "Xanh lá", "hex": "#3A6B35", "element": "Mộc"},
    ],
    "Thổ": [
        {"color": "Vàng đất", "hex": "#B8860B", "element": "Thổ"},
        {"color": "Nâu", "hex": "#8B6914", "element": "Thổ"},
        {"color": "Đỏ", "hex": "#C53030", "element": "Hỏa"},
    ],
}

SO_BY_HANH: dict[str, list[int]] = {
    "Kim": [4, 9],
    "Mộc": [1, 2, 6],
    "Thủy": [1, 6],
    "Hỏa": [2, 7],
    "Thổ": [5, 0, 8],
}

VAT_PHAM_BY_HANH: dict[str, list[dict]] = {
    "Kim": [
        {"item": "Chuông gió kim loại", "element": "Kim", "reason": "Tăng cường Kim khí — tốt cho tài lộc."},
        {"item": "Tượng rùa đồng", "element": "Kim", "reason": "Kim khí hỗ trợ sự nghiệp ổn định."},
    ],
    "Mộc": [
        {"item": "Cây xanh để bàn", "element": "Mộc", "reason": "Tăng cường Mộc khí — tốt cho tài lộc và sức khỏe."},
        {"item": "Bể cá nhỏ", "element": "Thủy", "reason": "Thủy sinh Mộc — kích hoạt dòng tiền lưu thông."},
        {"item": "Tranh phong cảnh rừng", "element": "Mộc", "reason": "Tăng Mộc khí trong không gian làm việc."},
    ],
    "Thủy": [
        {"item": "Bể cá phong thủy", "element": "Thủy", "reason": "Tăng cường Thủy khí — kích hoạt tài lộc."},
        {"item": "Thác nước mini", "element": "Thủy", "reason": "Nước chảy liên tục tượng trưng cho tiền bạc."},
    ],
    "Hỏa": [
        {"item": "Đèn muối Himalaya", "element": "Hỏa", "reason": "Ánh sáng ấm tăng Hỏa khí — tốt cho năng lượng."},
        {"item": "Nến thơm", "element": "Hỏa", "reason": "Lửa tượng trưng cho sự sáng tạo và nhiệt huyết."},
    ],
    "Thổ": [
        {"item": "Chậu đá cảnh", "element": "Thổ", "reason": "Đá thuộc Thổ — tăng sự ổn định."},
        {"item": "Bình gốm sứ", "element": "Thổ", "reason": "Gốm sứ thuộc Thổ — hỗ trợ sức khỏe."},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/phong-thuy
# ─────────────────────────────────────────────────────────────────────────────

@router.get("")
@router.get("/")
async def phong_thuy_endpoint(
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: Optional[int] = Query(None, description="Giờ sinh"),
    gender: Optional[int] = Query(None, description="Giới tính: 1 (nam) hoặc -1 (nữ)"),
) -> JSONResponse:
    try:
        bd = parse_dmy(birth_date)
        if bd.year < 1900 or bd >= date.today():
            return JSONResponse(
                status_code=400,
                content={"status": "error", "error_code": "INVALID_INPUT", "message": "birth_date phải là ngày quá khứ (năm >= 1900)."},
            )

        if birth_time is not None and birth_time not in VALID_BIRTH_HOURS:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "error_code": "INVALID_INPUT", "message": f"birth_time phải là một trong {sorted(VALID_BIRTH_HOURS)}"},
            )

        menh = get_menh_nap_am(bd.year)

        # Determine Dụng Thần / Kỵ Thần
        if birth_time is not None:
            tu_tru = get_tu_tru(bd.isoformat(), birth_time)
            dung_result = find_dung_than(tu_tru)
            dung_than = dung_result["dung_than"]
            ky_than = dung_result["ky_than"]
        else:
            # Fallback to Nạp Âm-based
            dung_than = menh["duong_than"]
            ky_than = menh["ky_than"]

        # Build directions
        huong_tot = HUONG_BY_HANH.get(dung_than, [])
        huong_xau = HUONG_BY_HANH.get(ky_than, [])
        # Relabel xau reasons
        huong_xau_labeled = [
            {**h, "reason": f"{h['element']} là Kỵ Thần — nên tránh hướng này."}
            for h in huong_xau
        ]

        # Colors
        mau_may_man = MAU_BY_HANH.get(dung_than, [])
        mau_ky = MAU_BY_HANH.get(ky_than, [])[:2]

        # Numbers
        so_may_man = SO_BY_HANH.get(dung_than, [])
        so_ky = SO_BY_HANH.get(ky_than, [])

        # Items
        vat_pham = VAT_PHAM_BY_HANH.get(dung_than, [])

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "user_menh": {"hanh": menh["hanh"], "name": menh["name"]},
                "dung_than": dung_than,
                "ky_than": ky_than,
                "huong_tot": huong_tot,
                "huong_xau": huong_xau_labeled,
                "mau_may_man": mau_may_man,
                "mau_ky": mau_ky,
                "so_may_man": so_may_man,
                "so_ky": so_ky,
                "vat_pham": vat_pham,
            },
        )

    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error_code": "INVALID_INPUT", "message": str(e)},
        )
    except Exception:
        logger.exception("Internal error in phong_thuy")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error_code": "INTERNAL_ERROR", "message": "Đã có lỗi xảy ra."},
        )
