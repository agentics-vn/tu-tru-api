"""
tang_can.py — Phase 2: Tàng Can (Hidden Stems / 藏干).

Reveals the hidden elemental energies inside each Dia Chi position.

Source of truth: docs/algorithm.md §18
"""

from __future__ import annotations

from engine.can_chi import CAN_NAMES, CAN_HANH

# ─────────────────────────────────────────────────────────────────────────────
# Hidden Stems Table
# Index = Dia Chi index (0-11)
# Value = list of Can indices [Chu Khi, Trung Khi, Du Khi]
# ─────────────────────────────────────────────────────────────────────────────

TANG_CAN: dict[int, list[int]] = {
    0:  [9],        # Tý:   Quý
    1:  [5, 9, 7],  # Sửu:  Kỷ, Quý, Tân
    2:  [0, 2, 4],  # Dần:  Giáp, Bính, Mậu
    3:  [1],        # Mão:  Ất
    4:  [4, 1, 9],  # Thìn: Mậu, Ất, Quý
    5:  [2, 6, 4],  # Tỵ:   Bính, Canh, Mậu
    6:  [3, 5],     # Ngọ:  Đinh, Kỷ
    7:  [5, 3, 1],  # Mùi:  Kỷ, Đinh, Ất
    8:  [6, 8, 4],  # Thân: Canh, Nhâm, Mậu
    9:  [7],        # Dậu:  Tân
    10: [4, 7, 3],  # Tuất: Mậu, Tân, Đinh
    11: [8, 0],     # Hợi:  Nhâm, Giáp
}

# Weights for hidden stems: Chủ Khí > Trung Khí > Dư Khí
# Standard weights used in most BaZi schools:
#   Chủ Khí = 1.0 (60%), Trung Khí = 0.6 (30%), Dư Khí = 0.3 (10%)
TANG_CAN_WEIGHTS: list[float] = [1.0, 0.6, 0.3]

# Role labels
TANG_CAN_ROLES: list[str] = ["chu_khi", "trung_khi", "du_khi"]


def get_tang_can(chi_idx: int) -> list[dict]:
    """
    Return hidden stems for a Dia Chi.

    Args:
        chi_idx: 0-11

    Returns:
        list of dicts: [{can_idx, can_name, hanh, role, weight}]
    """
    stems = TANG_CAN[chi_idx]
    result = []
    for i, can_idx in enumerate(stems):
        result.append({
            "can_idx": can_idx,
            "can_name": CAN_NAMES[can_idx],
            "hanh": CAN_HANH[can_idx],
            "role": TANG_CAN_ROLES[i],
            "weight": TANG_CAN_WEIGHTS[i],
        })
    return result


def get_all_elements(tu_tru: dict) -> dict[str, float]:
    """
    Count weighted element occurrences across all 4 pillars.

    Counts:
    - Thien Can (surface stems): weight 1.0 each
    - Dia Chi hidden stems: weighted by Chu/Trung/Du Khi

    Args:
        tu_tru: dict from get_tu_tru() with year/month/day/hour pillars

    Returns:
        {"Kim": float, "Mộc": float, "Thủy": float, "Hỏa": float, "Thổ": float}
    """
    counts: dict[str, float] = {
        "Kim": 0.0, "Mộc": 0.0, "Thủy": 0.0, "Hỏa": 0.0, "Thổ": 0.0,
    }

    for pillar_key in ("year", "month", "day", "hour"):
        pillar = tu_tru[pillar_key]

        # Thien Can (surface stem) — weight 1.0
        can_hanh = CAN_HANH[pillar["can_idx"]]
        counts[can_hanh] += 1.0

        # Dia Chi hidden stems
        for hidden in get_tang_can(pillar["chi_idx"]):
            counts[hidden["hanh"]] += hidden["weight"]

    return counts


def get_day_master_support(tu_tru: dict, day_master_hanh: str) -> tuple[float, float]:
    """
    Count how much support vs opposition the Day Master has.

    Support = same element + element that generates Day Master (Ấn Tinh)
    Opposition = everything else

    Args:
        tu_tru: from get_tu_tru()
        day_master_hanh: the Day Master's element (e.g. "Hỏa")

    Returns:
        (support_weight, opposition_weight)
    """
    # Ngũ Hành Tương Sinh: parent element that generates the target
    SINH_MAP = {
        "Kim": "Thổ", "Mộc": "Thủy", "Thủy": "Kim",
        "Hỏa": "Mộc", "Thổ": "Hỏa",
    }
    parent = SINH_MAP[day_master_hanh]

    elements = get_all_elements(tu_tru)

    support = elements.get(day_master_hanh, 0.0) + elements.get(parent, 0.0)
    total = sum(elements.values())
    opposition = total - support

    return support, opposition
