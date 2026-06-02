"""
luu_nien_luan_a.py — part_a for Vận trình năm luan-context (facts + signals only).
"""

from __future__ import annotations

from typing import Any

from engine.can_chi import CAN_HANH, get_can_chi_year, is_xung
from engine.dai_van import get_current_dai_van, get_next_dai_van
from engine.dung_than import find_dung_than
from engine.pillars import get_tu_tru
from engine.thap_than import analyze_thap_than
from engine.verdict_signal import (
    VerdictSignal,
    dai_van_relation_signal,
    verdict_signal_from_life_rating,
    verdict_signal_from_year,
)
from engine.luu_nien import build_luu_nien


_ASPECT_MAP = (
    ("su_nghiep", "Sự nghiệp", "su_nghiep"),
    ("tai_loc", "Tài chính", "tai_loc"),
    ("tinh_cam", "Tình cảm", "tinh_duyen"),
    ("suc_khoe", "Sức khỏe", "suc_khoe"),
)

_THEME_SIGNAL = {
    "tốt": "thuan_nam",
    "hao": "hao_nam",
    "trung_bình": "on_dinh",
    "xấu": "than_trong_nam",
}

def _detect_dai_van_transition(
    tu_tru: dict,
    gender: int,
    birth_date_iso: str,
    year: int,
) -> dict | None:
    early = get_current_dai_van(
        tu_tru, gender, birth_date_iso, current_date=f"{year}-01-15"
    )
    late = get_current_dai_van(
        tu_tru, gender, birth_date_iso, current_date=f"{year}-12-15"
    )
    if early is None or late is None or early["display"] == late["display"]:
        return None

    nxt = get_next_dai_van(tu_tru, gender, birth_date_iso, current_date=f"{year}-01-15")
    to_display = (nxt or late)["display"]
    from_display = early["display"]

    transition_month = 1
    for m in range(1, 13):
        mid = get_current_dai_van(
            tu_tru, gender, birth_date_iso, current_date=f"{year}-{m:02d}-15"
        )
        if mid and mid["display"] != from_display:
            transition_month = m
            break

    return {
        "transition_month": transition_month,
        "from_display": from_display,
        "to_display": to_display,
        "applies_from_month": transition_month,
        "disclaimer_fact_vi": (
            f"Từ tháng {transition_month} năm {year} đại vận {to_display} "
            f"(trước đó {from_display})."
        ),
    }


def _pack_dai_van(cycle: dict | None, dung_than: str, ky_than: str) -> dict | None:
    if not cycle:
        return None
    return {
        "display": cycle["display"],
        "can_hanh": cycle["can_hanh"],
        "age_range": f"{cycle['start_age']}-{cycle['end_age']}",
        "relation_to_dung_than_signal": dai_van_relation_signal(
            cycle["can_hanh"], dung_than, ky_than
        ),
    }


def _aspect_verdict_signal(
    aspect_id: str,
    *,
    relation: str,
    rating: str,
    year_hanh: str,
    dung_than: str,
    ky_than: str,
    flow_xung_tuoi: bool,
) -> VerdictSignal:
    if aspect_id == "su_nghiep":
        return verdict_signal_from_year(relation, rating)
    if aspect_id == "tinh_cam" and flow_xung_tuoi:
        return "than_trong"
    if aspect_id == "suc_khoe" and year_hanh == ky_than:
        return "than_trong"
    if aspect_id in ("tai_loc", "suc_khoe") and year_hanh == dung_than:
        return "thuan"
    return verdict_signal_from_life_rating(
        rating,
        year_hanh=year_hanh,
        dung_than=dung_than,
        ky_than=ky_than,
    )


def _aspect_driver_tags(
    aspect_id: str,
    *,
    relation: str,
    year_rating: str,
    year_hanh: str,
    dung_than: str,
    ky_than: str,
    flow_xung_tuoi: bool,
    dominant_thap_than: str,
) -> list[str]:
    tags = [f"aspect:{aspect_id}", f"year_relation:{relation}", f"year_rating:{year_rating}"]
    if aspect_id == "su_nghiep":
        tags.append(f"dominant_thap_than:{dominant_thap_than}")
    if aspect_id in ("tai_loc", "suc_khoe"):
        if year_hanh == dung_than:
            tags.append("dung_than_match")
        if year_hanh == ky_than:
            tags.append("ky_than_match")
    if aspect_id == "tinh_cam" and flow_xung_tuoi:
        tags.append("flow_year_xung_tuoi")
    return tags


def _aspect_fact_bullets(
    aspect_id: str,
    *,
    year: int,
    year_can_chi: str,
    year_hanh: str,
    relation: str,
    rating: str,
    dung_than: str,
    ky_than: str,
    flow_xung_tuoi: bool,
    dominant_thap_than: str,
) -> list[str]:
    bullets = [
        f"Lưu niên {year}: {year_can_chi}, hành {year_hanh}",
        f"Quan hệ năm–Nhật chủ: {relation.replace('_', ' ')}",
        f"year_rating:{rating}",
    ]
    if aspect_id == "su_nghiep":
        bullets.append(f"dominant_thap_than:{dominant_thap_than}")
    if aspect_id == "tai_loc":
        if year_hanh == dung_than:
            bullets.append("year_hanh trùng Dụng Thần")
        elif year_hanh == ky_than:
            bullets.append("year_hanh trùng Kỵ Thần")
    if aspect_id == "tinh_cam" and flow_xung_tuoi:
        bullets.append("năm xung tuổi")
    if aspect_id == "suc_khoe":
        if year_hanh == ky_than:
            bullets.append("year_hanh trùng Kỵ Thần")
        elif year_hanh == dung_than:
            bullets.append("year_hanh trùng Dụng Thần")
    return bullets


