"""
can_chi.py — Can Chi lookup tables and core primitives.

Ported from calendar-service.js §1-§2.
Source of truth: docs/algorithm.md §1, §2, §3, §7.

All functions are pure — no side effects, no I/O.
"""

from __future__ import annotations

from engine.bazi_solar import DEFAULT_TZ, bazi_cycle_year

# ─────────────────────────────────────────────────────────────────────────────
# 1. LOOKUP TABLES
# ─────────────────────────────────────────────────────────────────────────────

CAN_NAMES: list[str] = [
    "Giáp", "Ất", "Bính", "Đinh", "Mậu",
    "Kỷ", "Canh", "Tân", "Nhâm", "Quý",
]

CHI_NAMES: list[str] = [
    "Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ",
    "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi",
]

CAN_HANH: list[str] = [
    "Mộc", "Mộc", "Hỏa", "Hỏa", "Thổ",
    "Thổ", "Kim", "Kim", "Thủy", "Thủy",
]

CHI_HANH: list[str] = [
    "Thủy", "Thổ", "Mộc", "Mộc", "Thổ", "Hỏa",
    "Hỏa", "Thổ", "Kim", "Kim", "Thổ", "Thủy",
]

# 30 Nạp Âm pairs — index = pairIndex (0..29)
NAP_AM_HANH: list[str] = [
    "Kim",   # 0  Giáp Tý / Ất Sửu      Hải Trung Kim
    "Hỏa",  # 1  Bính Dần / Đinh Mão    Lò Trung Hỏa
    "Mộc",  # 2  Mậu Thìn / Kỷ Tỵ       Đại Lâm Mộc
    "Thổ",  # 3  Canh Ngọ / Tân Mùi     Lộ Bàng Thổ
    "Kim",   # 4  Nhâm Thân / Quý Dậu   Kiếm Phong Kim
    "Hỏa",  # 5  Giáp Tuất / Ất Hợi     Sơn Đầu Hỏa
    "Thủy", # 6  Bính Tý / Đinh Sửu     Giản Hạ Thủy
    "Thổ",  # 7  Mậu Dần / Kỷ Mão       Thành Đầu Thổ
    "Kim",   # 8  Canh Thìn / Tân Tỵ    Bạch Lạp Kim
    "Mộc",  # 9  Nhâm Ngọ / Quý Mùi    Dương Liễu Mộc
    "Thủy", # 10 Giáp Thân / Ất Dậu    Tuyền Trung Thủy
    "Thổ",  # 11 Bính Tuất / Đinh Hợi   Ốc Thượng Thổ
    "Hỏa",  # 12 Mậu Tý / Kỷ Sửu       Tích Lịch Hỏa
    "Mộc",  # 13 Canh Dần / Tân Mão     Tùng Bách Mộc
    "Thủy", # 14 Nhâm Thìn / Quý Tỵ    Trường Lưu Thủy
    "Kim",   # 15 Giáp Ngọ / Ất Mùi     Sa Trung Kim
    "Hỏa",  # 16 Bính Thân / Đinh Dậu   Sơn Hạ Hỏa
    "Mộc",  # 17 Mậu Tuất / Kỷ Hợi     Bình Địa Mộc
    "Thổ",  # 18 Canh Tý / Tân Sửu     Bích Thượng Thổ
    "Kim",  # 19 Nhâm Dần / Quý Mão    Kim Bạch Kim
    "Hỏa",  # 20 Giáp Thìn / Ất Tỵ     Phú Đăng Hỏa
    "Thủy", # 21 Bính Ngọ / Đinh Mùi    Thiên Hà Thủy
    "Thổ",  # 22 Mậu Thân / Kỷ Dậu     Đại Dịch Thổ
    "Kim",   # 23 Canh Tuất / Tân Hợi   Thoa Xuyến Kim
    "Mộc",  # 24 Nhâm Tý / Quý Sửu     Tang Đố Mộc
    "Thủy", # 25 Giáp Dần / Ất Mão     Đại Khê Thủy
    "Thổ",  # 26 Bính Thìn / Đinh Tỵ   Sa Trung Thổ
    "Hỏa",  # 27 Mậu Ngọ / Kỷ Mùi      Thiên Thượng Hỏa
    "Mộc",  # 28 Canh Thân / Tân Dậu   Thạch Lựu Mộc
    "Thủy", # 29 Nhâm Tuất / Quý Hợi   Đại Hải Thủy
]

NAP_AM_NAMES: list[str] = [
    "Hải Trung Kim", "Lò Trung Hỏa", "Đại Lâm Mộc", "Lộ Bàng Thổ",
    "Kiếm Phong Kim", "Sơn Đầu Hỏa", "Giản Hạ Thủy", "Thành Đầu Thổ",
    "Bạch Lạp Kim", "Dương Liễu Mộc", "Tuyền Trung Thủy", "Ốc Thượng Thổ",
    "Tích Lịch Hỏa", "Tùng Bách Mộc", "Trường Lưu Thủy", "Sa Trung Kim",
    "Sơn Hạ Hỏa", "Bình Địa Mộc", "Bích Thượng Thổ", "Kim Bạch Kim",
    "Phú Đăng Hỏa", "Thiên Hà Thủy", "Đại Dịch Thổ", "Thoa Xuyến Kim",
    "Tang Đố Mộc", "Đại Khê Thủy", "Sa Trung Thổ", "Thiên Thượng Hỏa",
    "Thạch Lựu Mộc", "Đại Hải Thủy",
]

