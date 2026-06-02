"""
luu_nhat_hours.py — Aggregate giờ hoàng đạo labels from calendar month rows.
"""

from __future__ import annotations

from collections import Counter

from api.gio_slots import format_gio_tot_slots


def aggregate_top_hours(scored_days: list[dict], *, limit: int = 5) -> list[str]:
    """Top recurring giờ tốt labels across days with day_chi_idx."""
    counter: Counter[str] = Counter()
    for row in scored_days:
        if not row.get("is_layer1_pass", True):
            continue
        if row.get("grade") not in ("A", "B"):
            continue
        chi_idx = row.get("day_chi_idx")
        if chi_idx is None:
            dinfo = row.get("day_info") or {}
            chi_idx = dinfo.get("day_chi_idx")
        if chi_idx is None:
            continue
        for slot in format_gio_tot_slots(chi_idx):
            label = slot.get("label_vi") or slot.get("label") or str(slot)
            counter[label] += 1
    return [label for label, _ in counter.most_common(limit)]
