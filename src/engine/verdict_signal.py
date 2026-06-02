"""
verdict_signal.py — Deterministic verdict_signal + driver_tags (no prose).

Used by Vận trình năm luan-context (facts for LLM).
"""

from __future__ import annotations

from typing import Literal

VerdictSignal = Literal["thuan", "than_trong", "trung_tinh", "hao"]
MonthArchetype = Literal["nang_do", "gieo_hat", "thu_hoach", "phong_thu", "chuyen_dong"]
EmphasisSignal = Literal["up", "down", "neutral"]

SINH_MAP = {"Kim": "Thủy", "Mộc": "Hỏa", "Thủy": "Mộc", "Hỏa": "Thổ", "Thổ": "Kim"}
KHAC_MAP = {"Kim": "Mộc", "Mộc": "Thổ", "Thổ": "Thủy", "Thủy": "Hỏa", "Hỏa": "Kim"}


def element_relation_nhat_chu(flow_hanh: str, nhat_chu_hanh: str) -> str:
    """Lưu niên / lưu nguyệt hành vs Nhật chủ (same keys as luu_nien)."""
    if flow_hanh == nhat_chu_hanh:
        return "bình_hòa"
    if SINH_MAP.get(flow_hanh) == nhat_chu_hanh:
        return "sinh_menh"
    if SINH_MAP.get(nhat_chu_hanh) == flow_hanh:
        return "menh_sinh"
    if KHAC_MAP.get(flow_hanh) == nhat_chu_hanh:
        return "khắc_menh"
    if KHAC_MAP.get(nhat_chu_hanh) == flow_hanh:
        return "menh_khắc"
    return "trung_hòa"


def year_rating_to_relation_bucket(year_rating: str) -> str:
    return {
        "tốt": "sinh_menh",
        "hao": "menh_sinh",
        "trung_bình": "bình_hòa",
        "xấu": "khắc_menh",
    }.get(year_rating, "trung_hòa")


def verdict_signal_from_year(relation: str, year_rating: str) -> VerdictSignal:
    if relation == "sinh_menh" and year_rating == "tốt":
        return "thuan"
    if relation in ("khắc_menh",) or year_rating == "xấu":
        return "than_trong"
    if relation == "menh_sinh" or year_rating == "hao":
        return "hao"
    if relation in ("menh_khắc", "bình_hòa", "trung_hòa"):
        return "trung_tinh"
    return "trung_tinh"


def verdict_signal_from_life_rating(year_rating: str, *, year_hanh: str, dung_than: str, ky_than: str) -> VerdictSignal:
    if year_hanh == dung_than:
        return "thuan"
    if year_hanh == ky_than:
        return "than_trong"
    return verdict_signal_from_year(year_rating_to_relation_bucket(year_rating), year_rating)


def driver_tags_for_year(
    *,
    relation: str,
    year_rating: str,
    year_hanh: str,
    dung_than: str,
    ky_than: str,
    flow_xung_tuoi: bool,
    dominant_thap_than: str | None = None,
) -> list[str]:
    tags: list[str] = [
        f"year_relation:{relation}",
        f"year_rating:{year_rating}",
        f"year_hanh:{year_hanh}",
    ]
    if year_hanh == dung_than:
        tags.append("dung_than_match")
    if year_hanh == ky_than:
        tags.append("ky_than_match")
    if flow_xung_tuoi:
        tags.append("flow_year_xung_tuoi")
    if dominant_thap_than:
        tags.append(f"dominant_thap_than:{dominant_thap_than}")
    return tags


def month_archetype_from_month(
    *,
    relation: str,
    grade_a: int,
    grade_d: int,
    layer1_fail: int,
) -> MonthArchetype:
    if relation == "khắc_menh" or grade_d >= 8 or layer1_fail >= 10:
        return "phong_thu"
    if relation == "sinh_menh" and grade_a >= 6:
        return "nang_do"
    if relation == "sinh_menh":
        return "gieo_hat"
    if relation == "menh_sinh":
        return "chuyen_dong"
    if grade_a >= 8:
        return "thu_hoach"
    if relation in ("menh_khắc", "bình_hòa"):
        return "chuyen_dong"
    return "gieo_hat"


def dai_van_relation_signal(can_hanh: str, dung_than: str, ky_than: str) -> str:
    if can_hanh == dung_than:
        return "ho_tro_dung_than"
    if can_hanh == ky_than:
        return "ky_than"
    return "trung_tinh"
