"""Unit tests for engine.la_so structured reading."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from engine.la_so import NHAT_CHU_ARCHETYPE, build_la_so, _build_tinh_duyen
from engine.pillars import get_tu_tru
from engine.thap_than import analyze_thap_than


def test_nhat_chu_archetype_covers_all_cans():
    assert set(NHAT_CHU_ARCHETYPE.keys()) == set(range(10))


def test_build_la_so_core_keys():
    tu_tru = get_tu_tru("1990-05-15", 8)
    out = build_la_so(tu_tru, None, "1990-05-15")
    assert "tinh_cach" in out
    assert "su_nghiep" in out
    assert "tai_van" in out
    assert "suc_khoe" in out
    assert "_raw" in out
    assert out["tinh_cach"]["archetype"]
    assert out["su_nghiep"]["dominant_thap_than"]
    assert "tinh_duyen" not in out
    assert "dai_van_current" not in out


def test_build_la_so_with_gender_adds_tinh_duyen_and_dai_van():
    tu_tru = get_tu_tru("1990-05-15", 8)
    out = build_la_so(tu_tru, 1, "1990-05-15")
    assert "tinh_duyen" in out
    assert out["tinh_duyen"]["spouse_star"] == "Chính Tài (vợ)"
    assert "dai_van_current" in out
    assert "display" in out["dai_van_current"]


def test_build_la_so_female_spouse_label():
    tu_tru = get_tu_tru("1990-05-15", 8)
    out = build_la_so(tu_tru, -1, "1990-05-15")
    assert out["tinh_duyen"]["spouse_star"] == "Chính Quan (chồng)"


def test_tinh_duyen_signals():
    tu_tru = get_tu_tru("1990-05-15", 8)
    thap = analyze_thap_than(tu_tru)
    td = _build_tinh_duyen(1, thap, "nhược")
    assert "signals" in td
    assert td["signals"]["weak_dm_needs_support"] is True
