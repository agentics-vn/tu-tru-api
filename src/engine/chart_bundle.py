"""
chart_bundle.py — Single-pass Tứ Trụ chart analysis (hóa hợp + cường nhược + Thập Thần).

Avoids recomputing detect_stem_transformations() across la_so / tu_tru / dung_than.
"""

from __future__ import annotations

from typing import Any

from engine.chart_contract import merge_chart_contract_into_result
from engine.cung_menh import analyze_cung_menh
from engine.dai_van import get_dai_van_with_dates
from engine.luu_nien_list import build_luu_nien_list
from engine.than_sat import analyze_than_sat
from engine.thap_than import (
    analyze_pho_tinh,
    analyze_tang_can_display,
    analyze_thap_than,
    short_thap_than_label,
)
from engine.tiet_khi_meta import build_calendar_header
from engine.truong_sinh import analyze_truong_sinh
from engine.tuan_khong import analyze_tuan_khong
from engine.can_chi import (
    CAN_HANH,
    CHI_HANH,
    NAP_AM_HANH,
    NAP_AM_NAMES,
    get_nap_am_pair_idx,
)
from engine.hoa_hop import effective_stem_hanh
from engine.pillars import BIRTH_HOUR_LABELS
from engine.cuong_nhuoc import analyze_chart_strength
from engine import dung_than_v2
from engine.dung_than import find_dung_than
from engine.hoa_hop import build_stem_transformations_payload, detect_stem_transformations


def build_chart_analysis(
    tu_tru: dict,
    dung_than_rule: str = "v1",
    co_gio: bool = True,
) -> dict[str, Any]:
    """
    Compute transforms, strength, dụng thần, thập thần once per request.

    ``dung_than_rule`` chỉ đổi ``dung_than_info`` (xem ``find_dung_than``); mặc định ``"v1"`` cho
    đúng đầu ra cũ.

    ``co_gio=False`` (chỉ ở ``2026-10.1``; v1 thì ``ValueError``): trụ giờ của ``tu_tru`` là giữ chỗ.
    ``transforms``/``stem_transformations`` là các cặp hợp hoá ba trụ của luật mới (đặc tả mục 7);
    ``strength_info`` và ``thap_than`` là phân tích v1 BỐN trụ nên là ``None``, không đặt một bản
    đọc trụ giờ giả cạnh kết quả ba trụ.

    Returns dict with keys: transforms, strength_info, dung_than_info, thap_than,
    stem_transformations (API payload).
    """
    if not co_gio:
        dung_than_info = find_dung_than(tu_tru, rule=dung_than_rule, co_gio=False)
        transforms = dung_than_v2.hop_hoa(tu_tru, co_gio=False)
        return {
            "transforms": transforms,
            "strength_info": None,
            "dung_than_info": dung_than_info,
            "thap_than": None,
            "stem_transformations": build_stem_transformations_payload(tu_tru, transforms),
        }
    transforms = detect_stem_transformations(tu_tru)
    strength_info = analyze_chart_strength(tu_tru, transforms)
    dung_than_info = find_dung_than(
        tu_tru, analysis=strength_info, rule=dung_than_rule, co_gio=co_gio,
    )
    thap_than = analyze_thap_than(tu_tru, transforms)
    stem_payload = build_stem_transformations_payload(tu_tru, transforms)
    return {
        "transforms": transforms,
        "strength_info": strength_info,
        "dung_than_info": dung_than_info,
        "thap_than": thap_than,
        "stem_transformations": stem_payload,
    }


