"""
GET /v1/phong-thuy — Gợi ý phong thủy theo Dụng Thần / Kỵ Thần.

v2: purpose (mục đích), year (Phi Tinh), partner_birth_date (hóa giải đôi),
    personalization (cường nhược khi có birth_time).
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.errors import error_response
from api.parse_date import parse_dmy
from api.tz import today_in_tz
from engine.can_chi import get_menh_nap_am_from_date
from engine.dung_than import find_dung_than
from engine.phi_tinh import PhiTinhSeedError, build_phi_tinh_payload
from engine.pillars import VALID_BIRTH_HOURS, get_tu_tru
from engine.phong_thuy import (
    DEFAULT_PURPOSE,
    HUONG_BY_HANH,
    MAU_BY_HANH,
    PhongThuySeedError,
    PURPOSE_CODES,
    SO_BY_HANH,
    build_couple_harmony,
    build_personalization,
    build_purpose_payload,
    huong_xau_labeled,
)

logger = logging.getLogger("phong_thuy")

router = APIRouter()


@router.get("")
@router.get("/", include_in_schema=False)
async def phong_thuy_endpoint(
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: Optional[int] = Query(None, description="Giờ sinh"),
    gender: Optional[int] = Query(
        None,
        description="Giới tính (dự phòng tương thích; chưa dùng trong logic phong thủy)",
    ),
    tz: Optional[str] = Query(None, description="IANA timezone, e.g. Asia/Ho_Chi_Minh (default)"),
    purpose: str = Query(
        DEFAULT_PURPOSE,
        description="Mục đích: NHA_O | VAN_PHONG | CUA_HANG | PHONG_KHACH",
    ),
    year: Optional[int] = Query(
        None,
        ge=1900,
        le=2100,
        description="Năm dương lịch để tính Phi Tinh (Cửu cung lưu niên)",
    ),
    partner_birth_date: Optional[str] = Query(
        None,
        description="Sinh nhật người cùng không gian (dd/mm/yyyy) — hóa giải xung Nạp Âm",
    ),
) -> JSONResponse:
    try:
        _today = today_in_tz(tz)
        bd = parse_dmy(birth_date)
        if bd.year < 1900 or bd >= _today:
            return error_response(
                400,
                "INVALID_INPUT",
                message_vi="birth_date phải là ngày quá khứ (năm >= 1900).",
            )

        if birth_time is not None and birth_time not in VALID_BIRTH_HOURS:
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

        pur = purpose.upper().strip()
        if pur not in PURPOSE_CODES:
            allowed = ", ".join(sorted(PURPOSE_CODES))
            return error_response(
                400,
                "INVALID_INPUT",
                message_vi=f"purpose phải là một trong: {allowed}",
            )

        menh = get_menh_nap_am_from_date(bd.year, bd.month, bd.day)
        tu_tru = None
        if birth_time is not None:
            tu_tru = get_tu_tru(bd.isoformat(), birth_time)
            dung_result = find_dung_than(tu_tru)
            dung_than = dung_result["dung_than"]
            ky_than = dung_result["ky_than"]
        else:
            dung_than = menh["duong_than"]
            ky_than = menh["ky_than"]

        huong_tot = HUONG_BY_HANH.get(dung_than, [])
        huong_xau = huong_xau_labeled(ky_than)
        mau_may_man = MAU_BY_HANH.get(dung_than, [])
        mau_ky = MAU_BY_HANH.get(ky_than, [])[:2]
        so_may_man = SO_BY_HANH.get(dung_than, [])
        so_ky = SO_BY_HANH.get(ky_than, [])

        vat_pham, purpose_extras = build_purpose_payload(pur, dung_than)

        payload: dict = {
            "status": "success",
            "version": 2,
            "purpose": pur,
            "user_menh": {"hanh": menh["hanh"], "name": menh["name"]},
            "dung_than": dung_than,
            "ky_than": ky_than,
            "huong_tot": huong_tot,
            "huong_xau": huong_xau,
            "mau_may_man": mau_may_man,
            "mau_ky": mau_ky,
            "so_may_man": so_may_man,
            "so_ky": so_ky,
            "vat_pham": vat_pham,
        }

        if purpose_extras:
            payload["purpose_specific"] = purpose_extras

        pers = build_personalization(tu_tru, dung_than)
        if pers is not None:
            payload["personalization"] = pers

        if year is not None:
            payload.update(build_phi_tinh_payload(year))

        if partner_birth_date and partner_birth_date.strip():
            pbd = parse_dmy(partner_birth_date.strip())
            if pbd.year < 1900 or pbd >= _today:
                return error_response(
                    400,
                    "INVALID_INPUT",
                    message_vi="partner_birth_date phải là ngày quá khứ (năm >= 1900).",
                )
            pm = get_menh_nap_am_from_date(pbd.year, pbd.month, pbd.day)
            ch = build_couple_harmony(
                menh["hanh"],
                pm["hanh"],
                person1_menh_name=menh["name"],
                person2_menh_name=pm["name"],
            )
            if ch is not None:
                payload["couple_harmony"] = ch

        return JSONResponse(status_code=200, content=payload)

    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except (PhiTinhSeedError, PhongThuySeedError) as e:
        return error_response(
            500,
            "INTERNAL_ERROR",
            message_vi=e.message_vi,
            message_en=e.message_en,
        )
    except Exception:
        logger.exception("Internal error in phong_thuy")
        return error_response(500, "INTERNAL_ERROR")
