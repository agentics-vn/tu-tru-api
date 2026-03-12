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

# ── Engine imports (Python ports of the JS engine modules) ─────────────────
from calendar_service import get_day_info, get_user_chart, get_can_chi_year, CAN_NAMES, CHI_NAMES
from filter import apply_layer2_filter
from scoring import compute_score
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
    KHAI_TRUONG = "KHAI_TRUONG"
    CUOI_HOI = "CUOI_HOI"
    DONG_THO = "DONG_THO"
    XUAT_HANH = "XUAT_HANH"
    KY_HOP_DONG = "KY_HOP_DONG"
    MAC_DINH = "MAC_DINH"


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ChonNgayRequest(BaseModel):
    birth_date: date
    birth_time: Optional[int] = Field(
        default=None,
        description="Birth hour from dropdown: 0,2,4,6,8,10,11,14,16,18,20,22,23",
    )
    gender: Optional[GenderEnum] = Field(
        default=None,
        description="Gender: male or female (required for Đại Vận)",
    )
    intent: IntentEnum
    range_start: date
    range_end: date
    top_n: Optional[int] = Field(default=TOP_N_DEFAULT, ge=1, le=TOP_N_MAX)

    @field_validator("birth_date")
    @classmethod
    def birth_date_must_be_past(cls, v: date) -> date:
        if v.year < 1900:
            raise ValueError("birth_date year must be >= 1900")
        if v >= date.today():
            raise ValueError("birth_date must be a past date")
        return v

    @field_validator("birth_time")
    @classmethod
    def birth_time_valid_values(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if v not in VALID_BIRTH_HOURS:
            raise ValueError(
                f"birth_time must be one of {sorted(VALID_BIRTH_HOURS)}, got {v}"
            )
        return v

    @model_validator(mode="after")
    def validate_range(self) -> "ChonNgayRequest":
        if self.range_end < self.range_start:
            raise ValueError("range_end must be on or after range_start")
        diff = (self.range_end - self.range_start).days
        if diff > MAX_RANGE_DAYS:
            raise ValueError(
                f"range_end must be within {MAX_RANGE_DAYS} days of range_start"
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
        if user_chart.get("hi_than"):
            summary["hi_than"] = user_chart["hi_than"]
        if user_chart.get("chart_strength"):
            summary["chart_strength"] = user_chart["chart_strength"]

    if user_chart.get("current_dai_van"):
        dv = user_chart["current_dai_van"]
        summary["current_dai_van"] = {
            "display": dv["display"],
            "hanh": dv["can_hanh"],
            "age_range": f"{dv['start_age']}-{dv['end_age']}",
        }

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
        birth_date_str = req.birth_date.isoformat()

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
        all_dates = _each_day_in_range(req.range_start, req.range_end)
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
                dates_to_avoid.append({
                    "date": date_str,
                    "reason_vi": ". ".join(filter_result["reasons"]) + ". Tuyệt đối tránh.",
                    "severity": filter_result["severity"],
                })
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
                        "from": req.range_start.isoformat(),
                        "to": req.range_end.isoformat(),
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

    except HTTPException:
        raise
    except Exception:
        logger.exception("Internal error in chon_ngay")
        return _error_response(
            500,
            "INTERNAL_ERROR",
            "Đã có lỗi xảy ra. Vui lòng thử lại sau.",
        )