# Hợp đồng thiếu giờ của ``build_full_chart`` (``co_gio=False``, chỉ ở luật ``2026-10.1``).
# ``birth_time`` của yêu cầu khi ấy chỉ là GIỮ CHỖ: mọi trường dưới đây khác v1 và KHÔNG đọc nó.
#   null      — trường chỉ có nghĩa khi biết giờ (trụ giờ, mệnh cung, giờ khởi vận…) hoặc là
#               phân tích v1 BỐN trụ (cường nhược, thập thần): trả null, không đoán.
#   ba_tru    — tính lại trên năm–tháng–ngày (đặc tả mục 7: bỏ can, tàng can và mọi cặp hợp hoá có
#               trụ giờ). ``element_counts``/``ngu_hanh`` = L của luật mới (đặc tả mục 3: cùng định
#               nghĩa với ``element_counts``), đếm bằng số nguyên đơn vị 0,1, in L/10; đây là nguồn
#               ``hanh_thieu`` của sản phẩm.
#   theo_ngay — chế độ không giờ sẵn có của engine: tiết khí theo kinh độ Mặt Trời của NGÀY (cùng
#               phép tính với trụ tháng), dương lịch không kèm giờ.
# Trường không có ở đây thì đúng v1 (đã không phụ thuộc giờ). Đường là khoá trong ``menh_ban``.
THIEU_GIO_MENH_BAN: dict[str, str] = {
    "tu_tru_display": "ba_tru",
    "header.birth_time_label": "null",
    "header.duong_lich_display": "theo_ngay",
    "header.tiet_khi": "theo_ngay",
    "header.khoi_van_date": "null",
    "pillars.hour": "null",
    "pillars.day.can": "ba_tru",
    "dai_van.virtual_days": "null",
    "dai_van.khoi_van_date": "null",
    "dai_van.jie_datetime": "null",
    "menh_cung": "null",
    "chart_analysis.stem_transformations": "ba_tru",
    "chart_analysis.strength_info": "null",
    "chart_analysis.dung_than_info": "ba_tru",
    "chart_analysis.thap_than": "null",
    "stem_transformations": "ba_tru",
    "element_counts": "ba_tru",
    "ngu_hanh": "ba_tru",
    "cuong_nhuoc": "null",
    "chart_strength": "null",
    "cuong_nhuoc_detail": "null",
    "god_groups": "null",
    "surface_god_counts": "null",
    "_raw": "null",
}


# Nhãn tiếng Việt cho vị trí trụ trong Tứ Trụ.
_PILLAR_LABELS_VI: dict[str, str] = {
    "year": "Trụ Năm",
    "month": "Trụ Tháng",
    "day": "Trụ Ngày",
    "hour": "Trụ Giờ",
}


def _pillar_surface_thap_than(pillar_key: str, thap_than: dict) -> dict:
    if pillar_key == "day":
        return {"key": "nhat_chu", "name": "NHẬT CHỦ", "short_label": "NHẬT CHỦ"}
    g = thap_than[f"{pillar_key}_god"]
    return {
        "key": g["key"],
        "name": g["name"],
        "short_label": short_thap_than_label(g["key"]),
    }


def _build_pillar_row(
    tu_tru: dict,
    pillar_key: str,
    transforms: list[dict],
    thap_than: dict,
    pho_tinh: dict,
    tang_can: dict,
    truong_sinh: dict,
    than_sat: dict,
) -> dict:
    p = tu_tru[pillar_key]
    pair_idx = get_nap_am_pair_idx(p["can_idx"], p["chi_idx"])
    eff_hanh, transformed = effective_stem_hanh(
        pillar_key, p["can_idx"], transforms,
    )
    return {
        "key": pillar_key,
        "label_vi": _PILLAR_LABELS_VI.get(pillar_key, pillar_key),
        "can": {
            "idx": p["can_idx"],
            "name": p["can_name"],
            "hanh": CAN_HANH[p["can_idx"]],
            "effective_hanh": eff_hanh,
            "transformed": transformed,
        },
        "chi": {
            "idx": p["chi_idx"],
            "name": p["chi_name"],
            "hanh": CHI_HANH[p["chi_idx"]],
        },
        "display": f"{p['can_name']} {p['chi_name']}",
        "nap_am": {
            "name": NAP_AM_NAMES[pair_idx],
            "hanh": NAP_AM_HANH[pair_idx],
        },
        "thap_than": _pillar_surface_thap_than(pillar_key, thap_than),
        "tang_can": tang_can[pillar_key],
        "pho_tinh": pho_tinh[pillar_key],
        "truong_sinh": truong_sinh[pillar_key],
        "than_sat": than_sat[pillar_key],
    }


