"""Unit tests for stem 合化 and god group integration."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from engine.cuong_nhuoc import analyze_chart_strength
from engine.hoa_hop import detect_stem_transformations, month_supports_transform
from engine.pillars import get_tu_tru
from engine.thap_than import analyze_thap_than


class TestHoaHop:
  def test_canh_at_hoa_kim_when_month_dau(self):
      """07/10/2020 — Canh năm + Ất tháng Dậu → hóa Kim (月令 Kim)."""
      tu_tru = get_tu_tru("2020-10-07", 10)
      transforms = detect_stem_transformations(tu_tru)
      assert len(transforms) == 1
      assert transforms[0]["transform_element"] == "Kim"
      assert transforms[0]["can_a_name"] == "Canh"
      assert transforms[0]["can_b_name"] == "Ất"

  def test_canh_at_fails_when_month_ty(self):
      """Ất Tỵ tháng — Hỏa không support Kim化."""
      tu_tru = get_tu_tru("1992-06-03", 18)
      assert tu_tru["month"]["chi_name"] == "Tỵ"
      transforms = detect_stem_transformations(tu_tru)
      assert transforms == []

  def test_month_supports_kim_on_dau(self):
      assert month_supports_transform(9, "Kim") is True

  def test_month_rejects_kim_on_ty(self):
      assert month_supports_transform(5, "Kim") is False


class TestGodGroupsAfterHoaHop:
  def test_wrong_chart_thuc_thuong_not_dominant_after_failed_hoa(self):
      """03/06/1992 Canh DM — no hóa; Thực Thương group may exist from raw Ất month."""
      tu_tru = get_tu_tru("1992-06-03", 18)
      th = analyze_thap_than(tu_tru)
      assert "god_groups" in th
      assert "percent" in th["god_groups"]
      assert sum(th["god_groups"]["percent"].values()) == 100.0

  def test_correct_chart_has_stem_transform_and_god_groups(self):
      tu_tru = get_tu_tru("2020-10-07", 10)
      strength = analyze_chart_strength(tu_tru)
      assert strength["stem_transformations"]
      th = analyze_thap_than(tu_tru)
      assert th["god_groups"]["percent"]["thuc_thuong"] >= 0
      assert th["dominant_god_group"]["key"] in th["god_groups"]["percent"]
      assert th["surface_god_counts"] == th["god_counts"]
