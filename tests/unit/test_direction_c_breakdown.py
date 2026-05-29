"""Unit tests for Direction C 4-factor breakdown."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from calendar_service import get_day_info, get_user_chart
from engine.hoang_dao import get_day_star, get_gio_hoang_dao
from engine.nhi_thap_bat_tu import get_nhi_thap_bat_tu
from engine.day_score import build_direction_c_breakdown
from filter import apply_layer2_filter
from scoring import collect_score_deltas

pytestmark = pytest.mark.direction_c

_INTENT_RULES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "docs", "seed", "intent-rules.json"
)
import json

with open(_INTENT_RULES_PATH, encoding="utf-8") as f:
    INTENT_RULES = json.load(f)


def _score_fixture(birth: str, target: str, intent: str = "MAC_DINH", birth_time=None, gender=None):
    # get_user_chart expects ISO YYYY-MM-DD
    if "/" in birth:
        from api.parse_date import parse_dmy
        birth = parse_dmy(birth).isoformat()
    day_info = get_day_info(target)
    user_chart = get_user_chart(birth, birth_time, gender)
    intent_rule = INTENT_RULES.get(intent, INTENT_RULES["MAC_DINH"])
    l2 = apply_layer2_filter(day_info, user_chart, intent)
    ctx = collect_score_deltas(day_info, user_chart, intent, intent_rule, l2)
    star = get_day_star(day_info["lunar_month"], day_info["day_chi_idx"])
    y, m, d = map(int, target.split("-"))
    sao_28 = get_nhi_thap_bat_tu(y, m, d)
    gio = get_gio_hoang_dao(day_info["day_chi_idx"])
    breakdown = build_direction_c_breakdown(
        day_info=day_info,
        user_chart=user_chart,
        intent=intent,
        presentation_buckets=ctx["presentation_buckets"],
        star_info=star,
        sao_28=sao_28,
        gio_tot=gio,
        personalized=True,
    )
    return ctx, breakdown


class TestDirectionCBreakdown:

    def test_four_items_fixed_order(self):
        _, bd = _score_fixture("15/03/1984", "2026-05-28")
        assert len(bd) == 4
        assert [x["id"] for x in bd] == ["truc", "sao28", "can_chi_laso", "gio_vang"]

    def test_sum_points_equals_score(self):
        ctx, bd = _score_fixture("15/03/1984", "2026-05-28")
        assert sum(x["points"] for x in bd) == ctx["score"]

    def test_no_diem_co_ban_row(self):
        _, bd = _score_fixture("15/03/1984", "2026-05-28")
        for item in bd:
            assert "Điểm cơ bản" not in item.get("source", "")
            assert "ĐIỂM CƠ BẢN" not in item.get("reason_vi", "").upper()

    def test_reason_vi_differs_from_type(self):
        _, bd = _score_fixture("15/03/1984", "2026-05-28")
        for item in bd:
            assert item["reason_vi"] != item["type"]
            assert len(item["reason_vi"]) > len(item["type"])

    def test_reason_vi_vietnamese_no_engine_enums(self):
        _, bd = _score_fixture("15/03/1984", "2026-05-28")
        for item in bd:
            for bad in ("neutral", "bonus", "penalty"):
                assert bad not in item["reason_vi"].lower()

    def test_personalization_mentions_chart(self):
        _, bd = _score_fixture("15/03/1984", "2026-05-28", birth_time=8, gender=1)
        can_chi_reason = next(x for x in bd if x["id"] == "can_chi_laso")["reason_vi"]
        assert any(k in can_chi_reason for k in ("mệnh", "Dụng Thần", "Nhật Chủ", "lá số"))

    def test_gio_vang_not_only_hour_list(self):
        _, bd = _score_fixture("15/03/1984", "2026-05-28")
        gio = next(x for x in bd if x["id"] == "gio_vang")["reason_vi"]
        assert "giờ vàng" in gio.lower() or "hoàng đạo" in gio.lower()

    @pytest.mark.parametrize("target", ["2026-03-10", "2026-06-15"])
    def test_various_dates_sum_invariant(self, target):
        ctx, bd = _score_fixture("01/01/1990", target)
        assert sum(x["points"] for x in bd) == ctx["score"]
