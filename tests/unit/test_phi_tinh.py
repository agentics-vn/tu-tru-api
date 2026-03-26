"""Unit tests for engine.phi_tinh."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from engine.phi_tinh import (
    PhiTinhSeedError,
    annual_center_star,
    build_phi_tinh_payload,
    fly_nine_palaces,
    is_yang_year_stem,
    load_star_meta,
)


def test_fly_nine_palaces_center_5_forward_matches_luo_shu():
    g = fly_nine_palaces(5, forward=True)
    assert g["Trung Tâm"] == 5
    assert g["Đông Nam"] == 4
    assert g["Nam"] == 9
    assert g["Tây Nam"] == 2
    assert g["Đông"] == 3
    assert g["Tây"] == 7
    assert g["Đông Bắc"] == 8
    assert g["Bắc"] == 1
    assert g["Tây Bắc"] == 6


def test_annual_center_star_2026_override():
    ovr = {"2026": 5}
    assert annual_center_star(2026, overrides=ovr) == 5
    # 2025 không nằm trong override → công thức neo 2024 = 3
    assert annual_center_star(2025, overrides=ovr) == 2


def test_is_yang_year_stem_2026():
    assert is_yang_year_stem(2026) is True


def test_build_phi_tinh_payload_structure():
    p = build_phi_tinh_payload(2024)
    assert p["phi_tinh_year"] == 2024
    assert len(p["phi_tinh"]) == 9
    assert "huong_tot_nam_nay" in p
    assert "huong_xau_nam_nay" in p
    assert "hoa_giai" in p
    dirs = [x["direction"] for x in p["phi_tinh"]]
    assert dirs[0] == "Đông Nam"
    assert "Trung Tâm" in dirs


def test_load_star_meta_raises_when_incomplete(monkeypatch):
    import engine.phi_tinh as pt

    cached = pt._load_star_meta_cached
    cached.cache_clear()
    monkeypatch.setattr(pt, "_load_star_meta_cached", lambda: {"1": {}})
    with pytest.raises(PhiTinhSeedError):
        load_star_meta()
    cached.cache_clear()