# Dương Thần / Kỵ Thần — element that helps / harms the mệnh
DUONG_THAN: dict[str, str] = {
    "Kim": "Thổ", "Mộc": "Thủy", "Thủy": "Kim",
    "Hỏa": "Mộc", "Thổ": "Hỏa",
}

KY_THAN: dict[str, str] = {
    "Kim": "Hỏa", "Mộc": "Kim", "Thủy": "Thổ",
    "Hỏa": "Thủy", "Thổ": "Mộc",
}

# Can Khắc map: dayCan khắc yearCan (attacker → target)
CAN_KHAC_MAP: dict[int, int] = {
    0: 4, 1: 5, 2: 6, 3: 7, 4: 8,
    5: 9, 6: 0, 7: 1, 8: 2, 9: 3,
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. CORE FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_jdn(y: int, m: int, d: int) -> int:
    """Julian Day Number (integer) from Gregorian date."""
    a = (14 - m) // 12
    yr = y + 4800 - a
    mo = m + 12 * a - 3
    return (
        d
        + (153 * mo + 2) // 5
        + 365 * yr
        + yr // 4
        - yr // 100
        + yr // 400
        - 32045
    )


# Anchor: 1900-01-31 = Giáp Tý
ANCHOR_JDN = 2415051


def get_can_chi_day(year: int, month: int, day: int) -> dict:
    """
    Can Chi for a solar date.

    Returns dict with keys:
        can_idx, chi_idx, can_name, chi_name, can_hanh, chi_hanh
    """
    jdn = get_jdn(year, month, day)
    offset = jdn - ANCHOR_JDN
    can_idx = ((offset % 10) + 10) % 10
    chi_idx = ((offset % 12) + 12) % 12
    return {
        "can_idx": can_idx,
        "chi_idx": chi_idx,
        "can_name": CAN_NAMES[can_idx],
        "chi_name": CHI_NAMES[chi_idx],
        "can_hanh": CAN_HANH[can_idx],
        "chi_hanh": CHI_HANH[chi_idx],
    }


def get_can_chi_year(solar_year: int) -> dict:
    """
    Can Chi for a solar year.

    Returns dict with keys: can_idx, chi_idx, can_name, chi_name
    """
    can_idx = ((solar_year - 4) % 10 + 10) % 10
    chi_idx = ((solar_year - 4) % 12 + 12) % 12
    return {
        "can_idx": can_idx,
        "chi_idx": chi_idx,
        "can_name": CAN_NAMES[can_idx],
        "chi_name": CHI_NAMES[chi_idx],
    }


def get_nap_am_pair_idx(can_idx: int, chi_idx: int) -> int:
    """
    Nạp Âm pair index (0-29) from Can Chi indices.
    Uses CRT: unique 60-cycle position collapsed to 30 pairs.
    """
    cycle_pos = (can_idx * 36 + chi_idx * 25) % 60
    return cycle_pos // 2


def _menh_nap_am_from_can_chi(cc: dict) -> dict:
    pair_idx = get_nap_am_pair_idx(cc["can_idx"], cc["chi_idx"])
    hanh = NAP_AM_HANH[pair_idx]
    return {
        "hanh": hanh,
        "name": NAP_AM_NAMES[pair_idx],
        "duong_than": DUONG_THAN[hanh],
        "ky_than": KY_THAN[hanh],
    }


def get_menh_nap_am_from_date(
    year: int,
    month: int,
    day: int,
    tz: float | None = None,
) -> dict:
    """
    Nạp Âm mệnh theo **năm Can Chi Bát Tự** (ranh giới Lập Xuân).

    Trước Lập Xuân của năm dương lịch ``year`` → thuộc năm trụ ``year - 1``
    (cùng quy ước ``bazi_cycle_year`` / trụ Năm trong ``get_tu_tru``).

    Returns dict with keys: hanh, name, duong_than, ky_than
    """
    t = DEFAULT_TZ if tz is None else tz
    cycle_y = bazi_cycle_year(year, month, day, t)
    cc = get_can_chi_year(cycle_y)
    return _menh_nap_am_from_can_chi(cc)


def get_menh_nap_am(birth_year: int) -> dict:
    """
    Nạp Âm mệnh chỉ từ **số năm dương lịch** (coi Can Chi năm = ``get_can_chi_year(birth_year)``).

    Không dùng cho hiển thị mệnh người sinh khi chỉ biết năm: trước Lập Xuân,
    mệnh thuộc năm trụ trước — dùng :func:`get_menh_nap_am_from_date`.
    Giữ hàm này cho tương thích & test vector theo năm.
    """
    cc = get_can_chi_year(birth_year)
    return _menh_nap_am_from_can_chi(cc)


def is_xung(chi_a: int, chi_b: int) -> bool:
    """Địa Chi Tương Xung — severity 3."""
    return abs(chi_a - chi_b) == 6


def is_can_khac(day_can_idx: int, year_can_idx: int) -> bool:
    """Thiên Can Tương Khắc — severity 2. Not symmetric."""
    return CAN_KHAC_MAP.get(day_can_idx) == year_can_idx
