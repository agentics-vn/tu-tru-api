"""Canonical giờ Hoàng/Hắc đạo slot shape (Direction C P3-02)."""

from __future__ import annotations

from typing import Any

from engine.hoang_dao import get_gio_hac_dao, get_gio_hoang_dao


def format_gio_slot(g: dict[str, Any]) -> dict[str, Any]:
    """Single slot used across day-detail, ngay-hom-nay, chon-ngay, lich-thang."""
    chi = g["chi_name"]
    start = g["start"]
    end = g["end"]
    return {
        "chi": chi,
        "chi_name": chi,
        "start_hour": start,
        "end_hour": end,
        "label_vi": f"{chi} {start}–{end}",
        "range": f"{start}-{end}",
    }


def format_gio_tot_slots(day_chi_idx: int) -> list[dict[str, Any]]:
    return [format_gio_slot(g) for g in get_gio_hoang_dao(day_chi_idx)]


def format_gio_xau_slots(day_chi_idx: int) -> list[dict[str, Any]]:
    return [format_gio_slot(g) for g in get_gio_hac_dao(day_chi_idx)]
