"""
engine/luu_nien.py — Annual luck (Lưu niên) for Direction C P2-02 / bazi reading §03 & §05.

Deterministic facts for NLTT màn 18 (no LLM). Phi Tinh lives in phong-thuy.
"""

from __future__ import annotations

from typing import Any, Optional

from engine.can_chi import CAN_HANH, CHI_NAMES, get_can_chi_year, is_xung
from engine.cuong_nhuoc import analyze_chart_strength
from engine.dai_van import get_next_dai_van
from engine.dung_than import find_dung_than
from engine.huong_by_hanh import primary_huong_for_dung_than
from engine.pillars import get_tu_tru
from engine.sao_ngay import LUC_HOP_MAP, TAM_HOP_SETS
from engine.thap_than import analyze_thap_than

SINH_MAP = {"Kim": "Thủy", "Mộc": "Hỏa", "Thủy": "Mộc", "Hỏa": "Thổ", "Thổ": "Kim"}
KHAC_MAP = {"Kim": "Mộc", "Mộc": "Thổ", "Thổ": "Thủy", "Thủy": "Hỏa", "Hỏa": "Kim"}

LIFE_AREA_DEFS: tuple[dict[str, str], ...] = (
    {"id": "tai_loc", "label_vi": "Tài lộc"},
    {"id": "su_nghiep", "label_vi": "Sự nghiệp"},
    {"id": "suc_khoe", "label_vi": "Sức khỏe"},
    {"id": "tinh_duyen", "label_vi": "Tình duyên"},
)

VERDICT_BY_RATING: dict[str, str] = {
    "tốt": "Thuận",
    "hao": "Hao tài",
    "trung_bình": "Ổn định",
    "xấu": "Cần thận trọng",
}


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


def _compatible_chi_names(chi_idx: int) -> list[str]:
    """Tam Hợp partners + Lục Hợp partner for a birth-year branch."""
    seen: set[int] = set()
    names: list[str] = []

    def add(idx: int) -> None:
        if idx not in seen:
            seen.add(idx)
            names.append(CHI_NAMES[idx])

    tam = TAM_HOP_SETS.get(chi_idx)
    if tam:
        for idx in sorted(tam):
            add(idx)
    luc = LUC_HOP_MAP.get(chi_idx)
    if luc is not None:
        add(luc)
    return names


def _clashing_chi_names(chi_idx: int, extra_chi_idx: Optional[int] = None) -> list[str]:
    names: list[str] = []
    xung = (chi_idx + 6) % 12
    names.append(CHI_NAMES[xung])
    if extra_chi_idx is not None and extra_chi_idx != xung and is_xung(chi_idx, extra_chi_idx):
        if CHI_NAMES[extra_chi_idx] not in names:
            names.append(CHI_NAMES[extra_chi_idx])
    return names


def build_quy_nhan(
    *,
    user_year_chi_idx: int,
    flow_year_chi_idx: int,
    dung_than: str,
    year_can_chi: str,
) -> dict[str, Any]:
    tuoi_hop = _compatible_chi_names(user_year_chi_idx)
    tuoi_xung = _clashing_chi_names(user_year_chi_idx, flow_year_chi_idx)
    huong = primary_huong_for_dung_than(dung_than)

    notes: list[str] = []
    if is_xung(user_year_chi_idx, flow_year_chi_idx):
        notes.append(
            f"Năm lưu niên {year_can_chi} xung tuổi — ưu tiên người tuổi hợp ({', '.join(tuoi_hop[:3]) or '—'})."
        )
    else:
        notes.append(
            f"Quý nhân theo tuổi hợp: {', '.join(tuoi_hop) or '—'}; hướng {huong} hỗ trợ Dụng Thần {dung_than}."
        )

    return {
        "tuoi_hop": tuoi_hop,
        "tuoi_xung": tuoi_xung,
        "huong_quy_nhan": huong,
        "note_vi": " ".join(notes),
    }


def _life_area_detail(
    area_id: str,
    *,
    rating: str,
    relation: str,
    year_hanh: str,
    dung_than: str,
    ky_than: str,
    dominant_thap_than: str,
    flow_xung_tuoi: bool,
) -> tuple[str, str]:
    verdict = VERDICT_BY_RATING.get(rating, "Ổn định")

    if area_id == "tai_loc":
        if rating in ("tốt", "hao"):
            detail = "Năm thuận để tích lũy và mở rộng nguồn thu nếu chọn thời điểm tốt."
        elif rating == "xấu":
            detail = "Tránh đầu cơ lớn; giữ dòng tiền an toàn."
        else:
            detail = "Tài lộc ổn định — cần chủ động và kỷ luật chi tiêu."
        if year_hanh == dung_than:
            verdict = "Thuận"
            detail = "Hành năm trùng Dụng Thần — thuận cho tích lũy và đầu tư có kế hoạch."
        return verdict, detail

    if area_id == "su_nghiep":
        detail = (
            f"Thập Thần chủ đạo {dominant_thap_than} — "
            + (
                "có cửa thăng tiến nếu chủ động."
                if rating in ("tốt", "hao")
                else "nên ổn định trước khi mở rộng."
            )
        )
        return verdict, detail

    if area_id == "suc_khoe":
        if year_hanh == ky_than:
            verdict = "Cần thận trọng"
            detail = f"Năm trùng Kỵ Thần ({ky_than}) — chú ý cân bằng sức khỏe và nghỉ ngơi."
        elif year_hanh == dung_than:
            verdict = "Thuận"
            detail = "Năng lượng Dụng Thần hỗ trợ — duy trì thói quen tốt."
        else:
            detail = "Theo dõi cân bằng ngũ hành cá nhân quanh các tháng điểm thấp."
        return verdict, detail

    # tinh_duyen
    if flow_xung_tuoi:
        verdict = "Cần thận trọng"
        detail = "Năm xung tuổi — tránh quyết định hôn nhân/tình cảm vội vàng."
    elif relation in ("sinh_menh", "bình_hòa"):
        detail = "Quan hệ có thể ấm áp hơn nếu chọn ngày hòa hợp."
    else:
        detail = "Nên lắng nghe và tránh xung đột nhỏ leo thang."
    return verdict, detail