def build_part_a(
    *,
    birth_date_iso: str,
    birth_time: int,
    gender: int,
    year: int,
    luu_raw: dict[str, Any] | None = None,
) -> dict:
    if luu_raw is None:
        luu_raw = build_luu_nien(
            birth_date_iso=birth_date_iso,
            birth_time=birth_time,
            gender=gender,
            year=year,
        )
    tu_tru = get_tu_tru(birth_date_iso, birth_time)
    dung = find_dung_than(tu_tru)
    thap_than = analyze_thap_than(tu_tru)
    dominant = thap_than["dominant_god"]["name"]
    dm_hanh = tu_tru["nhat_chu"]["hanh"]
    ycc = get_can_chi_year(year)
    year_hanh = CAN_HANH[ycc["can_idx"]]
    relation = luu_raw["element_relation"]
    rating = luu_raw["year_rating"]
    flow_xung = is_xung(tu_tru["year"]["chi_idx"], ycc["chi_idx"])

    hook_bullets = [
        f"Năm {year} — {luu_raw['year_can_chi']}, hành {year_hanh}",
        f"Quan hệ với Nhật chủ ({dm_hanh}): {relation.replace('_', ' ')}",
        f"Đánh giá năm: {rating}",
    ]
    if year_hanh == dung["dung_than"]:
        hook_bullets.append("Hành năm trùng Dụng Thần")
    if year_hanh == dung["ky_than"]:
        hook_bullets.append("Hành năm trùng Kỵ Thần")

    four: list[dict] = []
    for aspect_id, label_vi, _life_id in _ASPECT_MAP:
        vs = _aspect_verdict_signal(
            aspect_id,
            relation=relation,
            rating=rating,
            year_hanh=year_hanh,
            dung_than=dung["dung_than"],
            ky_than=dung["ky_than"],
            flow_xung_tuoi=flow_xung,
        )
        tags = _aspect_driver_tags(
            aspect_id,
            relation=relation,
            year_rating=rating,
            year_hanh=year_hanh,
            dung_than=dung["dung_than"],
            ky_than=dung["ky_than"],
            flow_xung_tuoi=flow_xung,
            dominant_thap_than=dominant,
        )
        bullets = _aspect_fact_bullets(
            aspect_id,
            year=year,
            year_can_chi=luu_raw["year_can_chi"],
            year_hanh=year_hanh,
            relation=relation,
            rating=rating,
            dung_than=dung["dung_than"],
            ky_than=dung["ky_than"],
            flow_xung_tuoi=flow_xung,
            dominant_thap_than=dominant,
        )
        four.append({
            "aspect_id": aspect_id,
            "label_vi": label_vi,
            "verdict_signal": vs,
            "driver_tags": tags,
            "fact_bullets_vi": bullets,
            "timing_tags": [],
        })

    cur_dv = get_current_dai_van(
        tu_tru, gender, birth_date_iso, current_date=f"{year}-06-15"
    )
    transition = _detect_dai_van_transition(tu_tru, gender, birth_date_iso, year)
    dai_van_block: dict = {
        "current": _pack_dai_van(cur_dv, dung["dung_than"], dung["ky_than"]),
        "transition_in_year": transition,
    }
    if transition:
        dai_van_block["disclaimer_fact_vi"] = transition["disclaimer_fact_vi"]

    day = tu_tru["day"]
    natal_facts = [
        f"Nhật chủ: {tu_tru['nhat_chu']['can_name']} ({dm_hanh}), ngày {day['can_name']} {day['chi_name']}",
        f"Dụng Thần: {dung['dung_than']}, Kỵ Thần: {dung['ky_than']}",
    ]

    return {
        "hook_year": {
            "year": year,
            "year_can_chi": luu_raw["year_can_chi"],
            "year_hanh": year_hanh,
            "element_relation": relation,
            "year_rating": rating,
            "year_theme_signal": _THEME_SIGNAL.get(rating, "on_dinh"),
            "fact_bullets_vi": hook_bullets,
        },
        "you_this_year": {
            "natal_facts_vi": natal_facts,
            "nhat_chu_hanh": dm_hanh,
            "dung_than": dung["dung_than"],
            "ky_than": dung["ky_than"],
            "dai_van": dai_van_block,
        },
        "four_aspects_year": four,
        "year_aspect_ranking": [a["aspect_id"] for a in sorted(
            four, key=lambda x: {"thuan": 0, "hao": 1, "trung_tinh": 2, "than_trong": 3}[x["verdict_signal"]]
        )],
    }
