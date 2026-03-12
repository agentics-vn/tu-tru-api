"""
sao_ngay.py — Day Star checks (Thiên Đức, Nguyệt Đức, etc.).

Ported from calendar-service.js §4.
Source of truth: docs/algorithm.md §12.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Thiên Đức — one per lunar month, matches either Can or Chi
# ─────────────────────────────────────────────────────────────────────────────

THIEN_DUC: list[dict] = [
    {"type": "can", "idx": 3},   # month 1:  Đinh
    {"type": "chi", "idx": 7},   # month 2:  Thân
    {"type": "can", "idx": 8},   # month 3:  Nhâm
    {"type": "can", "idx": 7},   # month 4:  Tân
    {"type": "chi", "idx": 11},  # month 5:  Hợi
    {"type": "can", "idx": 0},   # month 6:  Giáp
    {"type": "can", "idx": 9},   # month 7:  Quý
    {"type": "chi", "idx": 2},   # month 8:  Dần
    {"type": "can", "idx": 2},   # month 9:  Bính
    {"type": "can", "idx": 1},   # month 10: Ất
    {"type": "chi", "idx": 5},   # month 11: Tỵ
    {"type": "can", "idx": 6},   # month 12: Canh
]

# Thiên Đức Hợp — Can index, None = tháng tứ trọng
THIEN_DUC_HOP: list[int | None] = [8, None, 3, 2, None, 5, 4, None, 7, 6, None, 1]

# Nguyệt Đức — Can index per month
NGUYET_DUC_CAN: list[int] = [2, 0, 8, 6, 2, 0, 8, 6, 2, 0, 8, 6]

# Nguyệt Đức Hợp — Can index per month
NGUYET_DUC_HOP_CAN: list[int] = [7, 5, 3, 1, 7, 5, 3, 1, 7, 5, 3, 1]


def check_thien_duc(lunar_month: int, day_can_idx: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Đức for the given lunar month."""
    td = THIEN_DUC[lunar_month - 1]
    if td["type"] == "can":
        return day_can_idx == td["idx"]
    return day_chi_idx == td["idx"]


def check_thien_duc_hop(lunar_month: int, day_can_idx: int) -> bool:
    """Check if day has Thiên Đức Hợp for the given lunar month."""
    tdh = THIEN_DUC_HOP[lunar_month - 1]
    return tdh is not None and day_can_idx == tdh


def check_nguyet_duc(lunar_month: int, day_can_idx: int) -> bool:
    """Check if day has Nguyệt Đức for the given lunar month."""
    return day_can_idx == NGUYET_DUC_CAN[lunar_month - 1]


