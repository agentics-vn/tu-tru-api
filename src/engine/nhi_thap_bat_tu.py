"""
nhi_thap_bat_tu.py — Nhị Thập Bát Tú (28 Lunar Mansions) engine.

Formula: tuIdx = (JDN + 11) % 28
Calibrated from Jōkyō calendar reform (貞享暦):
  Feb 4, 1685 (JDN 2336529) = Tinh (idx 24).

Source of truth: docs/seed/sao-ngay.json → nhi_thap_bat_tu
"""

from __future__ import annotations

from engine.can_chi import get_jdn

# ─────────────────────────────────────────────────────────────────────────────
# 28 Tú data (idx 0-27)
# ─────────────────────────────────────────────────────────────────────────────

TU_28: list[dict] = [
    {"idx": 0,  "name": "Giác",   "hanh": "Mộc",   "tot_xau": "tốt"},
    {"idx": 1,  "name": "Cang",   "hanh": "Kim",   "tot_xau": "xấu"},
    {"idx": 2,  "name": "Đê",     "hanh": "Thổ",   "tot_xau": "xấu"},
    {"idx": 3,  "name": "Phòng",  "hanh": "Nhật",  "tot_xau": "tốt"},
    {"idx": 4,  "name": "Tâm",    "hanh": "Nguyệt","tot_xau": "xấu"},
    {"idx": 5,  "name": "Vĩ",     "hanh": "Hỏa",  "tot_xau": "tốt"},
    {"idx": 6,  "name": "Cơ",     "hanh": "Thủy",  "tot_xau": "tốt"},
    {"idx": 7,  "name": "Đẩu",    "hanh": "Mộc",   "tot_xau": "tốt"},
    {"idx": 8,  "name": "Ngưu",   "hanh": "Kim",   "tot_xau": "xấu"},
    {"idx": 9,  "name": "Nữ",     "hanh": "Thổ",   "tot_xau": "xấu"},
    {"idx": 10, "name": "Hư",     "hanh": "Nhật",  "tot_xau": "xấu"},
    {"idx": 11, "name": "Nguy",   "hanh": "Nguyệt","tot_xau": "xấu"},
    {"idx": 12, "name": "Thất",   "hanh": "Hỏa",  "tot_xau": "tốt"},
    {"idx": 13, "name": "Bích",   "hanh": "Thủy",  "tot_xau": "tốt"},
    {"idx": 14, "name": "Khuê",   "hanh": "Mộc",   "tot_xau": "vừa"},
    {"idx": 15, "name": "Lâu",    "hanh": "Kim",   "tot_xau": "tốt"},
    {"idx": 16, "name": "Vị",     "hanh": "Thổ",   "tot_xau": "xấu"},
    {"idx": 17, "name": "Mão",    "hanh": "Nhật",  "tot_xau": "tốt"},
    {"idx": 18, "name": "Tất",    "hanh": "Nguyệt","tot_xau": "tốt"},
    {"idx": 19, "name": "Chủy",   "hanh": "Hỏa",  "tot_xau": "xấu"},
    {"idx": 20, "name": "Sâm",    "hanh": "Thủy",  "tot_xau": "tốt"},
    {"idx": 21, "name": "Tỉnh",   "hanh": "Mộc",   "tot_xau": "tốt"},
    {"idx": 22, "name": "Quỷ",    "hanh": "Kim",   "tot_xau": "xấu"},
    {"idx": 23, "name": "Liễu",   "hanh": "Thổ",   "tot_xau": "xấu"},
    {"idx": 24, "name": "Tinh",   "hanh": "Nhật",  "tot_xau": "xấu"},
    {"idx": 25, "name": "Trương", "hanh": "Nguyệt","tot_xau": "tốt"},
    {"idx": 26, "name": "Dực",    "hanh": "Hỏa",  "tot_xau": "xấu"},
    {"idx": 27, "name": "Chẩn",   "hanh": "Thủy",  "tot_xau": "tốt"},
]

OFFSET = 11


def get_nhi_thap_bat_tu(year: int, month: int, day: int) -> dict:
    """
    Get the 28 Lunar Mansion for a solar date.

    Args:
        year, month, day: Gregorian date

    Returns:
        dict with keys: idx, name, hanh, tot_xau
    """
    jdn = get_jdn(year, month, day)
    idx = (jdn + OFFSET) % 28
    tu = TU_28[idx]
    return {
        "idx": tu["idx"],
        "name": tu["name"],
        "hanh": tu["hanh"],
        "tot_xau": tu["tot_xau"],
    }
