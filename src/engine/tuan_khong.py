"""
tuan_khong.py — Tuần không (旬空) per pillar.

Source: docs/algorithm.md §22.7
"""

from __future__ import annotations

from engine.can_chi import CHI_NAMES


# 六甲旬空: first stem-branch of xun -> void branch indices (0-based)
XUN_KHONG: list[tuple[int, int]] = [
    (10, 11),  # Giáp Tý → Tuất, Hợi
    (8, 9),    # Giáp Tuất → Thân, Dậu
    (6, 7),    # Giáp Thân → Ngọ, Mùi
    (4, 5),    # Giáp Ngọ → Thìn, Tỵ
    (2, 3),    # Giáp Thìn → Dần, Mão
    (0, 1),    # Giáp Dần → Tý, Sửu
]


def _cycle_position(can_idx: int, chi_idx: int) -> int:
    return (can_idx * 6 - chi_idx * 5) % 60


def get_tuan_khong(can_idx: int, chi_idx: int) -> dict:
    pos = _cycle_position(can_idx, chi_idx)
    xun_idx = pos // 10
    void_a, void_b = XUN_KHONG[xun_idx]
    names = [CHI_NAMES[void_a], CHI_NAMES[void_b]]
    return {
        "chi_indices": [void_a, void_b],
        "chi_names": names,
        "display": f"{names[0]} - {names[1]}",
    }


def analyze_tuan_khong(tu_tru: dict) -> dict:
    year = tu_tru["year"]
    day = tu_tru["day"]
    return {
        "nien_khong": get_tuan_khong(year["can_idx"], year["chi_idx"]),
        "nhat_khong": get_tuan_khong(day["can_idx"], day["chi_idx"]),
    }
