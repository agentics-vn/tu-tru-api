"""
calendar_month_summary.py — Score all days in a solar month (shared by lich-thang & luan-context).
"""

from __future__ import annotations

import calendar
from datetime import date

from calendar_service import get_month_info, get_user_chart
from filter import apply_layer2_filter
from scoring import collect_score_deltas
from api.intent_rules_loader import get_intent_rule

_DEFAULT_INTENT = "MAC_DINH"

_WEEKDAY_VI = [
    "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm",
    "Thứ Sáu", "Thứ Bảy", "Chủ Nhật",
]


def _date_vi(iso: str) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    wd = _WEEKDAY_VI[date(y, m, d).weekday()]
    return f"{wd}, {d:02d}/{m:02d}/{y}"


def _mitigation_tags(l2: dict, day_info: dict) -> list[str]:
    tags: list[str] = []
    if l2.get("severity") == 3:
        tags.append("xung_tuoi")
    elif l2.get("severity") == 2:
        tags.append("khac_menh")
    if not day_info.get("is_layer1_pass"):
        tags.append("layer1_fail_high")
    for reason in l2.get("reasons") or []:
        r = reason.lower()
        if "tam" in r and "tai" in r:
            tags.append("tam_tai")
        if "phá" in r:
            tags.append("pha")
    if day_info.get("is_nguyet_ky"):
        tags.append("nguyet_ky")
    if day_info.get("is_tam_nuong"):
        tags.append("tam_nuong")
    return tags or ["chon_gio_tot", "tranh_quyet_dinh_lon"]


def score_calendar_month(
    year: int,
    month: int,
    *,
    birth_date_iso: str,
    birth_time: int | None,
    gender: int | None,
    intent: str = _DEFAULT_INTENT,
) -> dict:
    """Score every day in a solar month (shared by lich-thang & luan-context)."""
    user_chart = get_user_chart(birth_date_iso, birth_time, gender)
    intent_rule = get_intent_rule(intent)
    all_days = get_month_info(year, month, filter_passed=False)

    scored: list[dict] = []
    for d in all_days:
        l2 = apply_layer2_filter(d, user_chart, intent)
        ctx = collect_score_deltas(d, user_chart, intent, intent_rule, l2)
        scored.append({
            "date": d["date"],
            "date_vi": _date_vi(d["date"]),
            "can_chi": f"{d['day_can_name']} {d['day_chi_name']}",
            "day_chi_idx": d["day_chi_idx"],
            "score": ctx["score"],
            "grade": ctx["grade"],
            "is_layer1_pass": d["is_layer1_pass"],
            "l2": l2,
            "day_info": d,
        })

    return {
        "year": year,
        "month": month,
        "user_chart": user_chart,
        "intent_rule": intent_rule,
        "scored_days": scored,
    }


def summarize_calendar_month(
    year: int,
    month: int,
    *,
    birth_date_iso: str,
    birth_time: int | None,
    gender: int | None,
    intent: str = _DEFAULT_INTENT,
) -> dict:
    """Return solar_range, day rows with scores, best_days[<=3], avoid_days[<=3], stats."""
    base = score_calendar_month(
        year, month,
        birth_date_iso=birth_date_iso,
        birth_time=birth_time,
        gender=gender,
        intent=intent,
    )
    user_chart = base["user_chart"]
    scored = base["scored_days"]

    grade_a = grade_b = grade_c = grade_d = 0
    layer1_fail = 0
    for row in scored:
        grade = row["grade"]
        if grade == "A":
            grade_a += 1
        elif grade == "B":
            grade_b += 1
        elif grade == "C":
            grade_c += 1
        else:
            grade_d += 1
        if not row["is_layer1_pass"]:
            layer1_fail += 1

    good = sorted(
        [r for r in scored if r["is_layer1_pass"] and r["grade"] in ("A", "B")],
        key=lambda r: (-r["score"], r["date"]),
    )[:3]
    bad = sorted(
        [r for r in scored if not r["is_layer1_pass"] or r["grade"] == "D" or r["l2"].get("severity", 0) >= 2],
        key=lambda r: (r["score"], r["date"]),
    )[:3]

    last_dom = calendar.monthrange(year, month)[1]
    solar_range = f"{year}-{month:02d}-01 → {year}-{month:02d}-{last_dom:02d}"

    return {
        "year": year,
        "month": month,
        "solar_range": solar_range,
        "user_chart": user_chart,
        "intent_rule": base["intent_rule"],
        "scored_days": scored,
        "stats": {
            "grade_a": grade_a,
            "grade_b": grade_b,
            "grade_c": grade_c,
            "grade_d": grade_d,
            "layer1_fail": layer1_fail,
            "total_days": len(scored),
        },
        "best_days": [
            {
                "date": r["date"],
                "date_vi": r["date_vi"],
                "can_chi": r["can_chi"],
                "grade": r["grade"],
                "score": r["score"],
            }
            for r in good
        ],
        "avoid_days": [
            {
                "date": r["date"],
                "date_vi": r["date_vi"],
                "can_chi": r["can_chi"],
                "grade": r["grade"],
                "score": r["score"],
                "mitigation_tags": _mitigation_tags(r["l2"], r["day_info"]),
            }
            for r in bad
        ],
    }
