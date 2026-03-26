"""
GET /v1/lich-thang — Calendar month view endpoint.

Returns all days in a month with hoàng đạo/hắc đạo badges,
giờ hoàng đạo, nhị thập bát tú, tốt/xấu summary,
layer-1 pass status, and basic astrology info for calendar rendering.
"""

from __future__ import annotations

from api.errors import error_response

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from api.parse_date import parse_dmy
from calendar_service import get_day_info, get_user_chart, get_month_info
from engine.hoang_dao import get_day_star, get_gio_hoang_dao
from engine.nhi_thap_bat_tu import get_nhi_thap_bat_tu
from filter import apply_layer2_filter

logger = logging.getLogger("lich_thang")

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_day_summary(
    day_info: dict,
    star_info: dict,
    tu_28: dict,
    user_chart: dict,
) -> dict:
    """Build a concise tốt/xấu summary for a single day."""
    tot: list[str] = []
    xau: list[str] = []

    # Hoàng Đạo / Hắc Đạo
    if star_info["is_hoang_dao"]:
        tot.append(f"Hoàng Đạo ({star_info['star_name']})")
    else:
        xau.append(f"Hắc Đạo ({star_info['star_name']})")

    # Trực score
    truc_score = day_info["truc_score"]
    if truc_score >= 2:
        tot.append(f"Trực {day_info['truc_name']}")
    elif truc_score < 0:
        xau.append(f"Trực {day_info['truc_name']}")

    # Sao cát ngày
    if day_info.get("has_thien_duc"):
        tot.append("Thiên Đức")
    if day_info.get("has_nguyet_duc"):
        tot.append("Nguyệt Đức")
    if day_info.get("has_thien_duc_hop"):
        tot.append("Thiên Đức Hợp")
    if day_info.get("has_nguyet_duc_hop"):
        tot.append("Nguyệt Đức Hợp")

    # Hung ngày
    if day_info.get("is_nguyet_ky"):
        xau.append("Nguyệt Kỵ")
    if day_info.get("is_tam_nuong"):
        xau.append("Tam Nương")
    if day_info.get("is_duong_cong_ky"):
        xau.append("Dương Công Kỵ")

    # 28 Tú
    if tu_28["tot_xau"] == "tốt":
        tot.append(f"Sao {tu_28['name']}")
    elif tu_28["tot_xau"] == "xấu":
        xau.append(f"Sao {tu_28['name']}")

    # Layer 2: personal xung/khac check
    l2 = apply_layer2_filter(day_info, user_chart, "MAC_DINH")
    if l2["severity"] == 3:
        xau.append("Xung tuổi")
    elif l2["severity"] == 2:
        xau.append("Khắc mệnh")

    return {
        "tot": tot,
        "xau": xau,
        "rating": "xấu" if not day_info["is_layer1_pass"] or l2["severity"] == 3
                  else "tốt" if len(tot) > len(xau)
                  else "bình thường",
    }


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/lich-thang
# ─────────────────────────────────────────────────────────────────────────────

@router.get("")
@router.get("/", include_in_schema=False)
async def lich_thang(
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: Optional[int] = Query(None, description="Giờ sinh: 0,2,4,6,8,10,11,14,16,18,20,22,23"),
    gender: Optional[int] = Query(None, description="Giới tính: 1 (nam) hoặc -1 (nữ)"),
    month: str = Query(..., description="Tháng mục tiêu, định dạng YYYY-MM"),
    tz: Optional[str] = Query(None, description="IANA timezone, e.g. Asia/Ho_Chi_Minh (default)"),
) -> JSONResponse:
    try:
        from api.tz import today_in_tz

        _today = today_in_tz(tz)

        # Parse birth_date (dd/mm/yyyy)
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

        # Get user chart (internal uses ISO format)
        user_chart = get_user_chart(bd.isoformat(), birth_time, gender)

        # Get all days in the month
        all_days = get_month_info(year, month_num, filter_passed=False)

        days_response: list[dict] = []
        for d in all_days:
            star_info = get_day_star(d["lunar_month"], d["day_chi_idx"])

            # Giờ Hoàng Đạo
            gio_tot = get_gio_hoang_dao(d["day_chi_idx"])

            # Nhị Thập Bát Tú
            tu_28 = get_nhi_thap_bat_tu(
                d["solar_year"], d["solar_month"], d["solar_day"]
            )

            # Tốt/xấu summary
            tot_xau = _build_day_summary(d, star_info, tu_28, user_chart)

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
                "gio_hoang_dao": [
                    {"chi_name": g["chi_name"], "range": f"{g['start']}-{g['end']}"}
                    for g in gio_tot
                ],
                "sao_28": {
                    "name": tu_28["name"],
                    "hanh": tu_28["hanh"],
                    "tot_xau": tu_28["tot_xau"],
                },
                "summary": tot_xau,
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
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except HTTPException:
        raise
    except Exception:
        logger.exception("Internal error in lich_thang")
        return error_response(500, "INTERNAL_ERROR")