def _build_life_areas(
    *,
    rating: str,
    relation: str,
    year_hanh: str,
    dung_than: str,
    ky_than: str,
    dominant_thap_than: str,
    flow_xung_tuoi: bool,
) -> list[dict[str, str]]:
    areas: list[dict[str, str]] = []
    for spec in LIFE_AREA_DEFS:
        verdict, detail = _life_area_detail(
            spec["id"],
            rating=rating,
            relation=relation,
            year_hanh=year_hanh,
            dung_than=dung_than,
            ky_than=ky_than,
            dominant_thap_than=dominant_thap_than,
            flow_xung_tuoi=flow_xung_tuoi,
        )
        areas.append({
            "id": spec["id"],
            "label_vi": spec["label_vi"],
            "verdict_vi": verdict,
            "detail_vi": detail,
            # Legacy aliases for older mappers
            "area": spec["id"],
            "outlook_vi": detail,
        })
    return areas


def _build_month_scores(rating: str, flow_year_chi_idx: int) -> list[dict[str, int]]:
    base = 55 if rating == "tốt" else 45 if rating == "xấu" else 50
    scores: list[dict[str, int]] = []
    for lunar_month in range(1, 13):
        # Lunar month offset vs flow-year branch (best-effort MVP)
        offset = (lunar_month + flow_year_chi_idx) % 5
        score = min(100, max(0, base + offset * 2 - 4))
        scores.append({"month": lunar_month, "score": score})
    return scores


def _build_dai_van_next(
    tu_tru: dict,
    gender: int,
    birth_date_iso: str,
) -> Optional[dict[str, str]]:
    nxt = get_next_dai_van(tu_tru, gender, birth_date_iso)
    if not nxt:
        return None

    birth_year = int(birth_date_iso.split("-")[0])
    start_year = birth_year + nxt["start_age"]
    theme = (
        f"Đại vận {nxt['display']} (hành {nxt['can_hanh']}) — "
        f"tuổi {nxt['start_age']}-{nxt['end_age']}, khoảng từ năm {start_year}."
    )
    return {
        "display": nxt["display"],
        "theme_vi": theme,
        "start_year": str(start_year),
        "age_range": f"{nxt['start_age']}-{nxt['end_age']}",
    }


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
    thap_than = analyze_thap_than(tu_tru)
    dm_hanh = tu_tru["nhat_chu"]["hanh"]
    user_year_chi_idx = tu_tru["year"]["chi_idx"]

    year_cc = get_can_chi_year(year)
    year_can_chi = f"{year_cc['can_name']} {year_cc['chi_name']}"
    year_chi_idx = year_cc["chi_idx"]
    year_hanh = CAN_HANH[year_cc["can_idx"]]

    relation = _element_relation(year_hanh, dm_hanh)
    rating = _year_rating(relation)
    dung_than = dung["dung_than"]
    ky_than = dung["ky_than"]
    flow_xung_tuoi = is_xung(user_year_chi_idx, year_chi_idx)

    theme_parts = [
        f"Năm {year} ({year_can_chi}) hành {year_hanh}",
        f"quan hệ với Nhật Chủ hành {dm_hanh}: {relation.replace('_', ' ')}",
    ]
    if year_hanh == dung_than:
        theme_parts.append("Trùng Dụng Thần — thuận cho bổ trợ sức khỏe và việc quan trọng.")
    elif year_hanh == ky_than:
        theme_parts.append("Trùng Kỵ Thần — nên thận trọng, chọn thời điểm tốt.")

    warnings: list[str] = []
    if relation == "khắc_menh":
        warnings.append("Năm khắc mệnh — tránh quyết định lớn vào ngày xấu.")
    if strength["strength"] == "nhược" and relation == "menh_sinh":
        warnings.append("Thân nhược gặp năm hao — cần bổ trợ, tránh làm quá sức.")
    if flow_xung_tuoi:
        warnings.append(f"Năm {year_can_chi} xung tuổi — cần thận trọng Tam Tai / quyết sách lớn.")

    life_areas = _build_life_areas(
        rating=rating,
        relation=relation,
        year_hanh=year_hanh,
        dung_than=dung_than,
        ky_than=ky_than,
        dominant_thap_than=thap_than["dominant_god"]["name"],
        flow_xung_tuoi=flow_xung_tuoi,
    )
    month_scores = _build_month_scores(rating, year_chi_idx)
    month_score_values = [row["score"] for row in month_scores]
    quy_nhan = build_quy_nhan(
        user_year_chi_idx=user_year_chi_idx,
        flow_year_chi_idx=year_chi_idx,
        dung_than=dung_than,
        year_can_chi=year_can_chi,
    )
    dai_van_next = _build_dai_van_next(tu_tru, gender, birth_date_iso)

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
        "month_score_values": month_score_values,
        "quy_nhan": quy_nhan,
        "dai_van_next": dai_van_next,
        "teaser": {
            "year_can_chi": year_can_chi,
            "year_rating": rating,
            "year_theme_vi": theme_parts[0],
        },
        "assumptions_vi": [
            "Điểm tháng là ước lượng theo quan hệ năm–Nhật Chủ và chi lưu niên (MVP).",
            "quy_nhan.tuoi_hop/xung theo Tam Hợp, Lục Hợp và xung tuổi năm sinh.",
        ],
    }
