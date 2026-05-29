"""
Shared HTTP payload builder for Direction C day-score endpoints.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from api.gio_slots import format_gio_tot_slots, format_gio_xau_slots
from api.intent_rules_loader import INTENT_RULES, get_intent_rule
from engine.day_score import build_direction_c_breakdown
from engine.hoang_dao import get_day_star, get_gio_hoang_dao
from engine.nhi_thap_bat_tu import get_nhi_thap_bat_tu
from engine.score_methodology import DIRECTION_C_SOURCES, get_score_methodology_block
from filter import apply_layer2_filter
from scoring import collect_score_deltas


def build_purpose_rows(day_info: dict, user_chart: dict) -> list[dict[str, Any]]:
    """Per-intent suitability rows for day-detail (P3-03)."""
    rows: list[dict[str, Any]] = []
    truc_idx = day_info["truc_idx"]

    for intent_key in sorted(k for k in INTENT_RULES if not k.startswith("_")):
        rule = INTENT_RULES[intent_key]
        label = rule.get("_label_vi", intent_key)
        short = label.split("/")[0].strip()
        l2 = apply_layer2_filter(day_info, user_chart, intent_key)
        preferred = rule.get("preferred_truc", [])
        forbidden = rule.get("forbidden_truc", [])

        if l2["severity"] == 3:
            verdict = "xau"
            reason = (
                ". ".join(l2["reasons"]) + ". Tuyệt đối tránh."
                if l2["reasons"]
                else "Xung khắc trực tiếp với tuổi — tuyệt đối tránh."
            )
        elif truc_idx in forbidden:
            verdict = "xau"
            reason = f"Trực {day_info['truc_name']} không phù hợp cho {short.lower()}."
        elif truc_idx in preferred and l2["pass"]:
            verdict = "tot"
            reason = f"Trực {day_info['truc_name']} thuận cho {short.lower()}."
        elif l2["severity"] == 2:
            verdict = "luu_y"
            reason = (
                ". ".join(l2["reasons"])
                if l2["reasons"]
                else "Có yếu tố cần lưu ý với lá số của bạn."
            )
        else:
            verdict = "trung"
            reason = f"Ngày trung bình cho {short.lower()}."

        rows.append({
            "intent": intent_key,
            "intent_label_vi": label,
            "short_label_vi": short,
            "verdict": verdict,
            "reason_vi": reason,
        })
    return rows


def good_and_avoid_from_purpose_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    """Derive good_for / avoid_for lists from purpose_rows (single source of truth)."""
    good_for: list[str] = []
    avoid_for: list[str] = []
    for row in rows:
        if row.get("intent") == "MAC_DINH":
            continue
        short = row["short_label_vi"]
        verdict = row["verdict"]
        if verdict == "tot":
            good_for.append(short)
        elif verdict == "xau":
            avoid_for.append(short)
    return good_for, avoid_for


def build_good_and_avoid(day_info: dict, user_chart: dict) -> tuple[list[str], list[str]]:
    return good_and_avoid_from_purpose_rows(build_purpose_rows(day_info, user_chart))


def score_day_context(
    *,
    day_info: dict,
    user_chart: dict,
    intent: str,
    intent_rule: dict,
    target: date,
    personalized: bool = True,
) -> dict[str, Any]:
    """Run scoring + breakdown for one day."""
    filter_result = (
        {"pass": True, "severity": 0, "reasons": []}
        if not personalized
        else apply_layer2_filter(day_info, user_chart, intent)
    )
    ctx = collect_score_deltas(day_info, user_chart, intent, intent_rule, filter_result)

    star_info = get_day_star(day_info["lunar_month"], day_info["day_chi_idx"])
    sao_28 = get_nhi_thap_bat_tu(target.year, target.month, target.day)
    gio_raw = get_gio_hoang_dao(day_info["day_chi_idx"])

    breakdown = build_direction_c_breakdown(
        day_info=day_info,
        user_chart=user_chart,
        intent=intent,
        presentation_buckets=ctx["presentation_buckets"],
        star_info=star_info,
        sao_28=sao_28,
        gio_tot=gio_raw,
        personalized=personalized,
    )

    return {
        "score": ctx["score"],
        "grade": ctx["grade"],
        "summary_vi": ctx["summary_vi"],
        "reasons_vi": ctx["reasons_vi"],
        "bonus_sao": ctx["bonus_sao"],
        "penalty_sao": ctx["penalty_sao"],
        "breakdown": breakdown,
        "sources": list(DIRECTION_C_SOURCES),
        "filter_result": filter_result,
        "star_info": star_info,
        "sao_28": sao_28,
        "gio_tot_raw": gio_raw,
        "gio_tot": format_gio_tot_slots(day_info["day_chi_idx"]),
    }


def build_personalized_day_payload(
    *,
    day_info: dict,
    user_chart: dict,
    intent: str,
    intent_rule: dict,
    target: date,
    include_layers: bool = False,
) -> dict[str, Any]:
    """Unified top-level fields for day-detail and chon-ngay/detail."""
    scored = score_day_context(
        day_info=day_info,
        user_chart=user_chart,
        intent=intent,
        intent_rule=intent_rule,
        target=target,
        personalized=True,
    )
    methodology = get_score_methodology_block()

    payload: dict[str, Any] = {
        "score": scored["score"],
        "grade": scored["grade"],
        "summary_vi": scored["summary_vi"],
        "breakdown": scored["breakdown"],
        "sources": scored["sources"],
        **methodology,
        "personalized": True,
    }
    if include_layers:
        payload["bonus_sao"] = scored["bonus_sao"]
        payload["penalty_sao"] = scored["penalty_sao"]
    return payload


def build_generic_day_payload(
    *,
    day_info: dict,
    user_chart: dict,
    target: date,
) -> dict[str, Any]:
    """Generic mode — calendar scoring without birth personalization."""
    intent = "MAC_DINH"
    intent_rule = get_intent_rule(intent)
    empty_chart = {
        "menh_name": "",
        "menh_hanh": "",
        "duong_than": None,
        "ky_than": None,
    }
    scored = score_day_context(
        day_info=day_info,
        user_chart=empty_chart,
        intent=intent,
        intent_rule=intent_rule,
        target=target,
        personalized=False,
    )
    methodology = get_score_methodology_block()
    return {
        "score": scored["score"],
        "grade": scored["grade"],
        "breakdown_generic": scored["breakdown"],
        "sources": scored["sources"],
        **methodology,
        "personalized": False,
    }


def build_luan_context_payload(
    *,
    day_info: dict,
    user_chart: dict,
    intent: str,
    intent_rule: dict,
    target: date,
) -> dict[str, Any]:
    scored = score_day_context(
        day_info=day_info,
        user_chart=user_chart,
        intent=intent,
        intent_rule=intent_rule,
        target=target,
        personalized=True,
    )
    gio_tot_slots = format_gio_tot_slots(day_info["day_chi_idx"])
    gio_xau_slots = format_gio_xau_slots(day_info["day_chi_idx"])
    can_chi_day = f"{day_info['day_can_name']} {day_info['day_chi_name']}"

    breakdown_summary = []
    for item in scored["breakdown"]:
        breakdown_summary.append({
            "id": item["id"],
            "label_vi": item["source"],
            "verdict_vi": item["type"],
            "reason_vi": item["reason_vi"],
            "points": item["points"],
            "source_ref": item["source_ref"],
        })

    menh_user = user_chart.get("menh_name") or user_chart.get("menh_hanh", "")

    gio_tot_labels = [s["label_vi"] for s in gio_tot_slots]
    gio_xau_labels = [s["label_vi"] for s in gio_xau_slots]

    return {
        "date_iso": target.isoformat(),
        "can_chi_day": can_chi_day,
        "score": scored["score"],
        "grade": scored["grade"],
        "menh_user": menh_user,
        "breakdown_summary": breakdown_summary,
        "sources": scored["sources"],
        "gio_tot": gio_tot_slots,
        "gio_xau": gio_xau_slots,
        "gio_tot_labels": gio_tot_labels,
        "gio_xau_labels": gio_xau_labels,
        "scope_hint_vi": (
            "Chỉ luận giải dựa trên dữ kiện ngày và lá số đã cung cấp; "
            "không dự đoán tương lai tuyệt đối."
        ),
        "anchor_question_hint_vi": (
            f"Giải thích vì sao ngày {can_chi_day} đạt điểm {scored['score']} "
            f"và từng yếu tố Trực, sao, Can Chi, giờ vàng."
        ),
        "suggested_followups": [
            "Nên làm gì vào giờ vàng?",
            "So sánh với ngày khác trong tuần?",
        ],
    }
