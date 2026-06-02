"""
luu_nguyet.py — Lưu nguyệt (流月) pillar (solar month, simplified).

Shared by tieu-van legacy and van-trinh-nam luan-context.
"""

from __future__ import annotations

from engine.can_chi import (
    CHI_NAMES,
    CAN_NAMES,
    NAP_AM_HANH,
    NAP_AM_NAMES,
    get_can_chi_year,
    get_nap_am_pair_idx,
)
from engine.verdict_signal import element_relation_nhat_chu

# Menh relation (legacy tieu-van)
TUONG_SINH = {
    "Kim": "Thủy", "Thủy": "Mộc", "Mộc": "Hỏa",
    "Hỏa": "Thổ", "Thổ": "Kim",
}
TUONG_KHAC = {
    "Kim": "Mộc", "Mộc": "Thổ", "Thổ": "Thủy",
    "Thủy": "Hỏa", "Hỏa": "Kim",
}


def element_relation_menh(month_hanh: str, menh_hanh: str) -> str:
    if month_hanh == menh_hanh:
        return "binh_hoa"
    if TUONG_SINH.get(month_hanh) == menh_hanh:
        return "bi_sinh"
    if TUONG_SINH.get(menh_hanh) == month_hanh:
        return "tuong_sinh"
    if TUONG_KHAC.get(month_hanh) == menh_hanh:
        return "bi_khac"
    if TUONG_KHAC.get(menh_hanh) == month_hanh:
        return "tuong_khac"
    return "binh_hoa"


def get_luu_nguyet_pillar(year: int, month: int) -> dict:
    """Solar month pillar (Ngũ Hổ Độn Nguyệt, simplified — see meta.disclaimers)."""
    year_cc = get_can_chi_year(year)
    year_can = year_cc["can_idx"]
    month_chi = (month + 1) % 12
    start_can = ((year_can % 5) * 2 + 2) % 10
    month_can = (start_can + month - 1) % 10
    pair_idx = get_nap_am_pair_idx(month_can, month_chi)
    return {
        "can_idx": month_can,
        "chi_idx": month_chi,
        "can_name": CAN_NAMES[month_can],
        "chi_name": CHI_NAMES[month_chi],
        "display": f"{CAN_NAMES[month_can]} {CHI_NAMES[month_chi]}",
        "nap_am_hanh": NAP_AM_HANH[pair_idx],
        "nap_am_name": NAP_AM_NAMES[pair_idx],
    }
