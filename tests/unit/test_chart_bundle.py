"""Chart bundle single-pass + tu-tru parity fields."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from engine.chart_bundle import build_chart_analysis
from engine.chart_contract import merge_chart_contract_into_result
from engine.la_so import build_la_so_chart_contract
from engine.pillars import get_tu_tru


class TestChartBundle:
    def test_single_detect_pass(self):
        tu_tru = get_tu_tru("2020-10-07", 10)
        bundle = build_chart_analysis(tu_tru)
        assert bundle["stem_transformations"]
        assert bundle["strength_info"]["element_counts"]
        assert bundle["thap_than"]["god_groups"]["percent"]

    def test_merge_adds_parity_fields_without_clobbering_dung_than_object(self):
        tu_tru = get_tu_tru("2020-10-07", 10)
        chart = build_la_so_chart_contract(tu_tru, 1, "2020-10-07")
        result = {
            "dung_than": {"element": "Mộc", "description": "test"},
            "thap_than": {"year": {}, "month": {}, "hour": {}, "dominant": {}},
        }
        merge_chart_contract_into_result(result, chart)
        assert result["dung_than"]["element"] == "Mộc"
        assert result["stem_transformations"]
        assert result["god_groups"]
        assert result["surface_god_counts"]
