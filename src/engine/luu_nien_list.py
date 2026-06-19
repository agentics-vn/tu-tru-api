"""
luu_nien_list.py — Annual pillar list for lá số grid.

Source: docs/algorithm.md §22.4
"""

from __future__ import annotations

from datetime import date as dt_date

from engine.bazi_solar import bazi_cycle_year
from engine.can_chi import CAN_NAMES, CHI_NAMES, get_can_chi_year


def build_luu_nien_list(
    birth_date: str,
    num_years: int = 10,
    start_year: int | None = None,
) -> list[dict]:
    """
    List annual pillars from birth year (or start_year) for num_years entries.
    """
    parts = birth_date.split("-")
    birth_y = int(parts[0])
    birth_m = int(parts[1])
    birth_d = int(parts[2])
    birth_dt = dt_date(birth_y, birth_m, birth_d)

    if start_year is None:
        start_year = birth_y

    rows: list[dict] = []
    for i in range(num_years):
        year = start_year + i
        cc = get_can_chi_year(bazi_cycle_year(year, birth_m, birth_d))
        age = year - birth_y + 1  # tuổi mụ
        rows.append({
            "year": year,
            "age": age,
            "can_idx": cc["can_idx"],
            "chi_idx": cc["chi_idx"],
            "can_name": cc["can_name"],
            "chi_name": cc["chi_name"],
            "display": f"{cc['can_name']} {cc['chi_name']}",
            "age_label": f"{age}t",
        })
    return rows
