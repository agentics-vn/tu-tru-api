"""
month_emphasis.py — b2_month_emphasis (≤2 aspects, emphasis_signal vs năm).
"""

from __future__ import annotations

from engine.verdict_signal import EmphasisSignal, element_relation_nhat_chu
from engine.luu_nguyet import get_luu_nguyet_pillar
from engine.can_chi import CAN_HANH

_ASPECT_ORDER = ("su_nghiep", "tai_loc", "tinh_cam", "suc_khoe")
_ASPECT_LABELS = {
    "su_nghiep": "Sự nghiệp",
    "tai_loc": "Tài chính",
    "tinh_cam": "Tình cảm",
    "suc_khoe": "Sức khỏe",
}

_REL_RANK = {
    "sinh_menh": 0,
    "bình_hòa": 1,
    "trung_hòa": 1,
    "menh_khắc": 2,
    "menh_sinh": 3,
    "khắc_menh": 4,
}


def _emphasis_vs_year(month_rel: str, year_rel: str) -> EmphasisSignal:
    m = _REL_RANK.get(month_rel, 2)
    y = _REL_RANK.get(year_rel, 2)
    if m < y:
        return "up"
    if m > y:
        return "down"
    return "neutral"


def _month_vs_year_delta(
    aspect_id: str,
    month_hanh: str,
    *,
    nhat_chu_hanh: str,
    year_rel: str,
    dung_than: str,
    ky_than: str,
    stats: dict,
) -> tuple[EmphasisSignal, list[str]]:
    month_rel = element_relation_nhat_chu(month_hanh, nhat_chu_hanh)
    tags: list[str] = [
        f"month_vs_nhat_chu:{month_rel}",
        f"year_vs_nhat_chu:{year_rel}",
    ]
    signal = _emphasis_vs_year(month_rel, year_rel)

    if aspect_id == "suc_khoe" and month_hanh == ky_than:
        signal = "up"
        tags.append("ky_than_match")
    elif aspect_id == "tai_loc" and month_hanh == dung_than:
        signal = "up"
        tags.append("dung_than_match")
    elif month_rel == "khắc_menh" and year_rel != "khắc_menh":
        signal = "down"
        tags.append("month_khac_nhat_chu")
    elif month_rel == "sinh_menh" and stats.get("grade_a", 0) >= 4:
        if signal == "neutral":
            signal = "up"
        tags.append("many_grade_a")

    if stats.get("grade_d", 0) >= 6:
        tags.append("many_grade_d")
        if signal == "neutral":
            signal = "down"

    return signal, tags


def build_month_emphasis(
    year: int,
    month: int,
    cal_summary: dict,
    part_a: dict,
    *,
    max_items: int = 2,
) -> list[dict]:
    pillar = get_luu_nguyet_pillar(year, month)
    month_hanh = CAN_HANH[pillar["can_idx"]]
    hook = part_a["hook_year"]
    year_rel = hook["element_relation"]
    nhat_chu_hanh = part_a["you_this_year"]["nhat_chu_hanh"]
    dung_than = part_a["you_this_year"]["dung_than"]
    ky_than = part_a["you_this_year"]["ky_than"]
    stats = cal_summary["stats"]

    year_aspects = {a["aspect_id"]: a for a in part_a["four_aspects_year"]}
    ranked: list[tuple[int, dict]] = []

    for aspect_id in _ASPECT_ORDER:
        ya = year_aspects[aspect_id]
        signal, shift_tags = _month_vs_year_delta(
            aspect_id,
            month_hanh,
            nhat_chu_hanh=nhat_chu_hanh,
            year_rel=year_rel,
            dung_than=dung_than,
            ky_than=ky_than,
            stats=stats,
        )
        month_rel = element_relation_nhat_chu(month_hanh, nhat_chu_hanh)
        if signal == "neutral" and month_rel == year_rel:
            continue
        priority = 2 if signal == "up" else 3 if signal == "down" else 1
        bullets: list[str] = []
        ab = stats["grade_a"] + stats["grade_b"]
        if ab > 0:
            bullets.append(f"{ab} ngày grade A/B trong tháng")
        if month_hanh == ky_than and aspect_id == "suc_khoe":
            bullets.append("Hành tháng trùng Kỵ Thần")
        ranked.append((priority, {
            "aspect_id": aspect_id,
            "label_vi": _ASPECT_LABELS[aspect_id],
            "emphasis_signal": signal,
            "shift_tags": shift_tags + [f"year_verdict:{ya['verdict_signal']}"],
            "fact_bullets_vi": bullets[:3],
        }))

    ranked.sort(key=lambda x: -x[0])
    return [item for _, item in ranked[:max_items]]
