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
    load_star_meta,
)


def test_fly_nine_palaces_center_5_forward_matches_luo_shu():
    g = fly_nine_palaces(5)
    assert g["Trung Tâm"] == 5
    assert g["Đông Nam"] == 4
    assert g["Nam"] == 9
    assert g["Tây Nam"] == 2
    assert g["Đông"] == 3
    assert g["Tây"] == 7
    assert g["Đông Bắc"] == 8
    assert g["Bắc"] == 1
    assert g["Tây Bắc"] == 6


def test_annual_center_star_override_co_hieu_luc():
    """Cơ chế override vẫn dùng được — chỉ seed là không còn ghi đè năm nào.

    Giá trị dưới đây là số bịa để thử cơ chế, KHÔNG phải mệnh lý. Nhập trung
    thật của 2026 là 1; xem test_phi_tinh_doi_chieu_sach.py.
    """
    ovr = {"2026": 4}
    assert annual_center_star(2026, overrides=ovr) == 4
    # 2025 không nằm trong override → công thức neo 2024 = 3
    assert annual_center_star(2025, overrides=ovr) == 2


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
