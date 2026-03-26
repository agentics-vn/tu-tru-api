"""
POST /v1/hop-tuoi — Two-person compatibility.

v1 (default): numeric score + grade (omit relationship_type).
v2: qualitative analysis by relationship_type (see engine.hop_tuoi).
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from api.errors import error_response
from api.parse_date import parse_dmy
from engine.can_chi import CAN_HANH, get_can_chi_year, get_menh_nap_am
from engine.dung_than import KHAC_BY, KHAC_TARGET, SINH_BY, SINH_TARGET
from engine.hop_tuoi import RELATIONSHIP_TYPES, analyze_compatibility
from engine.pillars import VALID_BIRTH_HOURS, get_tu_tru

logger = logging.getLogger("hop_tuoi")

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Ngũ Hành relationship helpers (v1)
# ─────────────────────────────────────────────────────────────────────────────

def _ngu_hanh_relation(hanh_a: str, hanh_b: str) -> tuple[str, int]:
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
    relationship_type: Optional[str] = Field(
        default=None,
        description=(
            "Để trống → phản hồi v1 (`version: 1`, điểm + grade). "
            "Một trong: PHU_THE, DOI_TAC, SEP_NHAN_VIEN, DONG_NGHIEP, BAN_BE, "
            "PHU_TU, ANH_CHI_EM, THAY_TRO → v2 (`version: 2`, verdict, criteria, …)."
        ),
    )

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

    @field_validator("relationship_type")
    @classmethod
    def relationship_type_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if v not in RELATIONSHIP_TYPES:
            allowed = ", ".join(sorted(RELATIONSHIP_TYPES))
            raise ValueError(f"relationship_type phải là một trong: {allowed}")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_person_info(bd_str: str, birth_time: Optional[int], gender: Optional[int]) -> dict:
    """Internal dict for v1 + v2 (includes indices and optional tu_tru)."""
    bd = parse_dmy(bd_str)
    year_cc = get_can_chi_year(bd.year)
    menh = get_menh_nap_am(bd.year)

    result: dict = {
        "birth_date": bd.isoformat(),
        "menh": menh["name"],
        "hanh": menh["hanh"],
    }

    if birth_time is not None:
        tu_tru = get_tu_tru(bd.isoformat(), birth_time)
        nhat_chu = tu_tru["nhat_chu"]
        result["nhatChu"] = f"{nhat_chu['can_name']} {nhat_chu['hanh']}"
        result["nhat_chu_hanh"] = nhat_chu["hanh"]
        result["year_chi_idx"] = tu_tru["year"]["chi_idx"]
        result["day_can_idx"] = tu_tru["day"]["can_idx"]
        result["tu_tru"] = tu_tru
    else:
        result["nhatChu"] = f"{year_cc['can_name']} {CAN_HANH[year_cc['can_idx']]}"
        result["nhat_chu_hanh"] = CAN_HANH[year_cc["can_idx"]]
        result["year_chi_idx"] = year_cc["chi_idx"]
        result["day_can_idx"] = year_cc["can_idx"]
        result["tu_tru"] = None

    result["gender"] = gender
    return result


def _strip_internal(p: dict) -> dict:
    out = {k: v for k, v in p.items() if k not in (
        "nhat_chu_hanh", "year_chi_idx", "day_can_idx", "tu_tru",
    )}
    return out


def _compute_compatibility_v1(p1: dict, p2: dict) -> dict:
    from engine.can_chi import is_xung

    details = []

    rel_name, rel_score = _ngu_hanh_relation(p1["hanh"], p2["hanh"])
    details.append({
        "category": "Ngũ Hành Nạp Âm",
        "score": rel_score,
        "description": f"{p1['hanh']} và {p2['hanh']} — {rel_name}.",
    })

    nc_rel, nc_score = _ngu_hanh_relation(p1["nhat_chu_hanh"], p2["nhat_chu_hanh"])
    details.append({
        "category": "Nhật Chủ tương tác",
        "score": nc_score,
        "description": f"{p1['nhat_chu_hanh']} và {p2['nhat_chu_hanh']} — {nc_rel}.",
    })

    chi_xung = is_xung(p1["year_chi_idx"], p2["year_chi_idx"])
    chi_score = 35 if chi_xung else 80
    details.append({
        "category": "Địa Chi",
        "score": chi_score,
        "description": "Địa Chi tương xung — bất lợi." if chi_xung else "Địa Chi không xung — ổn định.",
    })

    tc_rel, tc_score = _ngu_hanh_relation(
        CAN_HANH[p1["day_can_idx"]], CAN_HANH[p2["day_can_idx"]]
    )
    details.append({
        "category": "Thiên Can",
        "score": tc_score,
        "description": f"Thiên Can {CAN_HANH[p1['day_can_idx']]} và {CAN_HANH[p2['day_can_idx']]} — {tc_rel}.",
    })

    overall = round(sum(d["score"] for d in details) / len(details))
    grade = "A" if overall >= 85 else "B" if overall >= 70 else "C" if overall >= 50 else "D"

    dominant_rel = _RELATION_LABEL.get(rel_name, "Bình Hòa")

    if overall >= 80:
        summary = (
            f"Hai lá số rất tương hợp. {p1['hanh']} và {p2['hanh']} {rel_name.lower()} "
            "— mối quan hệ bền vững."
        )
        advice = (
            f"Nên chọn ngày có hành {p1['hanh']} hoặc {p2['hanh']} để tổ chức lễ cưới "
            "sẽ tăng thêm phúc khí."
        )
    elif overall >= 60:
        summary = "Hai lá số tương đối hòa hợp. Cần chú ý một số điểm xung khắc nhỏ."
        advice = "Nên tránh các ngày xung với Chi năm của hai người. Chọn ngày Hoàng Đạo để giảm thiểu bất lợi."
    else:
        summary = "Hai lá số có một số xung khắc. Cần hóa giải bằng phong thủy."
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

@router.post(
    "",
    summary="Hợp tuổi — v1 (điểm) hoặc v2 (luận theo quan hệ)",
    description=(
        "**v1 (mặc định):** không gửi `relationship_type` → `version: 1`, điểm tổng và `grade`.\n\n"
        "**v2:** gửi `relationship_type` (ví dụ `PHU_THE`, `DOI_TAC`) → `version: 2`, "
        "`verdict`, `criteria`, `reading`, `advice`. "
        "Xem `docs/api-spec.md` và body schema `relationship_type`."
    ),
)
@router.post("/", include_in_schema=False)
async def hop_tuoi_endpoint(req: HopTuoiRequest) -> JSONResponse:
    try:
        p1 = _build_person_info(req.person1_birth_date, req.person1_birth_time, req.person1_gender)
        p2 = _build_person_info(req.person2_birth_date, req.person2_birth_time, req.person2_gender)

        if req.relationship_type:
            analysis = analyze_compatibility(p1, p2, req.relationship_type)
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "version": 2,
                    "relationship_type": analysis["relationship_type"],
                    "relationship_label": analysis["relationship_label"],
                    "person1": _strip_internal(p1),
                    "person2": _strip_internal(p2),
                    "verdict": analysis["verdict"],
                    "verdict_level": analysis["verdict_level"],
                    "criteria": analysis["criteria"],
                    "reading": analysis["reading"],
                    "advice": analysis["advice"],
                },
            )

        compat = _compute_compatibility_v1(p1, p2)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "version": 1,
                "person1": _strip_internal(p1),
                "person2": _strip_internal(p2),
                **compat,
            },
        )

    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in hop_tuoi")
        return error_response(500, "INTERNAL_ERROR")
