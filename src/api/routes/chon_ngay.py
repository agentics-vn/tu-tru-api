"""
POST /v1/chon-ngay — Auspicious date selection endpoint.

Validates the request, runs the 3-layer filtering/scoring pipeline,
and returns recommended_dates + dates_to_avoid per docs/api-spec.md.
"""

from __future__ import annotations

import json
import logging
import traceback
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator

from api.parse_date import parse_dmy

# ── Engine imports (Python ports of the JS engine modules) ─────────────────
from calendar_service import get_day_info, get_user_chart, get_can_chi_year, CAN_NAMES, CHI_NAMES
from filter import apply_layer2_filter
from scoring import compute_score, compute_score_breakdown
from engine.hoang_dao import get_gio_hoang_dao
from engine.pillars import VALID_BIRTH_HOURS, BIRTH_HOUR_LABELS

logger = logging.getLogger("chon_ngay")

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Load intent rules from seed data
# ─────────────────────────────────────────────────────────────────────────────

_INTENT_RULES_PATH = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "seed" / "intent-rules.json"
with open(_INTENT_RULES_PATH, encoding="utf-8") as f:
    INTENT_RULES: dict = json.load(f)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

MAX_RANGE_DAYS = 90
TOP_N_DEFAULT = 3
TOP_N_MAX = 10

# Map API-facing intent → intent-rules.json key
INTENT_ALIAS: dict[str, str] = {
    "CUOI_HOI": "DAM_CUOI",
}

LUNAR_MONTH_NAMES = [
    "", "Giêng", "Hai", "Ba", "Tư", "Năm", "Sáu",
    "Bảy", "Tám", "Chín", "Mười", "Một", "Chạp",
]


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class IntentEnum(str, Enum):
    # ── Kinh doanh / Tài chính ──
    KHAI_TRUONG = "KHAI_TRUONG"
    KY_HOP_DONG = "KY_HOP_DONG"
    CAU_TAI = "CAU_TAI"
    NHAM_CHUC = "NHAM_CHUC"
    # ── Hôn nhân / Gia đình ──
    AN_HOI = "AN_HOI"
    CUOI_HOI = "CUOI_HOI"          # alias → DAM_CUOI
    DAM_CUOI = "DAM_CUOI"
    CAU_TU = "CAU_TU"
    # ── Xây dựng / Nhà đất ──
    DONG_THO = "DONG_THO"
    NHAP_TRACH = "NHAP_TRACH"
    LAM_NHA = "LAM_NHA"
    MUA_NHA_DAT = "MUA_NHA_DAT"
    XAY_BEP = "XAY_BEP"
    LAM_GIUONG = "LAM_GIUONG"
    DAO_GIENG = "DAO_GIENG"
    # ── Tang lễ ──
    AN_TANG = "AN_TANG"
    CAI_TANG = "CAI_TANG"
    # ── Di chuyển ──
    XUAT_HANH = "XUAT_HANH"
    DI_CHUYEN_NGOAI = "DI_CHUYEN_NGOAI"
    # ── Tâm linh / Sức khỏe ──
    TE_TU = "TE_TU"
    GIAI_HAN = "GIAI_HAN"
    KHAM_BENH = "KHAM_BENH"
    PHAU_THUAT = "PHAU_THUAT"
    # ── Học tập / Pháp lý ──
    NHAP_HOC_THI_CU = "NHAP_HOC_THI_CU"
    KIEN_TUNG = "KIEN_TUNG"
    # ── Nông nghiệp ──
    TRONG_CAY = "TRONG_CAY"
    # ── Mặc định ──
    MAC_DINH = "MAC_DINH"


class GenderEnum(int, Enum):
    MALE = 1
    FEMALE = -1