def build_full_chart(
    tu_tru: dict,
    birth_date: str,
    gender: int,
    birth_time_slot: int,
    birth_minute: int = 0,
    name: str | None = None,
    num_dai_van: int = 10,
    num_luu_nien: int = 10,
    view_year: int | None = None,
    dung_than_rule: str = "v1",
    co_gio: bool = True,
) -> dict[str, Any]:
    """
    Full Mệnh Bàn Tứ Trụ payload for POST /v1/la-so-full.

    ``dung_than_rule``/``co_gio``: xem ``build_chart_analysis``. Có giờ thì chỉ
    ``chart_analysis.dung_than_info`` theo luật được chọn, mọi trường khác đúng v1. ``co_gio=False``
    thì ``birth_time_slot`` là giữ chỗ và đầu ra theo hợp đồng ``THIEU_GIO_MENH_BAN``: không trường
    nào đọc nó (test ``test_thieu_gio_bat_bien_13_khung``).
    """
    analysis = build_chart_analysis(tu_tru, dung_than_rule, co_gio)
    transforms = analysis["transforms"]
    # Hàng trụ năm/tháng chỉ đọc year_god/month_god; thiếu giờ thì dựng với các cặp hợp hoá ba trụ.
    thap_than = analysis["thap_than"] if co_gio else analyze_thap_than(tu_tru, transforms)
    pho_tinh = analyze_pho_tinh(tu_tru)
    tang_can = analyze_tang_can_display(tu_tru)
    truong_sinh = analyze_truong_sinh(tu_tru)
    than_sat = analyze_than_sat(tu_tru)
    cung = analyze_cung_menh(tu_tru)
    tuan = analyze_tuan_khong(tu_tru)
    dai_van = get_dai_van_with_dates(
        tu_tru,
        gender,
        birth_date,
        birth_time_slot if co_gio else None,
        birth_minute,
        num_dai_van,
    )
    if not co_gio:
        # Tuổi khởi vận và các vận đếm theo NGÀY (civil_days_to_jie); ba trường dưới tính tới giờ.
        for k in ("virtual_days", "khoi_van_date", "jie_datetime"):
            dai_van[k] = None
    luu_nien = build_luu_nien_list(
        birth_date, num_luu_nien, start_year=view_year,
    )
    if view_year is not None:
        for row in luu_nien:
            row["selected"] = row["year"] == view_year
    header = build_calendar_header(
        birth_date,
        tu_tru["month"]["chi_name"],
        BIRTH_HOUR_LABELS.get(birth_time_slot) if co_gio else None,
        birth_time_slot=birth_time_slot if co_gio else None,
        birth_minute=birth_minute,
    )
    if not co_gio:
        header["birth_time_label"] = None
    gender_label = "Dương Càn tạo" if gender == 1 else "Âm Khôn tạo"

    pillars = {
        pk: _build_pillar_row(
            tu_tru, pk, transforms, thap_than, pho_tinh, tang_can,
            truong_sinh, than_sat,
        )
        for pk in (("year", "month", "day", "hour") if co_gio else ("year", "month", "day"))
    }
    if not co_gio:
        pillars["hour"] = None

    result: dict[str, Any] = {
        "tu_tru_display": tu_tru["display"],
        "nhat_chu": tu_tru["nhat_chu"],
        "header": {
            **header,
            "name": name,
            "gender": gender,
            "gender_label": gender_label,
            "khoi_van_date": dai_van["khoi_van_date"],
        },
        "pillars": pillars,
        "dai_van": dai_van,
        "luu_nien": luu_nien,
        "menh_cung": cung["menh_cung"],
        "thai_nguyen": cung["thai_nguyen"],
        "tuan_khong": tuan,
        "chart_analysis": {
            "stem_transformations": analysis["stem_transformations"],
            "strength_info": analysis["strength_info"],
            "dung_than_info": analysis["dung_than_info"],
            "thap_than": analysis["thap_than"],
        },
    }
    # Lazy import avoids chart_bundle ↔ la_so cycle
    from engine.la_so import build_la_so_chart_contract

    chart_contract = build_la_so_chart_contract(tu_tru, gender, birth_date)
    merge_chart_contract_into_result(result, chart_contract)
    if not co_gio:
        _ba_tru(result, tu_tru, analysis)
    return result


def _ba_tru(result: dict[str, Any], tu_tru: dict, analysis: dict[str, Any]) -> None:
    """Thiếu giờ: đặt các trường của ``THIEU_GIO_MENH_BAN`` mà phần dựng chung ở trên còn để v1."""
    L = dung_than_v2.luc(tu_tru, co_gio=False)["L"]
    ba = {h: L[h] / dung_than_v2.DON_VI for h in ("Kim", "Mộc", "Thủy", "Hỏa", "Thổ")}
    result["tu_tru_display"] = " | ".join(
        f"{tu_tru[p]['can_name']} {tu_tru[p]['chi_name']}" for p in ("year", "month", "day"))
    result["menh_cung"] = None
    result["stem_transformations"] = analysis["stem_transformations"]
    result["element_counts"] = ba
    result["ngu_hanh"] = dict(ba)
    for k in ("cuong_nhuoc", "chart_strength", "cuong_nhuoc_detail", "god_groups",
              "surface_god_counts", "_raw"):
        result[k] = None
