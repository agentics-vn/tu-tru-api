"""Merge P2 chart contract fields into API response dicts."""

from __future__ import annotations

from typing import Any


# Fields safe to copy from build_la_so_chart_contract without clobbering
# tu-tru-specific shapes (dung_than object, pillars can_chi, dai_van block).
CHART_PARITY_TOP_LEVEL_KEYS: tuple[str, ...] = (
    "cuong_nhuoc",
    "chart_strength",
    "element_counts",
    "ngu_hanh",
    "stem_transformations",
    "cuong_nhuoc_detail",
    "god_groups",
    "surface_god_counts",
    "_raw",
    "dai_van_list",
)


def merge_chart_contract_into_result(
    result: dict[str, Any],
    chart: dict[str, Any],
) -> None:
    """Copy shared GET /la-so chart fields onto POST /tu-tru (parity)."""
    for key in CHART_PARITY_TOP_LEVEL_KEYS:
        if key in chart:
            result[key] = chart[key]
