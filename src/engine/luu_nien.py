"""
engine/luu_nien.py — Annual luck (Lưu niên) MVP for Direction C P2-02.

Not Phi Tinh (phong-thuy) or monthly tieu-van.
Phase 2b (quy_nhan, tuoi_hop, tuoi_xung) deferred — NLTT màn 18 §05 blocked until then.
"""

from __future__ import annotations

from typing import Any, Optional

from engine.can_chi import CAN_HANH, CAN_NAMES, CHI_NAMES, get_can_chi_year
from engine.cuong_nhuoc import analyze_chart_strength
from engine.dung_than import find_dung_than
from engine.pillars import get_tu_tru

SINH_MAP = {"Kim": "Thủy", "Thủy": "Mộc", "Mộc": "Hỏa", "Hỏa": "Thổ", "Thổ": "Kim"}
KHAC_MAP = {"Kim": "Mộc", "Mộc": "Thổ", "Thổ": "Thủy", "Thủy": "Hỏa", "Hỏa": "Kim"}


def _element_relation(year_hanh: str, user_hanh: str) -> str:
    if year_hanh == user_hanh:
        return "bình_hòa"
    if SINH_MAP.get(year_hanh) == user_hanh:
        return "sinh_menh"
    if SINH_MAP.get(user_hanh) == year_hanh:
        return "menh_sinh"
    if KHAC_MAP.get(year_hanh) == user_hanh:
        return "khắc_menh"
    if KHAC_MAP.get(user_hanh) == year_hanh:
        return "menh_khắc"
    return "trung_hòa"


def _year_rating(relation: str) -> str:
    return {
        "sinh_menh": "tốt",
        "menh_sinh": "hao",
        "bình_hòa": "trung_bình",
        "menh_khắc": "trung_bình",
        "khắc_menh": "xấu",
        "trung_hòa": "trung_bình",
    }.get(relation, "trung_bình")


def build_luu_nien(
    *,
    birth_date_iso: str,
    birth_time: int,
    gender: int,
    year: int,
) -> dict[str, Any]:
    tu_tru = get_tu_tru(birth_date_iso, birth_time)
    dung = find_dung_than(tu_tru)
    strength = analyze_chart_strength(tu_tru)
    dm_hanh = tu_tru["nhat_chu"]["hanh"]

    year_cc = get_can_chi_year(year)
    year_can_chi = f"{year_cc['can_name']} {year_cc['chi_name']}"
    year_can_idx = year_cc["can_idx"]
    year_hanh = CAN_HANH[year_can_idx]

    relation = _element_relation(year_hanh, dm_hanh)
    rating = _year_rating(relation)
    dung_than = dung["dung_than"]

    theme_parts = [
        f"Năm {year} ({year_can_chi}) hành {year_hanh}",
        f"quan hệ với Nhật Chủ hành {dm_hanh}: {relation.replace('_', ' ')}",
    ]
    if year_hanh == dung_than:
        theme_parts.append("Trùng Dụng Thần — thuận cho bổ trợ sức khỏe và việc quan trọng.")
    elif year_hanh == dung["ky_than"]:
        theme_parts.append("Trùng Kỵ Thần — nên thận trọng, chọn thời điểm tốt.")

    life_areas = []
    if rating in ("tốt", "trung_bình"):
        life_areas.append({"area": "sự_nghiệp", "outlook_vi": "Có cơ hội nếu chủ động và chọn ngày tốt"})
    if year_hanh == dung_than:
        life_areas.append({"area": "sức_khoe", "outlook_vi": "Năng lượng Dụng Thần hỗ trợ — duy trì thói quen tốt"})
    else:
        life_areas.append({"area": "sức_khoe", "outlook_vi": "Theo dõi cân bằng ngũ hành cá nhân"})

    warnings: list[str] = []
    if relation == "khắc_menh":
        warnings.append("Năm khắc mệnh — tránh quyết định lớn vào ngày xấu.")
    if strength["strength"] == "nhược" and relation == "menh_sinh":
        warnings.append("Thân nhược gặp năm hao — cần bổ trợ, tránh làm quá sức.")

    # Best-effort monthly scores (simplified: same year relation + month can offset)
    month_scores = []
    for m in range(1, 13):
        base = 55 if rating == "tốt" else 45 if rating == "xấu" else 50
        month_scores.append({"month": m, "score": min(100, max(0, base + (m % 3) * 3 - 3))})

    return {
        "year": year,
        "year_can_chi": year_can_chi,
        "year_label_vi": f"Lưu niên {year} — {year_can_chi}",
        "element_relation": relation,
        "year_rating": rating,
        "year_theme_vi": " ".join(theme_parts),
        "life_areas": life_areas,
        "warnings": warnings,
        "month_scores": month_scores,
        "assumptions_vi": [
            "MVP: điểm tháng là ước lượng theo quan hệ năm–Nhật Chủ, chưa tính xung hợp chi tiết.",
            "Phase 2b: quy_nhan, tuoi_hop, tuoi_xung chưa có — màn NLTT §05 Quý nhân vẫn blocked.",
        ],
    }
