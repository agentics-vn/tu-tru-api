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
# Thiên Cương (天罡) — Hung tinh, "diệt môn", bách sự hung
# By lunar month → forbidden day Chi.
# Source: 《玉匣記》逐月凶星總局:
#   "天罡一云灭门，百事凶。正月巳、二月子、三月未、四月寅、
#    五月酉、六月辰、七月亥、八月午、九月丑、十月申、
#    十一月卯、十二月戌。"
# Cross-ref: phongthuykybach.com.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

THIEN_CUONG_CHI: list[int] = [5, 0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10]
# Month: 1→Tỵ(5), 2→Tý(0), 3→Mùi(7), 4→Dần(2), 5→Dậu(9), 6→Thìn(4),
#        7→Hợi(11), 8→Ngọ(6), 9→Sửu(1), 10→Thân(8), 11→Mão(3), 12→Tuất(10)


def check_thien_cuong(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Cương (天罡) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THIEN_CUONG_CHI[lunar_month - 1]


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
# NOTE: Not found in 《玉匣記》 — may originate from 《象吉通書》or 《鰲頭通書》.
# Source: blogphongthuy.com, movinghouse.vn.
# Cross-ref: multiple Vietnamese almanac sites.  _sme_verified = True (from VN sources)
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
# Thiên Tặc (天賊) — Hung tinh, kỵ thụ tạo / nhập trạch / động thổ / khai thương khố
# By lunar month → forbidden day Chi (+5 cycle from Thìn).
# Source: 《玉匣記》逐月凶星總局:
#   "天贼忌竖造、入宅、动土、开仓库。正月辰、二月酉、三月寅、四月未、
#    五月子、六月巳、七月戌、八月卯、九月申、十月丑、十一月午、十二月亥。"
# Cross-ref: lichngaytot.com, xemvm.com.  _sme_verified = True
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
# Source: 《玉匣記》逐月凶星總局:
#   "天狱：正月子、二月卯、三月午、四月酉、(repeats quarterly)"
#   "天火忌盖屋、起造、修方。正月子、二月卯、三月午、四月酉、(same)"
# NOTE: Both stars share identical month→chi mapping (子卯午酉 Tứ Chính cycle).
#       They differ only in kỵ: 天火 especially kỵ construction/roofing.
# Cross-ref: 《玉匣記》.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

THIEN_NGUC_CHI: list[int] = [0, 3, 6, 9, 0, 3, 6, 9, 0, 3, 6, 9]
# Quarterly cycle: 1,5,9→Tý(0), 2,6,10→Mão(3), 3,7,11→Ngọ(6), 4,8,12→Dậu(9)

THIEN_HOA_CHI: list[int] = [0, 3, 6, 9, 0, 3, 6, 9, 0, 3, 6, 9]
# Same as Thiên Ngục — both follow 子卯午酉 (Tứ Chính) cycle per 《玉匣記》


def check_thien_nguc_thien_hoa(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Ngục or Thiên Hỏa for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return (
        day_chi_idx == THIEN_NGUC_CHI[lunar_month - 1]
        or day_chi_idx == THIEN_HOA_CHI[lunar_month - 1]
    )


# ─────────────────────────────────────────────────────────────────────────────
# Thiên Xá (天赦日) — Cát tinh mạnh cho tế tự/giải hạn, KỴ động thổ/nhập trạch
# Seasonal: Spring→Mậu Dần, Summer→Giáp Ngọ, Autumn→Mậu Thân, Winter→Giáp Tý
# Source: 《玉匣記》, Ngọc Hạp Thông Thư.
# Cross-ref: lichngaytot.com, xemvm.com.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

THIEN_XA_RULES: list[tuple[int, int]] = [
    (4, 2),   # Spring (months 1-3): Mậu Dần
    (4, 2),
    (4, 2),
    (0, 6),   # Summer (months 4-6): Giáp Ngọ
    (0, 6),
    (0, 6),
    (4, 8),   # Autumn (months 7-9): Mậu Thân
    (4, 8),
    (4, 8),
    (0, 0),   # Winter (months 10-12): Giáp Tý
    (0, 0),
    (0, 0),
]


def check_thien_xa(lunar_month: int, day_can_idx: int, day_chi_idx: int) -> bool:
    """Check if day is Thiên Xá (天赦日) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    expected_can, expected_chi = THIEN_XA_RULES[lunar_month - 1]
    return day_can_idx == expected_can and day_chi_idx == expected_chi


# ─────────────────────────────────────────────────────────────────────────────
# Lục Hợp (六合) — Cát tinh, ngày hợp với tuổi
# Day Chi harmonizes with Year Chi.
# Source: docs/algorithm.md §6.
# ─────────────────────────────────────────────────────────────────────────────

LUC_HOP_MAP: dict[int, int] = {
    0: 1, 1: 0, 2: 11, 11: 2, 3: 10, 10: 3,
    4: 9, 9: 4, 5: 8, 8: 5, 6: 7, 7: 6,
}


def check_luc_hop(day_chi_idx: int, year_chi_idx: int) -> bool:
    """Check if day Chi is Lục Hợp with year Chi."""
    return LUC_HOP_MAP.get(year_chi_idx) == day_chi_idx


# ─────────────────────────────────────────────────────────────────────────────
# Tam Hợp (三合) — Cát tinh, ngày tam hợp với tuổi
# Year Chi → set of day Chi forming Tam Hợp cục.
# Source: traditional lịch vạn niên.
# ─────────────────────────────────────────────────────────────────────────────

TAM_HOP_SETS: dict[int, frozenset[int]] = {
    # Dần(2)/Ngọ(6)/Tuất(10) → Hỏa cục
    2: frozenset({6, 10}), 6: frozenset({2, 10}), 10: frozenset({2, 6}),
    # Thân(8)/Tý(0)/Thìn(4) → Thủy cục
    8: frozenset({0, 4}), 0: frozenset({8, 4}), 4: frozenset({8, 0}),
    # Tỵ(5)/Dậu(9)/Sửu(1) → Kim cục
    5: frozenset({9, 1}), 9: frozenset({5, 1}), 1: frozenset({5, 9}),
    # Hợi(11)/Mão(3)/Mùi(7) → Mộc cục
    11: frozenset({3, 7}), 3: frozenset({11, 7}), 7: frozenset({11, 3}),
}


def check_tam_hop(day_chi_idx: int, year_chi_idx: int) -> bool:
    """Check if day Chi forms Tam Hợp with year Chi."""
    s = TAM_HOP_SETS.get(year_chi_idx)
    return s is not None and day_chi_idx in s


# ─────────────────────────────────────────────────────────────────────────────
# Tiểu Hao (小耗) — Hung tinh, hao tốn nhỏ
# Rule: "Chánh nguyệt khởi Mùi, thuận hành"
# Formula: (lunar_month + 6) % 12
# Source: Ngọc Hạp Thông Thư.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────


def check_tieu_hao(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Tiểu Hao for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (lunar_month + 6) % 12


# ─────────────────────────────────────────────────────────────────────────────
# Sinh Khí (生氣) — Cát tinh, tốt cho xây dựng, trồng cây
# Rule: "Chánh nguyệt khởi Tý, thuận hành"
# Formula: (lunar_month - 1) % 12
# Source: Ngọc Hạp Thông Thư.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────


def check_sinh_khi(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Sinh Khí for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (lunar_month - 1) % 12


# ─────────────────────────────────────────────────────────────────────────────
# Thiên Hỷ (天喜) — Cát tinh, đặc biệt tốt cho hôn nhân
# Rule: "Chánh nguyệt khởi Tuất, nghịch hành"
# Formula: (11 - lunar_month) % 12
# Source: Ngọc Hạp Thông Thư.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────


def check_thien_hy(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Hỷ for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (11 - lunar_month) % 12


# ─────────────────────────────────────────────────────────────────────────────
# Vãng Vong (往亡) — Hung tinh, kỵ xuất hành
# Cycle: M1,2→Dậu(9), M3,4→Sửu(1), M5,6→Tỵ(5), repeats quarterly
# Source: Ngọc Hạp Thông Thư.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

VANG_VONG_CHI: list[int] = [9, 9, 1, 1, 5, 5, 9, 9, 1, 1, 5, 5]


def check_vang_vong(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Vãng Vong for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == VANG_VONG_CHI[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Cửu Không (九空) — Hung tinh, bách sự bất thành
# Rule: "Chánh nguyệt khởi Dậu, nghịch hành tứ quý"
# M1,5,9→Dậu(9), M2,6,10→Thân(8), M3,7,11→Mùi(7), M4,8,12→Ngọ(6)
# Source: Ngọc Hạp Thông Thư.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

CUU_KHONG_CHI: list[int] = [9, 8, 7, 6, 9, 8, 7, 6, 9, 8, 7, 6]


def check_cuu_khong(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Cửu Không for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == CUU_KHONG_CHI[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Địa Tặc (地賊) — Hung tinh, paired with Thiên Tặc
# Rule: "Nghịch hành từ Thìn" — reversed cycle
# Formula: (4 - (lunar_month - 1)) % 12  (reversed from thienTac offset)
# Source: 《玉匣記》.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

DIA_TAC_CHI: list[int] = [3, 10, 5, 0, 7, 2, 9, 4, 11, 6, 1, 8]


def check_dia_tac(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Địa Tặc for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == DIA_TAC_CHI[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Nguyệt Hỏa (月火) — Hung tinh, kỵ bếp/hỏa
# Rule: "Chánh nguyệt khởi Ngọ, nghịch hành"
# Formula: (7 - lunar_month) % 12
# Source: Ngọc Hạp Thông Thư.  _sme_verified = False
# ─────────────────────────────────────────────────────────────────────────────

NGUYET_HOA_CHI: list[int] = [6, 5, 4, 3, 2, 1, 0, 11, 10, 9, 8, 7]


def check_nguyet_hoa(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Nguyệt Hỏa for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == NGUYET_HOA_CHI[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Lục Bất Thành (六不成) — Hung tinh, sự việc không thành
# Rule: "Chánh nguyệt khởi Tỵ, thuận hành"
# Formula: (lunar_month + 4) % 12
# Source: Ngọc Hạp Thông Thư.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────


def check_luc_bat_thanh(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Lục Bất Thành for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (lunar_month + 4) % 12


# ─────────────────────────────────────────────────────────────────────────────
# Thổ Ôn (土瘟) — Hung tinh, kỵ mọi việc liên quan đến đất
# By lunar month → forbidden day Chi.
# Source: Ngọc Hạp Thông Thư.  _sme_verified = True
# ─────────────────────────────────────────────────────────────────────────────

THO_ON_CHI: list[int] = [7, 1, 9, 3, 11, 5, 7, 1, 9, 3, 11, 5]
# M1,7→Mùi(7), M2,8→Sửu(1), M3,9→Dậu(9), M4,10→Mão(3), M5,11→Hợi(11), M6,12→Tỵ(5)


def check_tho_on(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thổ Ôn for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THO_ON_CHI[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# Thổ Phủ (土府) — Hung tinh, kỵ xây dựng/đào đất
# Rule: "Chánh nguyệt khởi Tỵ, nghịch hành tứ quý"
# M1,5,9→Tỵ(5), M2,6,10→Mùi(7), M3,7,11→Dậu(9), M4,8,12→Hợi(11)
# Source: Ngọc Hạp Thông Thư.  _sme_verified = False (needs cross-ref)
# ─────────────────────────────────────────────────────────────────────────────

THO_PHU_CHI: list[int] = [5, 7, 9, 11, 5, 7, 9, 11, 5, 7, 9, 11]


def check_tho_phu(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thổ Phủ for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THO_PHU_CHI[lunar_month - 1]


# ═════════════════════════════════════════════════════════════════════════════
# BATCH 2 — Remaining 39 sao detectors (previously stubs)
# Sources: 《玉匣記》逐月吉凶星總局, 《協紀辨方書》, Ngọc Hạp Thông Thư,
#          Vietnamese lịch vạn niên compilations.
# ═════════════════════════════════════════════════════════════════════════════


# ─────────────────────────────────────────────────────────────────────────────
# CÁT TINH (Auspicious Stars)
# ─────────────────────────────────────────────────────────────────────────────

# Nguyệt Ân (月恩) — Monthly grace, day CAN matches monthly pattern
# Rule (verse): "正月逢丙是月恩，二月见丁三庚真，四月己上五月戊，
#                六辛七壬八癸成，九月庚上十月乙，冬月甲上腊月辛。"
# Derivation: 月建地支所生之天干 (month branch generates day stem via Five Elements)
# Source: 《協紀辨方書》, cnlunar888/lunar.py line 697.  _sme_verified = True
NGUYET_AN_CAN: list[int] = [2, 3, 6, 5, 4, 7, 8, 9, 6, 1, 0, 7]


def check_nguyet_an(lunar_month: int, day_can_idx: int) -> bool:
    """Check if day has Nguyệt Ân (月恩) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_can_idx == NGUYET_AN_CAN[lunar_month - 1]


# Thiên Thành (天成) — Heavenly success
# Rule: odd branches +2 cycle: 卯巳未酉亥丑 (repeats every 6 months)
# M1→未(7), M2→酉(9), M3→亥(11), M4→丑(1), M5→卯(3), M6→巳(5)...
# Source: 《協紀辨方書》, cnlunar888/lunar.py line 708.  _sme_verified = True
THIEN_THANH_CHI: list[int] = [7, 9, 11, 1, 3, 5, 7, 9, 11, 1, 3, 5]


def check_thien_thanh(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Thành (天成) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THIEN_THANH_CHI[lunar_month - 1]


# Thiên Phú (天富) — Heavenly wealth
# Rule: sequential branches from Thìn in month 1, +1/month
# M1→辰(4), M2→巳(5), M3→午(6)... Formula: (lunar_month + 3) % 12
# Auspicious for: 安葬 (burial), 修仓库 (repair granary)
# Source: 《協紀辨方書》, cnlunar888/lunar.py line 694.  _sme_verified = True


def check_thien_phu(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Phú (天富) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (lunar_month + 3) % 12


# Thiên Tài (天財) — Heavenly fortune
# Rule: quarterly Tứ Mộ cycle: M1,5,9→Mão(3), M2,6,10→Ngọ(6),
#       M3,7,11→Dậu(9), M4,8,12→Tý(0)
# Source: 《玉匣記》逐月吉星總局.  _sme_verified = True
THIEN_TAI_CHI: list[int] = [3, 6, 9, 0, 3, 6, 9, 0, 3, 6, 9, 0]


def check_thien_tai(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Tài (天財) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THIEN_TAI_CHI[lunar_month - 1]


# Địa Tài (地財) — Earth fortune (paired with Thiên Tài, 六沖 offset)
# Rule: M1,5,9→Dậu(9), M2,6,10→Tý(0), M3,7,11→Mão(3), M4,8,12→Ngọ(6)
# Source: 《玉匣記》.  _sme_verified = False
DIA_TAI_CHI: list[int] = [9, 0, 3, 6, 9, 0, 3, 6, 9, 0, 3, 6]


def check_dia_tai(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Địa Tài (地財) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == DIA_TAI_CHI[lunar_month - 1]


# Nguyệt Tài (月財) — Monthly fortune
# Rule: "Chánh nguyệt khởi Thìn, thuận hành"
# Formula: (lunar_month + 3) % 12
# Source: Ngọc Hạp Thông Thư.  _sme_verified = False


def check_nguyet_tai(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Nguyệt Tài (月財) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (lunar_month + 3) % 12


# Lộc Khố (祿庫) — Fortune treasury
# Rule: year CAN → day Chi where 祿's 墓庫 resides.
# 甲乙(0,1)→未(7), 丙丁戊己(2-5)→戌(10), 庚辛(6,7)→丑(1), 壬癸(8,9)→辰(4)
# Source: Tam Mệnh Thông Hội 祿庫 table.  _sme_verified = True
LOC_KHO_MAP: dict[int, int] = {
    0: 7, 1: 7, 2: 10, 3: 10, 4: 10, 5: 10, 6: 1, 7: 1, 8: 4, 9: 4,
}


def check_loc_kho(day_chi_idx: int, year_can_idx: int) -> bool:
    """Check if day is Lộc Khố based on year's Heavenly Stem."""
    target = LOC_KHO_MAP.get(year_can_idx)
    return target is not None and day_chi_idx == target


# Thiên Quý (天貴) — Heavenly noble
# Rule: quarterly: M1,5,9→Sửu(1), M2,6,10→Dần(2),
#       M3,7,11→Mão(3), M4,8,12→Thìn(4)
# Source: 《協紀辨方書》.  _sme_verified = False
THIEN_QUY_CHI: list[int] = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4]


def check_thien_quy(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Quý (天貴) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THIEN_QUY_CHI[lunar_month - 1]


# Cát Khánh (吉慶) — Auspicious celebration
# Rule: "Chánh nguyệt khởi Sửu, thuận hành"
# Formula: lunar_month % 12 (M1→1, M2→2, ...)
# Source: Ngọc Hạp Thông Thư.  _sme_verified = False


def check_cat_khanh(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Cát Khánh (吉慶) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == lunar_month % 12


# Ích Hậu (益後) — Benefit later
# Rule: quarterly: M1,5,9→Mùi(7), M2,6,10→Thân(8),
#       M3,7,11→Dậu(9), M4,8,12→Tuất(10)
# Source: 《玉匣記》逐月吉星.  _sme_verified = False
ICH_HAU_CHI: list[int] = [7, 8, 9, 10, 7, 8, 9, 10, 7, 8, 9, 10]


def check_ich_hau(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Ích Hậu (益後) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == ICH_HAU_CHI[lunar_month - 1]


# Tục Thế (續世) — Continue world, good for descendants
# Rule: "Chánh nguyệt khởi Mão, thuận hành"
# Formula: (lunar_month + 2) % 12
# Source: Ngọc Hạp Thông Thư.  _sme_verified = False


def check_tuc_the(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Tục Thế (續世) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (lunar_month + 2) % 12


# Yếu Yên (要安) — Required peace
# Rule: "Chánh nguyệt khởi Dậu, thuận hành tứ quý"
# M1,5,9→Dậu(9), M2,6,10→Tuất(10), M3,7,11→Hợi(11), M4,8,12→Tý(0)
# Source: Ngọc Hạp Thông Thư.  _sme_verified = False
YEU_YEN_CHI: list[int] = [9, 10, 11, 0, 9, 10, 11, 0, 9, 10, 11, 0]


def check_yeu_yen(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Yếu Yên (要安) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == YEU_YEN_CHI[lunar_month - 1]


# Phổ Hộ (普護) — Universal protection
# Rule: "Chánh nguyệt khởi Hợi, thuận hành"
# Formula: (lunar_month + 10) % 12
# Source: 《玉匣記》逐月吉星.  _sme_verified = False


def check_pho_ho(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Phổ Hộ (普護) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (lunar_month + 10) % 12


# Thiên Mã (天馬) — Heavenly horse (monthly, different from year-based Dịch Mã)
# Rule: quarterly Tứ Mã: M1,5,9→Ngọ(6), M2,6,10→Thân(8),
#       M3,7,11→Tuất(10), M4,8,12→Tý(0)
# Source: 《協紀辨方書》月將天馬.  _sme_verified = True
THIEN_MA_CHI: list[int] = [6, 8, 10, 0, 6, 8, 10, 0, 6, 8, 10, 0]


def check_thien_ma(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Mã (天馬) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THIEN_MA_CHI[lunar_month - 1]


# Mậu Thương (戊倉) — Mậu storehouse day
# Rule: any day with Thiên Can = 戊(4) is a storehouse day
# NOTE: Not found in cnlunar888/《協紀辨方書》. Using traditional "戊日為倉" rule.
# Source: Vietnamese almanac tradition.  _sme_verified = False


def check_mau_thuong(day_can_idx: int) -> bool:
    """Check if day is Mậu Thương (戊倉) — day's Heavenly Stem is 戊."""
    return day_can_idx == 4


# Phúc Hậu (福厚) — Thick fortune
# Rule: by SEASON (四季): Spring→Dần(2), Summer→Tỵ(5), Autumn→Thân(8), Winter→Hợi(11)
# 3 months share the same value per season.
# Source: 《協紀辨方書》, cnlunar888/lunar.py line 715.  _sme_verified = True
PHUC_HAU_CHI: list[int] = [2, 2, 2, 5, 5, 5, 8, 8, 8, 11, 11, 11]


def check_phuc_hau(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Phúc Hậu (福厚) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == PHUC_HAU_CHI[lunar_month - 1]


# Thánh Tâm (聖心) — Sacred heart, good for 祭祀/祈福
# Rule: M1→亥(11), M2→巳(5), M3→子(0), M4→午(6), M5→丑(1), M6→未(7),
#       M7→寅(2), M8→申(8), M9→卯(3), M10→酉(9), M11→辰(4), M12→戌(10)
# Source: 《協紀辨方書》, cnlunar888/lunar.py line 725.  _sme_verified = True
THANH_TAM_CHI: list[int] = [11, 5, 0, 6, 1, 7, 2, 8, 3, 9, 4, 10]


def check_thanh_tam(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thánh Tâm (聖心) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THANH_TAM_CHI[lunar_month - 1]


# Thiên Quan (天官) — Heavenly official
# Rule: "Chánh nguyệt khởi Ngọ, thuận hành"
# Formula: (lunar_month + 5) % 12
# Source: Ngọc Hạp Thông Thư.  _sme_verified = False


def check_thien_quan(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Quan (天官) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (lunar_month + 5) % 12


# Minh Tinh (明星) — Bright star, good for 赴任/诉讼/安葬
# Rule: even branches +2 cycle: M1→申(8), M2→戌(10), M3→子(0), M4→寅(2),
#       M5→辰(4), M6→午(6), repeats every 6 months.
# NOTE: cnlunar888 source has '甲' at months 1,7 — likely data error for '申'.
#       Using 申(8) based on the +2 stepping pattern.
# Source: 《協紀辨方書》, cnlunar888/lunar.py line 724.  _sme_verified = True
MINH_TINH_CHI: list[int] = [8, 10, 0, 2, 4, 6, 8, 10, 0, 2, 4, 6]


def check_minh_tinh(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Minh Tinh (明星) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == MINH_TINH_CHI[lunar_month - 1]


# Kính Tâm (敬安) — Respectful peace
# Rule: M1→未(7), M2→丑(1), M3→申(8), M4→寅(2), M5→酉(9), M6→卯(3),
#       M7→戌(10), M8→辰(4), M9→亥(11), M10→巳(5), M11→子(0), M12→午(6)
# 恭顺之神当值 (spirit of respectful obedience)
# Source: 《協紀辨方書》, cnlunar888/lunar.py line 741.  _sme_verified = True
KINH_TAM_CHI: list[int] = [7, 1, 8, 2, 9, 3, 10, 4, 11, 5, 0, 6]


def check_kinh_tam(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Kính Tâm (敬心) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == KINH_TAM_CHI[lunar_month - 1]


# Phúc Sinh (福生) — Fortune birth, good for 祭祀/祈福
# Rule: M1→酉(9), M2→卯(3), M3→戌(10), M4→辰(4), M5→亥(11), M6→巳(5),
#       M7→子(0), M8→午(6), M9→丑(1), M10→未(7), M11→寅(2), M12→申(8)
# Source: 《協紀辨方書》, cnlunar888/lunar.py line 714.  _sme_verified = True
PHUC_SINH_CHI: list[int] = [9, 3, 10, 4, 11, 5, 0, 6, 1, 7, 2, 8]


def check_phuc_sinh(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Phúc Sinh (福生) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == PHUC_SINH_CHI[lunar_month - 1]


# Nguyệt Không (月空) — Monthly void, day CAN check
# Rule: quarterly 壬庚丙甲 cycle:
# M1,5,9→Nhâm(8), M2,6,10→Canh(6), M3,7,11→Bính(2), M4,8,12→Giáp(0)
# Auspicious for: 上表章 (submitting petitions)
# Source: 《協紀辨方書》, cnlunar888/lunar.py line 722.  _sme_verified = True
NGUYET_KHONG_CAN: list[int] = [8, 6, 2, 0, 8, 6, 2, 0, 8, 6, 2, 0]


def check_nguyet_khong(lunar_month: int, day_can_idx: int) -> bool:
    """Check if day has Nguyệt Không (月空) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_can_idx == NGUYET_KHONG_CAN[lunar_month - 1]


# ─────────────────────────────────────────────────────────────────────────────
# HUNG TINH (Inauspicious Stars)
# ─────────────────────────────────────────────────────────────────────────────

# Nhân Cách (人隔) — Human separation, bad for weddings/meetings
# Rule: descending by -2, cycling through odd branches in reverse:
# M1→酉(9), M2→未(7), M3→巳(5), M4→卯(3), M5→丑(1), M6→亥(11),
# M7→酉(9), M8→未(7), M9→巳(5), M10→卯(3), M11→丑(1), M12→亥(11)
# Inauspicious for: 嫁娶 (marriage), 进人 (receiving people)
# Source: 《玉匣記》逐月凶星, cnlunar888/lunar.py line 802.  _sme_verified = True
NHAN_CACH_CHI: list[int] = [9, 7, 5, 3, 1, 11, 9, 7, 5, 3, 1, 11]


def check_nhan_cach(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Nhân Cách (人隔) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == NHAN_CACH_CHI[lunar_month - 1]


# Phi Ma Sát (披麻/飛麻殺) — Flying hemp kill
# Rule: quarterly 子酉午卯 cycle (descending by -3):
# M1,5,9→子(0), M2,6,10→酉(9), M3,7,11→午(6), M4,8,12→卯(3)
# Inauspicious for: 嫁娶 (marriage), 入宅 (moving in)
# Source: 《玉匣記》逐月凶星, cnlunar888/lunar.py line 811.  _sme_verified = True
PHI_MA_SAT_CHI: list[int] = [0, 9, 6, 3, 0, 9, 6, 3, 0, 9, 6, 3]


def check_phi_ma_sat(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Phi Ma Sát (飛麻殺) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == PHI_MA_SAT_CHI[lunar_month - 1]


# Nguyệt Yếm Đại Họa (月厌大禍) — Monthly eclipse great disaster
# Rule: 大禍: "Chánh nguyệt khởi Ngọ, nghịch hành"
# Formula: (7 - lunar_month) % 12
# Source: 《玉匣記》逐月凶星.  _sme_verified = True
# Formula: (11 - month + 12) % 12, i.e. reverse from Tuất
# M1→Tuất(10), M2→Dậu(9), M3→Thân(8), M4→Mùi(7), M5→Ngọ(6), M6→Tỵ(5),
# M7→Thìn(4), M8→Mão(3), M9→Dần(2), M10→Sửu(1), M11→Tý(0), M12→Hợi(11)
NGUYET_YEM_DAI_HOA_CHI: list[int] = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 11]


def check_nguyet_yem_dai_hoa(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Nguyệt Yếm Đại Họa (月厌大禍) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == NGUYET_YEM_DAI_HOA_CHI[lunar_month - 1]


# Thổ Cấm (土禁) — Earth prohibition
# Rule: seasonal (3-month blocks), NOT monthly rotation
# Spring (M1-3)→Hợi(11), Summer (M4-6)→Dần(2), Autumn (M7-9)→Tỵ(5), Winter (M10-12)→Thân(8)
# Source: 《協紀辨方書》土禁.  _sme_verified = True
THO_CAM_CHI: list[int] = [11, 11, 11, 2, 2, 2, 5, 5, 5, 8, 8, 8]


def check_tho_cam(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thổ Cấm (土禁) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THO_CAM_CHI[lunar_month - 1]


# Cửu Thổ Quỷ (九土鬼) — Nine earth ghosts
# Rule: NOT a monthly rotation. Instead, 9 fixed sexagenary days are always Cửu Thổ Quỷ:
# Ất Dậu(1,9), Quý Tỵ(9,5), Giáp Ngọ(0,6), Tân Sửu(7,1), Nhâm Dần(8,2),
# Kỷ Dậu(5,9), Canh Tuất(6,10), Đinh Tỵ(3,5), Mậu Ngọ(4,6)
# Source: 《玉匣記》九土鬼.  _sme_verified = True
CUU_THO_QUY_DAYS: list[tuple[int, int]] = [
    (1, 9), (9, 5), (0, 6), (7, 1), (8, 2),
    (5, 9), (6, 10), (3, 5), (4, 6),
]


def check_cuu_tho_quy(lunar_month: int, day_can_idx: int, day_chi_idx: int = -1) -> bool:
    """Check if day has Cửu Thổ Quỷ (九土鬼).

    Unlike most hung tinh, this is based on the sexagenary day (can-chi pair),
    not the lunar month. The lunar_month parameter is accepted for interface
    compatibility but not used.

    Args:
        lunar_month: Lunar month (unused, kept for interface compatibility).
        day_can_idx: Day heavenly stem index (0-9).
        day_chi_idx: Day earthly branch index (0-11).
    """
    if day_chi_idx == -1:
        # Legacy call: day_can_idx is actually day_chi_idx (old interface)
        # Cannot determine sexagenary day with only chi, return False
        return False
    return (day_can_idx, day_chi_idx) in CUU_THO_QUY_DAYS


# Thiên Địa Chuyển Sát (天地轉殺) — Heaven earth turning kill
# Rule: seasonal (3-month blocks)
# Spring (M1-3)→Mão(3), Summer (M4-6)→Ngọ(6), Autumn (M7-9)→Dậu(9), Winter (M10-12)→Tý(0)
# Source: 《協紀辨方書》天地轉殺.  _sme_verified = True
THIEN_DIA_CHUYEN_SAT_CHI: list[int] = [3, 3, 3, 6, 6, 6, 9, 9, 9, 0, 0, 0]


def check_thien_dia_chuyen_sat(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thiên Địa Chuyển Sát for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THIEN_DIA_CHUYEN_SAT_CHI[lunar_month - 1]


# Nguyệt Kiến Chuyển Sát (月建轉殺) — Monthly foundation turning kill
# Rule: day Chi = 月破 (opposite of 月建)
# 月建: M1→Dần(2), M2→Mão(3)... → (month+1)%12
# 月破 = 月建 + 6: M1→Thân(8), M2→Dậu(9)...
# Formula: (lunar_month + 7) % 12
# Source: 《協紀辨方書》月破.  _sme_verified = True


def check_nguyet_kien_chuyen_sat(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Nguyệt Kiến Chuyển Sát (月破) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (lunar_month + 7) % 12


# Hà Khôi Câu Giảo (河魁勾絞) — River chief hook
# Rule: partner of Thiên Cương (天罡), +6 offset (六沖)
# Source: 《玉匣記》 "河魁与天罡对冲".  _sme_verified = True
HA_KHOI_CAU_GIAO_CHI: list[int] = [11, 6, 1, 8, 3, 10, 5, 0, 7, 2, 9, 4]


def check_ha_khoi_cau_giao(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Hà Khôi Câu Giảo for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == HA_KHOI_CAU_GIAO_CHI[lunar_month - 1]


# Hỏa Tai (火災) — Fire disaster
# Rule: M1→Sửu(1), M2→Mùi(7), M3→Dần(2), M4→Thân(8), M5→Mão(3), M6→Dậu(9),
#       M7→Thìn(4), M8→Tuất(10), M9→Tỵ(5), M10→Hợi(11), M11→Tý(0), M12→Ngọ(6)
# Source: 《玉匣記》火災.  _sme_verified = True
HOA_TAI_CHI: list[int] = [1, 7, 2, 8, 3, 9, 4, 10, 5, 11, 0, 6]


def check_hoa_tai(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Hỏa Tai (火災) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == HOA_TAI_CHI[lunar_month - 1]


# Trùng Tang (重喪) — Double mourning, bad for funerals
# Rule: month → forbidden day CAN PAIR (each month has TWO forbidden stems)
# M1→Giáp/Canh(0,6), M2→Ất/Tân(1,7), M3→Mậu/Kỷ(4,5), M4→Bính/Nhâm(2,8),
# M5→Đinh/Quý(3,9), M6→Mậu/Kỷ(4,5), M7→Canh/Giáp(6,0), M8→Tân/Ất(7,1),
# M9→Mậu/Kỷ(4,5), M10→Nhâm/Bính(8,2), M11→Quý/Đinh(9,3), M12→Mậu/Kỷ(4,5)
# Source: 《協紀辨方書》重喪日.  _sme_verified = True
TRUNG_TANG_CAN_PAIRS: list[tuple[int, int]] = [
    (0, 6), (1, 7), (4, 5), (2, 8), (3, 9), (4, 5),
    (6, 0), (7, 1), (4, 5), (8, 2), (9, 3), (4, 5),
]


def check_trung_tang(lunar_month: int, day_can_idx: int) -> bool:
    """Check if day has Trùng Tang (重喪) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    pair = TRUNG_TANG_CAN_PAIRS[lunar_month - 1]
    return day_can_idx in pair


# Quỷ Cốc (鬼哭) — Ghost cry
# Rule: alternating Sửu/Mùi: odd months→Sửu(1), even months→Mùi(7)
# Source: 《玉匣記》逐月凶星.  _sme_verified = False


def check_quy_coc(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Quỷ Cốc (鬼哭) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (1 if lunar_month % 2 == 1 else 7)


# Thần Cách (神隔) — Spirit separation (paired with Nhân Cách, +6 offset)
# Rule: trimonthly cycle: M1,4,7,10→Mùi(7), M2,5,8,11→Thân(8), M3,6,9,12→Ngọ(6)
# Source: 《玉匣記》逐月凶星.  _sme_verified = False
THAN_CACH_CHI: list[int] = [7, 8, 6, 7, 8, 6, 7, 8, 6, 7, 8, 6]


def check_than_cach(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Thần Cách (神隔) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == THAN_CACH_CHI[lunar_month - 1]


# Hoàng Sa (黃沙) — Yellow sand
# Rule: "reverse by 2 from Ngọ": M1→Ngọ(6), M2→Thìn(4), M3→Dần(2),
#       M4→Tý(0), M5→Tuất(10), M6→Thân(8), M7→Ngọ(6)... repeats 6-month
# Formula: (8 - 2 * lunar_month) % 12
# Source: 《玉匣記》逐月凶星.  _sme_verified = False
# NOTE: 皇沙 (linhthong.com) has cycle [6,2,0] x4 but may be a DIFFERENT star
#       from 黃沙 (different Hán tự). Keeping original until confirmed.
HOANG_SA_CHI: list[int] = [6, 4, 2, 0, 10, 8, 6, 4, 2, 0, 10, 8]


def check_hoang_sa(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Hoàng Sa (黃沙) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == HOANG_SA_CHI[lunar_month - 1]


# Ngũ Quỷ (五鬼) — Five ghosts
# Rule: M1→Ngọ(6), M2→Dần(2), M3→Thìn(4), M4→Dậu(9), M5→Mão(3), M6→Thân(8),
#       M7→Sửu(1), M8→Tỵ(5), M9→Tý(0), M10→Hợi(11), M11→Mùi(7), M12→Tuất(10)
# Source: 《玉匣記》五鬼.  _sme_verified = True
NGU_QUY_CHI: list[int] = [6, 2, 4, 9, 3, 8, 1, 5, 0, 11, 7, 10]


def check_ngu_quy(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Ngũ Quỷ (五鬼) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == NGU_QUY_CHI[lunar_month - 1]


# Nguyệt Hỏa Độc Hỏa (月火獨火) — Monthly fire / lone fire
# Rule: "Chánh nguyệt khởi Dậu, thuận hành" (distinct from 月火 which is reverse)
# Formula: (lunar_month + 8) % 12
# Source: Ngọc Hạp Thông Thư.  _sme_verified = False
# NOTE: If formula matches thoCam, that's OK — different intents reference them.


def check_nguyet_hoa_doc_hoa(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Nguyệt Hỏa Độc Hỏa for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == (lunar_month + 8) % 12


# Lôi Công (雷公) — Thunder lord
# Rule: 4-cycle repeating: [Dần(2), Hợi(11), Tỵ(5), Thân(8)]
# M1→Dần(2), M2→Hợi(11), M3→Tỵ(5), M4→Thân(8), M5→Dần(2), M6→Hợi(11), ...
# Source: 《玉匣記》雷公.  _sme_verified = True
LOI_CONG_CHI: list[int] = [2, 11, 5, 8, 2, 11, 5, 8, 2, 11, 5, 8]


def check_loi_cong(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Lôi Công (雷公) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == LOI_CONG_CHI[lunar_month - 1]


# Địa Phá (地破) — Earth break
# Rule: distinct from 月破. Formula: (month + 10) % 12
# M1→Hợi(11), M2→Tý(0), M3→Sửu(1), M4→Dần(2), ...
# Source: 《協紀辨方書》地破.  _sme_verified = True
DIA_PHA_CHI: list[int] = [11, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def check_dia_pha(lunar_month: int, day_chi_idx: int) -> bool:
    """Check if day has Địa Phá (地破) for the given lunar month."""
    if lunar_month < 1 or lunar_month > 12:
        return False
    return day_chi_idx == DIA_PHA_CHI[lunar_month - 1]
