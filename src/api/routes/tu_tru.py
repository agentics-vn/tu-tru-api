"""
POST /v1/tu-tru — Four Pillars (Tứ Trụ / Bát Tự) endpoint.

Computes the full Four Pillars birth chart for a given birth date/time,
including Nhật Chủ, Mệnh Nạp Âm, Dụng Thần, Thập Thần, and Đại Vận.
"""

from __future__ import annotations

import logging

from api.errors import error_response
from datetime import date
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from api.parse_date import parse_dmy

from engine.bazi_solar import bazi_cycle_year
from engine.pillars import get_tu_tru, VALID_BIRTH_HOURS, BIRTH_HOUR_LABELS
from engine.can_chi import (
    CAN_NAMES,
    CHI_NAMES,
    NAP_AM_HANH,
    NAP_AM_NAMES,
    get_can_chi_year,
    get_menh_nap_am_from_date,
    get_nap_am_pair_idx,
)
from engine.dung_than import find_dung_than
from engine.thap_than import analyze_thap_than
from engine.dai_van import get_current_dai_van, get_dai_van, get_dai_van_direction

logger = logging.getLogger("tu_tru")

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Request schema
# ─────────────────────────────────────────────────────────────────────────────

class TuTruRequest(BaseModel):
    birth_date: str
    birth_time: Optional[int] = None
    gender: Optional[int] = None

    @field_validator("birth_date")
    @classmethod
    def birth_date_must_be_past(cls, v: str) -> str:
        d = parse_dmy(v)
        if d.year < 1900:
            raise ValueError("birth_date phải có năm >= 1900")
        if d >= date.today():
            raise ValueError("birth_date phải là ngày quá khứ")
        return v

    @field_validator("birth_time")
    @classmethod
    def birth_time_must_be_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in VALID_BIRTH_HOURS:
            raise ValueError(
                f"birth_time phải là một trong {sorted(VALID_BIRTH_HOURS)}"
            )
        return v

    @field_validator("gender")
    @classmethod
    def gender_must_be_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in (1, -1):
            raise ValueError("gender phải là 1 (nam) hoặc -1 (nữ)")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_pillar_display(pillar: dict) -> dict:
    """Format a single pillar for API output."""
    can_idx = pillar["can_idx"]
    chi_idx = pillar["chi_idx"]
    pair_idx = get_nap_am_pair_idx(can_idx, chi_idx)
    return {
        "can_chi": f"{pillar['can_name']} {pillar['chi_name']}",
        "can": {"idx": can_idx, "name": pillar["can_name"]},
        "chi": {"idx": chi_idx, "name": pillar["chi_name"]},
        "nap_am": {
            "hanh": NAP_AM_HANH[pair_idx],
            "name": NAP_AM_NAMES[pair_idx],
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /v1/tu-tru
# ─────────────────────────────────────────────────────────────────────────────

@router.post("")
@router.post("/", include_in_schema=False)
async def tu_tru_endpoint(req: TuTruRequest) -> JSONResponse:
    try:
        bd = parse_dmy(req.birth_date)
        birth_date_str = bd.isoformat()
        birth_year = bd.year

        # ── Year-level info (always available) ──────────────────────────
        cycle_y = bazi_cycle_year(bd.year, bd.month, bd.day)
        year_cc = get_can_chi_year(cycle_y)
        menh = get_menh_nap_am_from_date(bd.year, bd.month, bd.day)

        result: dict = {
            "status": "success",
            "birth_date": birth_date_str,
            "birth_year_can_chi": f"{year_cc['can_name']} {year_cc['chi_name']}",
            "menh": {
                "nap_am_name": menh["name"],
                "hanh": menh["hanh"],
                "duong_than": menh["duong_than"],
                "ky_than": menh["ky_than"],
            },
        }

        # ── Full Tứ Trụ (requires birth_time) ──────────────────────────
        if req.birth_time is not None:
            tu_tru = get_tu_tru(birth_date_str, req.birth_time)

            result["birth_time"] = req.birth_time
            result["birth_time_label"] = BIRTH_HOUR_LABELS[req.birth_time]
            result["tu_tru_display"] = tu_tru["display"]

            result["pillars"] = {
                "year": _build_pillar_display(tu_tru["year"]),
                "month": _build_pillar_display(tu_tru["month"]),
                "day": _build_pillar_display(tu_tru["day"]),
                "hour": _build_pillar_display(tu_tru["hour"]),
            }

            # Nhật Chủ (Day Master)
            nhat_chu = tu_tru["nhat_chu"]
            result["nhat_chu"] = {
                "can_name": nhat_chu["can_name"],
                "hanh": nhat_chu["hanh"],
            }

            # Dụng Thần analysis
            dung_than_result = find_dung_than(tu_tru)
            result["chart_strength"] = dung_than_result["strength"]
            result["dung_than"] = {
                "element": dung_than_result["dung_than"],
                "description": "Nguyên tố hỗ trợ tốt nhất cho lá số",
            }
            result["hi_than"] = {
                "element": dung_than_result["hi_than"],
                "description": "Nguyên tố hỗ trợ phụ",
            }
            result["ky_than"] = {
                "element": dung_than_result["ky_than"],
                "description": "Nguyên tố bất lợi nhất",
            }
            result["cuu_than"] = {
                "element": dung_than_result["cuu_than"],
                "description": "Nguyên tố sinh ra Kỵ Thần",
            }

            # Thập Thần profile
            thap_than = analyze_thap_than(tu_tru)
            result["thap_than"] = {
                "year": {
                    "key": thap_than["year_god"]["key"],
                    "name": thap_than["year_god"]["name"],
                    "category": thap_than["year_god"]["category"],
                },
                "month": {
                    "key": thap_than["month_god"]["key"],
                    "name": thap_than["month_god"]["name"],
                    "category": thap_than["month_god"]["category"],
                },
                "hour": {
                    "key": thap_than["hour_god"]["key"],
                    "name": thap_than["hour_god"]["name"],
                    "category": thap_than["hour_god"]["category"],
                },
                "dominant": {
                    "key": thap_than["dominant_god"]["key"],
                    "name": thap_than["dominant_god"]["name"],
                },
            }

            # Đại Vận (requires gender)
            if req.gender:
                result["gender"] = req.gender

                cycles = get_dai_van(tu_tru, req.gender, birth_date_str)
                current = get_current_dai_van(tu_tru, req.gender, birth_date_str)
                dir_step = get_dai_van_direction(tu_tru["year"]["can_idx"], req.gender)

                result["dai_van"] = {
                    "direction": "thuận" if dir_step == 1 else "nghịch",
                    "current": (
                        {
                            "display": current["display"],
                            "hanh": current["can_hanh"],
                            "nap_am_hanh": current["nap_am_hanh"],
                            "age_range": f"{current['start_age']}-{current['end_age']}",
                        }
                        if current
                        else None
                    ),
                    "cycles": [
                        {
                            "cycle_num": c["cycle_num"],
                            "display": c["display"],
                            "hanh": c["can_hanh"],
                            "nap_am_hanh": c["nap_am_hanh"],
                            "age_range": f"{c['start_age']}-{c['end_age']}",
                        }
                        for c in cycles
                    ],
                }
        else:
            result["_note"] = (
                "Chỉ có thông tin cơ bản (mệnh Nạp Âm). "
                "Cung cấp birth_time để xem đầy đủ Tứ Trụ, Dụng Thần, Thập Thần."
            )

        return JSONResponse(status_code=200, content=result)

    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in tu_tru")
        return error_response(500, "INTERNAL_ERROR")
