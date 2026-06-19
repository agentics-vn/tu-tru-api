"""
truong_sinh.py — Thập nhị trường sinh (12 life stages) per pillar branch.

Source: docs/algorithm.md §22.2, docs/seed/truong-sinh.json
"""

from __future__ import annotations

from engine.can_chi import CHI_NAMES
from engine.seed_loader import load_seed_json


def _load_data() -> dict:
    return load_seed_json("truong-sinh.json")


def get_truong_sinh_stage(day_master_can: int, chi_idx: int) -> dict:
    """
    Life stage for a branch relative to Day Master stem.

    Returns: { key, label_vi }
    """
    data = _load_data()
    stages: list[str] = data["stages"]
    labels: dict[str, str] = data["stage_labels_vi"]
    start_map = {int(k): v for k, v in data["chang_sheng_start_chi"].items()}
    yang_stems: set[int] = set(data["yang_stems"])

    start_chi = start_map[day_master_can]
    if day_master_can in yang_stems:
        offset = (chi_idx - start_chi + 12) % 12
    else:
        offset = (start_chi - chi_idx + 12) % 12

    key = stages[offset]
    return {"key": key, "label_vi": labels[key]}


def analyze_truong_sinh(tu_tru: dict) -> dict[str, dict]:
    """12 stages for all four pillar branches."""
    dm_can = tu_tru["day"]["can_idx"]
    result: dict[str, dict] = {}
    for pillar_key in ("year", "month", "day", "hour"):
        chi_idx = tu_tru[pillar_key]["chi_idx"]
        stage = get_truong_sinh_stage(dm_can, chi_idx)
        result[pillar_key] = {
            **stage,
            "chi_name": CHI_NAMES[chi_idx],
        }
    return result
