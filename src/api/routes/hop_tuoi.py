"""
POST /v1/hop-tuoi — Two-person compatibility analysis.

Compares two birth charts based on Ngũ Hành Nạp Âm, Thiên Can, Địa Chi,
and Nhật Chủ interactions to produce a compatibility score.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from api.parse_date import parse_dmy
from engine.can_chi import (
    CAN_HANH,
    CHI_HANH,
    get_can_chi_year,
    get_menh_nap_am,
    get_nap_am_pair_idx,
    is_xung,
)
from engine.pillars import get_tu_tru, VALID_BIRTH_HOURS, BIRTH_HOUR_LABELS
from engine.dung_than import find_dung_than, SINH_BY, SINH_TARGET, KHAC_BY, KHAC_TARGET

logger = logging.getLogger("hop_tuoi")

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Ngũ Hành relationship helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ngu_hanh_relation(hanh_a: str, hanh_b: str) -> tuple[str, int]:
    """
    Return (relationship_name, score_bonus) for two elements.
    """
    if hanh_a == hanh_b:
        return ("Tỷ Hòa", 75)
    if SINH_BY.get(hanh_a) == hanh_b or SINH_TARGET.get(hanh_a) == hanh_b:
        return ("Tương Sinh", 90)
    if KHAC_BY.get(hanh_a) == hanh_b or KHAC_TARGET.get(hanh_a) == hanh_b:
        return ("Tương Khắc", 40)
    return ("Bình Hòa", 60)


_RELATION_LABEL = {
    "Tương Sinh": "Tương Sinh",
    "Tương Khắc": "Tương Khắc",
    "Tỷ Hòa": "Bình Hòa",
    "Bình Hòa": "Bình Hòa",
}


# ─────────────────────────────────────────────────────────────────────────────
# Request schema
# ─────────────────────────────────────────────────────────────────────────────

class HopTuoiRequest(BaseModel):
    person1_birth_date: str
    person1_birth_time: Optional[int] = None
    person1_gender: Optional[int] = None
    person2_birth_date: str
    person2_birth_time: Optional[int] = None
    person2_gender: Optional[int] = None

    @field_validator("person1_birth_date", "person2_birth_date")
    @classmethod
    def birth_date_must_be_past(cls, v: str) -> str:
        d = parse_dmy(v)
        if d.year < 1900:
            raise ValueError("birth_date phải có năm >= 1900")
        if d >= date.today():
            raise ValueError("birth_date phải là ngày quá khứ")
        return v

    @field_validator("person1_birth_time", "person2_birth_time")
    @classmethod
    def birth_time_must_be_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in VALID_BIRTH_HOURS:
            raise ValueError(f"birth_time phải là một trong {sorted(VALID_BIRTH_HOURS)}")
        return v

    @field_validator("person1_gender", "person2_gender")
    @classmethod
    def gender_must_be_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in (1, -1):
            raise ValueError("gender phải là 1 (nam) hoặc -1 (nữ)")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_person_info(bd_str: str, birth_time: Optional[int], gender: Optional[int]) -> dict:
    """Build person summary dict."""
    bd = parse_dmy(bd_str)
    year_cc = get_can_chi_year(bd.year)
    menh = get_menh_nap_am(bd.year)

    result = {
        "birth_date": bd.isoformat(),
        "menh": menh["name"],
        "hanh": menh["hanh"],
    }

    if birth_time is not None:
        tu_tru = get_tu_tru(bd.isoformat(), birth_time)
        nhat_chu = tu_tru["nhat_chu"]
        result["nhatChu"] = f"{nhat_chu['can_name']} {nhat_chu['hanh']}"
        result["nhat_chu_hanh"] = nhat_chu["hanh"]
        result["year_chi_idx"] = year_cc["chi_idx"]
        result["day_can_idx"] = tu_tru["day"]["can_idx"]
    else:
        result["nhatChu"] = f"{year_cc['can_name']} {CAN_HANH[year_cc['can_idx']]}"
        result["nhat_chu_hanh"] = CAN_HANH[year_cc["can_idx"]]
        result["year_chi_idx"] = year_cc["chi_idx"]
        result["day_can_idx"] = year_cc["can_idx"]

    return result


def _compute_compatibility(p1: dict, p2: dict) -> dict:
    """Compute detailed compatibility scores."""
    details = []

    # 1. Ngũ Hành Nạp Âm
    rel_name, rel_score = _ngu_hanh_relation(p1["hanh"], p2["hanh"])
    details.append({
        "category": "Ngũ Hành Nạp Âm",
        "score": rel_score,
        "description": f"{p1['hanh']} và {p2['hanh']} — {rel_name}.",
    })

    # 2. Nhật Chủ interaction
    nc_rel, nc_score = _ngu_hanh_relation(p1["nhat_chu_hanh"], p2["nhat_chu_hanh"])
    details.append({
        "category": "Nhật Chủ tương tác",
        "score": nc_score,
        "description": f"{p1['nhat_chu_hanh']} và {p2['nhat_chu_hanh']} — {nc_rel}.",
    })

    # 3. Địa Chi (year branch)
    chi_xung = is_xung(p1["year_chi_idx"], p2["year_chi_idx"])
    chi_score = 35 if chi_xung else 80
    details.append({
        "category": "Địa Chi",
        "score": chi_score,
        "description": "Địa Chi tương xung — bất lợi." if chi_xung else "Địa Chi không xung — ổn định.",
    })

    # 4. Thiên Can
    tc_rel, tc_score = _ngu_hanh_relation(
        CAN_HANH[p1["day_can_idx"]], CAN_HANH[p2["day_can_idx"]]
    )
    details.append({
        "category": "Thiên Can",
        "score": tc_score,
        "description": f"Thiên Can {CAN_HANH[p1['day_can_idx']]} và {CAN_HANH[p2['day_can_idx']]} — {tc_rel}.",
    })

    # Overall
    overall = round(sum(d["score"] for d in details) / len(details))
    grade = "A" if overall >= 85 else "B" if overall >= 70 else "C" if overall >= 50 else "D"

    # Summary
    dominant_rel = _RELATION_LABEL.get(rel_name, "Bình Hòa")

    if overall >= 80:
        summary = f"Hai lá số rất tương hợp. {p1['hanh']} và {p2['hanh']} {rel_name.lower()} — mối quan hệ bền vững."
        advice = f"Nên chọn ngày có hành {p1['hanh']} hoặc {p2['hanh']} để tổ chức lễ cưới sẽ tăng thêm phúc khí."
    elif overall >= 60:
        summary = f"Hai lá số tương đối hòa hợp. Cần chú ý một số điểm xung khắc nhỏ."
        advice = "Nên tránh các ngày xung với Chi năm của hai người. Chọn ngày Hoàng Đạo để giảm thiểu bất lợi."
    else:
        summary = f"Hai lá số có một số xung khắc. Cần hóa giải bằng phong thủy."
        advice = "Nên nhờ thầy xem kỹ và chọn ngày cẩn thận. Có thể dùng vật phẩm phong thủy hành trung gian để hóa giải."

    return {
        "overall_score": overall,
        "grade": grade,
        "ngu_hanh_relation": dominant_rel,
        "details": details,
        "summary": summary,
        "advice": advice,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /v1/hop-tuoi
# ─────────────────────────────────────────────────────────────────────────────

@router.post("")
@router.post("/")
async def hop_tuoi_endpoint(req: HopTuoiRequest) -> JSONResponse:
    try:
        p1 = _build_person_info(req.person1_birth_date, req.person1_birth_time, req.person1_gender)
        p2 = _build_person_info(req.person2_birth_date, req.person2_birth_time, req.person2_gender)

        compat = _compute_compatibility(p1, p2)

        # Clean internal keys before response
        for p in (p1, p2):
            p.pop("nhat_chu_hanh", None)
            p.pop("year_chi_idx", None)
            p.pop("day_can_idx", None)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "person1": p1,
                "person2": p2,
                **compat,
            },
        )

    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "error_code": "INVALID_INPUT", "message": str(e)},
        )
    except Exception:
        logger.exception("Internal error in hop_tuoi")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error_code": "INTERNAL_ERROR", "message": "Đã có lỗi xảy ra."},
        )