class ChonNgayRequest(BaseModel):
    birth_date: str = Field(..., description="Ngày sinh dd/mm/yyyy")
    birth_time: Optional[int] = Field(
        default=None,
        description="Giờ sinh: 0,2,4,6,8,10,11,14,16,18,20,22,23",
    )
    gender: Optional[GenderEnum] = Field(
        default=None,
        description="Giới tính: 1 (nam) hoặc -1 (nữ) (bắt buộc cho Đại Vận)",
    )
    intent: IntentEnum
    range_start: str = Field(..., description="Ngày bắt đầu dd/mm/yyyy")
    range_end: str = Field(..., description="Ngày kết thúc dd/mm/yyyy")
    top_n: Optional[int] = Field(default=TOP_N_DEFAULT, ge=1, le=TOP_N_MAX)

    @field_validator("birth_date")
    @classmethod
    def birth_date_must_be_past(cls, v: str) -> str:
        d = parse_dmy(v)
        if d.year < 1900:
            raise ValueError("Năm sinh phải >= 1900")
        if d >= date.today():
            raise ValueError("Ngày sinh phải là ngày trong quá khứ")
        return v

    @field_validator("range_start", "range_end")
    @classmethod
    def range_dates_must_be_valid(cls, v: str) -> str:
        parse_dmy(v)  # validates format
        return v

    @field_validator("birth_time")
    @classmethod
    def birth_time_valid_values(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v not in VALID_BIRTH_HOURS:
            raise ValueError(
                f"Giờ sinh phải là một trong {sorted(VALID_BIRTH_HOURS)}, nhận được {v}"
            )
        return v

    @model_validator(mode="after")
    def validate_range(self) -> "ChonNgayRequest":
        start = parse_dmy(self.range_start)
        end = parse_dmy(self.range_end)
        if end < start:
            raise ValueError("Ngày kết thúc phải bằng hoặc sau ngày bắt đầu")
        diff = (end - start).days
        if diff > MAX_RANGE_DAYS:
            raise ValueError(
                f"Khoảng cách không được vượt quá {MAX_RANGE_DAYS} ngày"
            )
        return self


# ─────────────────────────────────────────────────────────────────────────────
# Error response helper
# ─────────────────────────────────────────────────────────────────────────────

def _error_response(status_code: int, error_code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "error_code": error_code,
            "message": message,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _each_day_in_range(start: date, end: date) -> list[date]:
    """Return every date from start to end inclusive."""
    days: list[date] = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += timedelta(days=1)
    return days


def _format_lunar_date(day_info: dict) -> str:
    """Format lunar date string like 'Ngày 29 tháng Chạp năm Ất Tỵ'."""
    lm = day_info["lunar_month"]
    month_name = LUNAR_MONTH_NAMES[lm] if 1 <= lm <= 12 else str(lm)
    year_cc = get_can_chi_year(day_info["lunar_year"])
    return (
        f"Ngày {day_info['lunar_day']} tháng {month_name} "
        f"năm {year_cc['can_name']} {year_cc['chi_name']}"
    )


ELEMENT_PLAIN_VI: dict[str, str] = {
    "Kim": "Kim (kim loại)", "Mộc": "Mộc (cây cỏ)",
    "Thủy": "Thủy (nước)", "Hỏa": "Hỏa (lửa)", "Thổ": "Thổ (đất)",
}

STRENGTH_PLAIN_VI: dict[str, str] = {
    "nhược": "thân nhược — cần bổ trợ thêm năng lượng phù hợp",
    "vượng": "thân vượng — cần cân bằng, tránh thừa năng lượng",
}


def _build_bat_tu_summary(user_chart: dict) -> dict:
    """Build the bat_tu_summary section for the response."""
    summary: dict = {
        "ngu_hanh_menh": user_chart["menh_hanh"],
        "duong_than": user_chart["duong_than"],
        "ky_than": user_chart["ky_than"],
    }

    # Enrich with Tứ Trụ data when available
    if user_chart.get("tu_tru"):
        tu_tru = user_chart["tu_tru"]
        summary["tu_tru"] = {
            "display": tu_tru["display"],
            "year": {
                "can_name": tu_tru["year"]["can_name"],
                "chi_name": tu_tru["year"]["chi_name"],
            },
            "month": {
                "can_name": tu_tru["month"]["can_name"],
                "chi_name": tu_tru["month"]["chi_name"],
            },
            "day": {
                "can_name": tu_tru["day"]["can_name"],
                "chi_name": tu_tru["day"]["chi_name"],
            },
            "hour": {
                "can_name": tu_tru["hour"]["can_name"],
                "chi_name": tu_tru["hour"]["chi_name"],
            },
        }
        summary["nhat_chu"] = {
            "can_name": tu_tru["nhat_chu"]["can_name"],
            "hanh": tu_tru["nhat_chu"]["hanh"],
        }

    if user_chart.get("dung_than"):
        summary["dung_than"] = user_chart["dung_than"]
        summary["hi_than"] = user_chart.get("hi_than")
        summary["chart_strength"] = user_chart.get("chart_strength")

    if user_chart.get("current_dai_van"):
        dv = user_chart["current_dai_van"]
        summary["current_dai_van"] = {
            "display": dv["display"],
            "hanh": dv["can_hanh"],
            "age_range": f"{dv['start_age']}-{dv['end_age']}",
        }

    # ── Plain-language summary for non-experts ──
    menh = user_chart["menh_hanh"]
    plain_parts = [f"Mệnh bạn thuộc hành {ELEMENT_PLAIN_VI.get(menh, menh)}."]

    if user_chart.get("chart_strength"):
        strength = user_chart["chart_strength"]
        plain_parts.append(
            f"Lá số của bạn {STRENGTH_PLAIN_VI.get(strength, strength)}."
        )

    if user_chart.get("dung_than"):
        dung = user_chart["dung_than"]
        plain_parts.append(
            f"Yếu tố có lợi nhất cho bạn là hành "
            f"{ELEMENT_PLAIN_VI.get(dung, dung)} — "
            f"nên chọn ngày có năng lượng này."
        )

    if user_chart.get("hi_than"):
        hi = user_chart["hi_than"]
        plain_parts.append(
            f"Hành {ELEMENT_PLAIN_VI.get(hi, hi)} cũng tốt cho bạn."
        )

    if user_chart.get("ky_than_v2"):
        ky = user_chart["ky_than_v2"]
        plain_parts.append(
            f"Nên tránh những ngày có năng lượng hành "
            f"{ELEMENT_PLAIN_VI.get(ky, ky)} vì xung khắc với mệnh bạn."
        )

    if user_chart.get("current_dai_van"):
        dv = user_chart["current_dai_van"]
        dv_hanh = dv.get("can_hanh", "")
        dung = user_chart.get("dung_than", "")
        hi = user_chart.get("hi_than", "")
        ky = user_chart.get("ky_than_v2", "")
        cuu = user_chart.get("cuu_than", "")

        if dv_hanh == dung or dv_hanh == hi:
            plain_parts.append(
                f"Giai đoạn vận may hiện tại ({dv['start_age']}-{dv['end_age']} tuổi) "
                f"đang thuận lợi cho bạn."
            )
        elif dv_hanh == ky or dv_hanh == cuu:
            plain_parts.append(
                f"Giai đoạn vận may hiện tại ({dv['start_age']}-{dv['end_age']} tuổi) "
                f"không thuận lợi lắm — cần chọn ngày cẩn thận hơn."
            )

    summary["summary_vi"] = " ".join(plain_parts)

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# POST /v1/chon-ngay
# ─────────────────────────────────────────────────────────────────────────────

@router.post("")
@router.post("/")
async def chon_ngay(req: ChonNgayRequest) -> JSONResponse:
    try:
        intent = req.intent.value
        top_n = req.top_n or TOP_N_DEFAULT
        birth_date_str = parse_dmy(req.birth_date).isoformat()

        # ── Resolve intent key for intent-rules.json ──────────────────────
        rule_key = INTENT_ALIAS.get(intent, intent)
        intent_rule = INTENT_RULES.get(
            rule_key,
            INTENT_RULES.get("MAC_DINH", {"bonus_sao": [], "forbidden_sao": []}),
        )

        # ── User chart (Layer 2 input) ────────────────────────────────────
        gender_str = req.gender.value if req.gender else None
        user_chart = get_user_chart(birth_date_str, req.birth_time, gender_str)

        # ── Iterate date range ────────────────────────────────────────────
        all_dates = _each_day_in_range(parse_dmy(req.range_start), parse_dmy(req.range_end))
        total_scanned = len(all_dates)

        layer1_passed = 0
        layer2_passed = 0
        scored_days: list[dict] = []
        dates_to_avoid: list[dict] = []

        for d in all_dates:
            date_str = d.isoformat()

            # Layer 1
            day_info = get_day_info(date_str)
            if not day_info["is_layer1_pass"]:
                continue
            layer1_passed += 1

            # Layer 2
            filter_result = apply_layer2_filter(day_info, user_chart, rule_key)

            if not filter_result["pass"]:
                # severity 3 → dates_to_avoid
                avoid_entry: dict = {
                    "date": date_str,
                    "reason_vi": ". ".join(filter_result["reasons"]) + ". Tuyệt đối tránh.",
                    "severity": filter_result["severity"],
                }
                if filter_result["severity"] == 3:
                    avoid_entry["summary_vi"] = (
                        "Ngày này xung khắc trực tiếp với tuổi của bạn. "
                        "Tuyệt đối không nên chọn ngày này cho bất kỳ việc quan trọng nào."
                    )
                dates_to_avoid.append(avoid_entry)
                continue

            layer2_passed += 1

            # Layer 3 — scoring
            score_result = compute_score(
                day_info, user_chart, rule_key, intent_rule, filter_result
            )

            # severity 2 days still pass but also appear in dates_to_avoid
            if filter_result["severity"] == 2:
                dates_to_avoid.append({
                    "date": date_str,
                    "reason_vi": ". ".join(filter_result["reasons"]),
                    "severity": 2,
                    "summary_vi": "Ngày này có yếu tố không hợp với mệnh bạn. Nếu có thể, nên chọn ngày khác.",
                })

            scored_days.append({"day_info": day_info, "score_result": score_result})

        # ── Sort and pick top N ───────────────────────────────────────────
        scored_days.sort(key=lambda x: x["score_result"]["score"], reverse=True)
        top_days = scored_days[:top_n]

        # ── Safety invariant: severity=3 MUST NEVER appear in recommended ─
        avoid_sev3_dates = {
            d["date"] for d in dates_to_avoid if d["severity"] == 3
        }
        recommended_dates = [
            {
                "date": d["day_info"]["date"],
                "lunar_date": _format_lunar_date(d["day_info"]),
                "score": d["score_result"]["score"],
                "grade": d["score_result"]["grade"],
                "truc": d["day_info"]["truc_name"],
                "sao_cat": d["score_result"]["bonus_sao"],
                "sao_hung": d["score_result"]["penalty_sao"],
                "nguhanh_day": d["day_info"]["day_nap_am_hanh"],
                "reason_vi": ". ".join(d["score_result"]["reasons_vi"]),
                "summary_vi": d["score_result"]["summary_vi"],
                "time_slots": [
                        f"{g['start']}-{g['end']}"
                        for g in get_gio_hoang_dao(d["day_info"]["day_chi_idx"])
                    ],
            }
            for d in top_days
            if d["day_info"]["date"] not in avoid_sev3_dates
        ]

        # ── 422 if nothing survived ───────────────────────────────────────
        if not recommended_dates:
            return _error_response(
                422,
                "NO_DATES_FOUND",
                "Không tìm được ngày tốt nào trong khoảng thời gian đã chọn.",
            )

        # ── Build response ────────────────────────────────────────────────
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "meta": {
                    "intent": intent,
                    "range_scanned": {
                        "from": req.range_start,
                        "to": req.range_end,
                    },
                    "total_days_scanned": total_scanned,
                    "days_passed_layer1": layer1_passed,
                    "days_passed_layer2": layer2_passed,
                    "bat_tu_summary": _build_bat_tu_summary(user_chart),
                },
                "recommended_dates": recommended_dates,
                "dates_to_avoid": dates_to_avoid,
            },
        )

    except Exception:
        logger.exception("Internal error in chon_ngay")
        return _error_response(
            500,
            "INTERNAL_ERROR",
            "Đã có lỗi xảy ra. Vui lòng thử lại sau.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# POST /v1/chon-ngay/detail — Single-day detailed analysis
# ─────────────────────────────────────────────────────────────────────────────

class DetailRequest(BaseModel):
    birth_date: str = Field(..., description="Ngày sinh dd/mm/yyyy")
    birth_time: Optional[int] = Field(
        default=None,
        description="Giờ sinh: 0,2,4,6,8,10,11,14,16,18,20,22,23",
    )
    gender: Optional[GenderEnum] = Field(
        default=None,
        description="Giới tính: 1 (nam) hoặc -1 (nữ) (bắt buộc cho Đại Vận)",
    )
    intent: IntentEnum
    date: str = Field(..., description="Ngày cần phân tích dd/mm/yyyy")

    @field_validator("birth_date")
    @classmethod
    def birth_date_must_be_past(cls, v: str) -> str:
        d = parse_dmy(v)
        if d.year < 1900:
            raise ValueError("Năm sinh phải >= 1900")
        if d >= date.today():
            raise ValueError("Ngày sinh phải là ngày trong quá khứ")
        return v

    @field_validator("date")
    @classmethod
    def date_must_be_valid(cls, v: str) -> str:
        parse_dmy(v)
        return v

    @field_validator("birth_time")
    @classmethod
    def birth_time_valid_values(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v not in VALID_BIRTH_HOURS:
            raise ValueError(
                f"Giờ sinh phải là một trong {sorted(VALID_BIRTH_HOURS)}, nhận được {v}"
            )
        return v


def _ngu_hanh_relation(day_hanh: str, menh_hanh: str) -> str:
    """Return the Ngũ Hành relationship between day and mệnh."""
    SINH_MAP = {"Kim": "Thủy", "Thủy": "Mộc", "Mộc": "Hỏa", "Hỏa": "Thổ", "Thổ": "Kim"}
    KHAC_MAP = {"Kim": "Mộc", "Mộc": "Thổ", "Thổ": "Thủy", "Thủy": "Hỏa", "Hỏa": "Kim"}

    if day_hanh == menh_hanh:
        return "bình hòa"
    if SINH_MAP.get(day_hanh) == menh_hanh:
        return "ngày sinh mệnh (tốt)"
    if SINH_MAP.get(menh_hanh) == day_hanh:
        return "mệnh sinh ngày (hao)"
    if KHAC_MAP.get(day_hanh) == menh_hanh:
        return "ngày khắc mệnh (xấu)"
    if KHAC_MAP.get(menh_hanh) == day_hanh:
        return "mệnh khắc ngày (trung bình)"
    return "không xác định"


@router.post("/detail")
async def chon_ngay_detail(req: DetailRequest) -> JSONResponse:
    """Return detailed analysis for a single date."""
    try:
        intent = req.intent.value
        target_date = parse_dmy(req.date)
        birth_date_str = parse_dmy(req.birth_date).isoformat()

        # Resolve intent
        rule_key = INTENT_ALIAS.get(intent, intent)
        intent_rule = INTENT_RULES.get(
            rule_key,
            INTENT_RULES.get("MAC_DINH", {"bonus_sao": [], "forbidden_sao": []}),
        )

        # User chart
        gender_str = req.gender.value if req.gender else None
        user_chart = get_user_chart(birth_date_str, req.birth_time, gender_str)

        # ── Layer 1 ─────────────────────────────────────────────────────────
        date_str = target_date.isoformat()
        day_info = get_day_info(date_str)

        layer1_detail = {
            "is_pass": day_info["is_layer1_pass"],
            "truc": {
                "name": day_info["truc_name"],
                "idx": day_info["truc_idx"],
                "score": day_info["truc_score"],
            },
            "hung_ngay": {
                "is_nguyet_ky": day_info["is_nguyet_ky"],
                "is_tam_nuong": day_info["is_tam_nuong"],
                "is_duong_cong_ky": day_info["is_duong_cong_ky"],
            },
            "is_truc_pha": day_info.get("is_truc_pha", False),
            "is_truc_nguy": day_info.get("is_truc_nguy", False),
            "sao_tot": {
                "thien_duc": day_info.get("has_thien_duc", False),
                "thien_duc_hop": day_info.get("has_thien_duc_hop", False),
                "nguyet_duc": day_info.get("has_nguyet_duc", False),
                "nguyet_duc_hop": day_info.get("has_nguyet_duc_hop", False),
                "thien_xa": day_info.get("has_thien_xa", False),
            },
        }

        # If Layer 1 fails, return early with just layer1 info
        if not day_info["is_layer1_pass"]:
            fail_reasons = []
            if day_info["is_nguyet_ky"]:
                fail_reasons.append("Nguyệt Kỵ")
            if day_info["is_tam_nuong"]:
                fail_reasons.append("Tam Nương")
            if day_info["is_duong_cong_ky"]:
                fail_reasons.append("Dương Công Kỵ")
            if day_info.get("is_truc_pha"):
                fail_reasons.append("Trực Phá")
            if day_info.get("is_truc_nguy"):
                fail_reasons.append("Trực Nguy")

            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "date": date_str,
                    "lunar_date": _format_lunar_date(day_info),
                    "can_chi_day": f"{day_info['day_can_name']} {day_info['day_chi_name']}",
                    "nguhanh_day": day_info["day_nap_am_hanh"],
                    "verdict": "Nên tránh",
                    "verdict_vi": "Ngày xấu — không qua được bộ lọc cơ bản.",
                    "layer1": layer1_detail,
                    "layer1_fail_reasons": fail_reasons,
                    "layer2": None,
                    "layer3": None,
                    "time_slots": None,
                },
            )

        # ── Layer 2 ─────────────────────────────────────────────────────────
        filter_result = apply_layer2_filter(day_info, user_chart, rule_key)

        ngu_hanh_rel = _ngu_hanh_relation(
            day_info["day_nap_am_hanh"], user_chart["menh_hanh"]
        )

        layer2_detail = {
            "is_pass": filter_result["pass"],
            "severity": filter_result["severity"],
            "reasons": filter_result["reasons"],
            "ngu_hanh_match": {
                "day_hanh": day_info["day_nap_am_hanh"],
                "menh_hanh": user_chart["menh_hanh"],
                "relation": ngu_hanh_rel,
            },
            "dia_chi_clash": not filter_result["pass"] and filter_result["severity"] == 3,
        }

        # If Layer 2 fails (severity 3), return early
        if not filter_result["pass"]:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "date": date_str,
                    "lunar_date": _format_lunar_date(day_info),
                    "can_chi_day": f"{day_info['day_can_name']} {day_info['day_chi_name']}",
                    "nguhanh_day": day_info["day_nap_am_hanh"],
                    "verdict": "Cấm",
                    "verdict_vi": (
                        "Tuyệt đối tránh — ngày xung khắc trực tiếp với tuổi của bạn."
                        if filter_result["severity"] == 3
                        else ". ".join(filter_result["reasons"])
                    ),
                    "severity": filter_result["severity"],
                    "layer1": layer1_detail,
                    "layer2": layer2_detail,
                    "layer3": None,
                    "time_slots": None,
                },
            )

        # ── Layer 3 — detailed scoring ──────────────────────────────────────
        score_result = compute_score_breakdown(
            day_info, user_chart, rule_key, intent_rule, filter_result
        )

        layer3_detail = {
            "base_score": 50,
            "final_score": score_result["score"],
            "grade": score_result["grade"],
            "breakdown": score_result["breakdown"],
            "bonus_sao": score_result["bonus_sao"],
            "penalty_sao": score_result["penalty_sao"],
        }

        # ── Time slots ──────────────────────────────────────────────────────
        gio_list = get_gio_hoang_dao(day_info["day_chi_idx"])
        time_slots = [
            {
                "name": f"Giờ {g['chi_name']}",
                "range": f"{g['start']}-{g['end']}",
                "is_hoang_dao": True,
            }
            for g in gio_list
        ]

        # Verdict
        grade = score_result["grade"]
        if grade == "A":
            verdict = "Rất tốt"
            verdict_vi = "Ngày rất tốt — nên chọn."
        elif grade == "B":
            verdict = "Tốt"
            verdict_vi = "Ngày tốt — có thể chọn."
        elif grade == "C":
            verdict = "Chấp nhận được"
            verdict_vi = "Ngày bình thường — chấp nhận được nếu không có lựa chọn khác."
        else:
            verdict = "Không tốt"
            verdict_vi = "Ngày không tốt — nên tránh nếu có thể."

        if filter_result["severity"] == 2:
            verdict_vi += " (Có cảnh báo — xem chi tiết lớp lọc 2.)"

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "date": date_str,
                "lunar_date": _format_lunar_date(day_info),
                "can_chi_day": f"{day_info['day_can_name']} {day_info['day_chi_name']}",
                "nguhanh_day": day_info["day_nap_am_hanh"],
                "verdict": verdict,
                "verdict_vi": verdict_vi,
                "severity": filter_result["severity"],
                "score": score_result["score"],
                "grade": score_result["grade"],
                "layer1": layer1_detail,
                "layer2": layer2_detail,
                "layer3": layer3_detail,
                "time_slots": time_slots,
                "reason_vi": ". ".join(score_result["reasons_vi"]),
                "summary_vi": score_result["summary_vi"],
            },
        )

    except Exception:
        logger.exception("Internal error in chon_ngay_detail")
        return _error_response(
            500,
            "INTERNAL_ERROR",
            "Đã có lỗi xảy ra. Vui lòng thử lại sau.",
        )