def check_nguyet_duc_hop(lunar_month: int, day_can_idx: int) -> bool:
    """Check if day has Nguyệt Đức Hợp for the given lunar month."""
    return day_can_idx == NGUYET_DUC_HOP_CAN[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Thọ Tử (受死日) — KỴ TUYỆT ĐỐI cho phẫu thuật
# By lunar month → forbidden day Chi index (Chi-only method, more conservative).
# Source: Ngọc Hạp Thông Thư.
# Cross-ref: blogphongthuy.com, chuyenhakienvang.com, nhungtho.vn.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

THO_TU_CHI: list[int] = [10, 4, 11, 5, 0, 6, 1, 7, 2, 8, 3, 9]
# Month:  1→Tuất(10), 2→Thìn(4), 3→Hợi(11), 4→Tỵ(5), 5→Tý(0), 6→Ngọ(6),
#         7→Sửu(1),  8→Mùi(7),  9→Dần(2), 10→Thân(8), 11→Mão(3), 12→Dậu(9)


def check_tho_tu(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day is Thọ Tử (受死日) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THO_TU_CHI[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Giải Thần (解神) — Cát tinh, tốt cho chữa bệnh / giải trừ
# By lunar month → favorable day Chi (pairs of months share same Chi).
# Source: Ngọc Hạp Thông Thư, Lịch Lệ.
# Cross-ref: xemvm.com.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

GIAI_THAN_CHI: list[int] = [8, 8, 10, 10, 0, 0, 2, 2, 4, 4, 6, 6]
# Month: 1,2→Thân(8), 3,4→Tuất(10), 5,6→Tý(0), 7,8→Dần(2), 9,10→Thìn(4), 11,12→Ngọ(6)


def check_giai_than(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Giải Thần (解神) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == GIAI_THAN_CHI[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Thiên Ân (天恩日) — Cát tinh, 15 fixed Can-Chi combinations
# Rule: Giáp Tý→Mậu Thìn (5), Kỷ Mão→Quý Mùi (5), Kỷ Dậu→Quý Sửu (5) = 15 ngày
# Source: Hiệp Kỷ Biện Phương Thư.
# Cross-ref: xemvm.com.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

THIEN_AN_PAIRS: frozenset[tuple[int, int]] = frozenset({
    # Group 1: Giáp Tý → Mậu Thìn (first 5 of 60 Hoa Giáp)
    (0, 0),   # Giáp Tý
    (1, 1),   # Ất Sửu
    (2, 2),   # Bính Dần
    (3, 3),   # Đinh Mão
    (4, 4),   # Mậu Thìn
    # Group 2: Kỷ Mão → Quý Mùi
    (5, 3),   # Kỷ Mão
    (6, 4),   # Canh Thìn
    (7, 5),   # Tân Tỵ
    (8, 6),   # Nhâm Ngọ
    (9, 7),   # Quý Mùi
    # Group 3: Kỷ Dậu → Quý Sửu
    (5, 9),   # Kỷ Dậu
    (6, 10),  # Canh Tuất
    (7, 11),  # Tân Hợi
    (8, 0),   # Nhâm Tý
    (9, 1),   # Quý Sửu
})


def check_thien_an(day_can_idx: int, day_chi_idx: int) -> bool:
    """Check if day is Thiên Ân (天恩日) — fixed set of Can-Chi pairs."""
    return (day_can_idx, day_chi_idx) in THIEN_AN_PAIRS


# ─────────────────────────────────────────────────────────────────────────────
# Thiên Phúc (天福) — Cát tinh
# By lunar month → favorable day Chi.
# NOTE: Tử Vi version uses Thiên Can (year-based). This trạch nhật version
#       uses lunar month → day Chi. Could not find independent verification.
# Source: Ngọc Hạp Thông Thư (unconfirmed).  _sme_verified = False
# ─────────────────────────────────────────────────────────────────────────────

THIEN_PHUC_CHI: list[int] = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 11, 10]
# Month: 1→Dậu(9), 2→Thân(8), 3→Mùi(7), 4→Ngọ(6), 5→Tỵ(5), 6→Thìn(4),
#        7→Mão(3), 8→Dần(2), 9→Sửu(1), 10→Tý(0), 11→Hợi(11), 12→Tuất(10)


def check_thien_phuc(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Phúc (天福) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THIEN_PHUC_CHI[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Dịch Mã (驛馬) — Cát tinh cho xuất hành, cầu y
# By year Chi → day Chi (Tam Hợp method).
# Source: docs/algorithm.md §6.2, Tam Mệnh Thông Hội.
# Cross-ref: lyso.vn, tuvibattu.vn, thuatso.com.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

DICH_MA_MAP: dict[int, int] = {
    2: 8, 6: 8, 10: 8,     # Dần/Ngọ/Tuất → Thân
    8: 2, 0: 2, 4: 2,      # Thân/Tý/Thìn → Dần
    5: 11, 9: 11, 1: 11,   # Tỵ/Dậu/Sửu → Hợi
    11: 5, 3: 5, 7: 5,     # Hợi/Mão/Mùi → Tỵ
}


def check_dich_ma(day_chi_idx: int, year_chi_idx: int) -> bool:
    """Check if day has Dịch Mã (驛馬) based on year's Chi."""
    target = DICH_MA_MAP.get(year_chi_idx)
    return target is not None and day_chi_idx == target


# ─────────────────────────────────────────────────────────────────────────────
# Nguyệt Sát (月殺) — Hung tinh
# Rule: "Chánh nguyệt khởi Sửu, nghịch hành tứ quý" (Sửu→Tuất→Mùi→Thìn)
# Source: Hiệp Kỷ Biện Phương Thư, Ngọc Hạp Thông Thư.
# Cross-ref: xemvm.com, phongthuytuongminh.com.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

NGUYET_SAT_CHI: list[int] = [1, 10, 7, 4, 1, 10, 7, 4, 1, 10, 7, 4]
# Months 1,5,9→Sửu(1), 2,6,10→Tuất(10), 3,7,11→Mùi(7), 4,8,12→Thìn(4)


def check_nguyet_sat(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Nguyệt Sát (月殺) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == NGUYET_SAT_CHI[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Thiên Cương (天罡) — Hung tinh
# By lunar month → forbidden day Chi.
# Formula: (lunarMonth + 3) % 12
# NOTE: Thiên Cương in Độn Thiên Cương is more complex (day+hour based).
#       This simplified month→chi formula needs SME review.
# Source: Ngọc Hạp Thông Thư.  _sme_verified = False
# ─────────────────────────────────────────────────────────────────────────────


def check_thien_cuong(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Cương (天罡) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (lunar_month + 3) % 12


# ─────────────────────────────────────────────────────────────────────────────
# Đại Hao (大耗) — Hung tinh (a.k.a. Quan Phù, Tử Khí)
# By lunar month → forbidden day Chi.
# Rule: "Quan phù tháng giêng khởi ở Ngọ, thuận hành 12 thời"
# Formula: (lunarMonth + 5) % 12
# Source: Lịch Lệ, Ngọc Hạp Thông Thư.
# Cross-ref: xemvm.com.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────


def check_dai_hao(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Đại Hao (大耗) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (lunar_month + 5) % 12


# ─────────────────────────────────────────────────────────────────────────────
# Sát Chủ Âm (殺主) — Hung tinh, kỵ phẫu thuật / an táng / tế tự
# By lunar month → forbidden day Chi.
# Source: blogphongthuy.com, movinghouse.vn.
# Cross-ref: multiple Vietnamese almanac sites.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

SAT_CHU_CHI: list[int] = [5, 0, 7, 3, 8, 10, 11, 1, 6, 9, 2, 4]
# Month: 1→Tỵ(5), 2→Tý(0), 3→Mùi(7), 4→Mão(3), 5→Thân(8), 6→Tuất(10),
#        7→Hợi(11), 8→Sửu(1), 9→Ngọ(6), 10→Dậu(9), 11→Dần(2), 12→Thìn(4)


def check_sat_chu(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Sát Chủ (殺主) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == SAT_CHU_CHI[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Thiên Tặc (天賊) — Hung tinh
# By lunar month → forbidden day Chi.
# Source: lichngaytot.com, xemvm.com, phongthuykybach.com.
# Cross-ref: Hiệp Kỷ Biện Phương Thư.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

THIEN_TAC_CHI: list[int] = [4, 9, 2, 7, 0, 5, 10, 3, 8, 1, 6, 11]
# Month: 1→Thìn(4), 2→Dậu(9), 3→Dần(2), 4→Mùi(7), 5→Tý(0), 6→Tỵ(5),
#        7→Tuất(10), 8→Mão(3), 9→Thân(8), 10→Sửu(1), 11→Ngọ(6), 12→Hợi(11)


def check_thien_tac(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Tặc (天賊) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THIEN_TAC_CHI[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Thiên Ngục (天獄) + Thiên Hỏa (天火) — Hung tinh compound
# Two separate stars, both kỵ phẫu thuật. Triggered if either matches.
# By lunar month → forbidden day Chi.
# Source: Ngọc Hạp Thông Thư.  _sme_verified = False
# ─────────────────────────────────────────────────────────────────────────────

THIEN_NGUC_CHI: list[int] = [4, 4, 7, 7, 10, 10, 1, 1, 4, 4, 7, 7]
# Grouped by season: Spring(1,2)→Thìn, Summer(3,4)→Mùi, Autumn(5,6)→Tuất, Winter(7,8)→Sửu, repeats

THIEN_HOA_CHI: list[int] = [6, 6, 9, 9, 0, 0, 3, 3, 6, 6, 9, 9]
# Grouped by season: Spring(1,2)→Ngọ, Summer(3,4)→Dậu, Autumn(5,6)→Tý, Winter(7,8)→Mão, repeats


def check_thien_nguc_thien_hoa(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Ngục or Thiên Hỏa for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return (
        day_chi_idx == THIEN_NGUC_CHI[lunar_month - 1]
        or day_chi_idx == THIEN_HOA_CHI[lunar_month - 1]
    )
