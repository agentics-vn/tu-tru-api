"""Unit tests for engine.phong_thuy contextual feng shui."""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from engine.phong_thuy import (
    DEFAULT_PURPOSE,
    PhongThuySeedError,
    build_couple_harmony,
    build_personalization,
    build_purpose_payload,
)


def test_default_purpose_nha_o_vat_pham():
    vat, extras = build_purpose_payload(DEFAULT_PURPOSE, "Mộc")
    assert isinstance(vat, list)
    assert len(vat) >= 1
    assert all("item" in x for x in vat)


def test_purpose_van_phong_has_huong_ngoi_for_moc():
    vat, extras = build_purpose_payload("VAN_PHONG", "Mộc")
    assert "huong_ngoi" in extras
    assert "tot" in extras["huong_ngoi"]


def test_purpose_cua_hang_has_quay():
    _, extras = build_purpose_payload("CUA_HANG", "Mộc")
    assert "quay_thu_ngan" in extras


def test_personalization_none_without_tu_tru():
    assert build_personalization(None, "Mộc") is None


def test_couple_moc_khac_tho():
    ch = build_couple_harmony(
        "Mộc",
        "Thổ",
        person1_menh_name="Đại Lâm Mộc",
        person2_menh_name="Lộ Bàng Thổ",
    )
    assert ch is not None
    assert ch["remedy_element"] == "Hỏa"
    assert "khắc" in ch["relation"]
    assert ch["person1_hanh"] == "Mộc"
    assert ch["person2_hanh"] == "Thổ"
    assert ch["person1_menh_name"] == "Đại Lâm Mộc"
    assert ch["person2_menh_name"] == "Lộ Bàng Thổ"
    assert len(ch.get("remedies", [])) >= 1


def test_couple_same_hanh_returns_none():
    assert build_couple_harmony("Kim", "Kim") is None


def test_couple_sinh_not_direct_ke():
    """Hai hành tương sinh — không có khắc trực tiếp → None."""
    assert build_couple_harmony("Mộc", "Hỏa") is None


def test_load_purposes_missing_file_raises_phong_thuy_seed_error(
    monkeypatch, tmp_path,
):
    import engine.phong_thuy as pt

    pt._load_purposes.cache_clear()
    monkeypatch.setattr(pt, "_seed_root", lambda: tmp_path)
    with pytest.raises(PhongThuySeedError) as exc:
        pt._load_purposes()
    assert "phong-thuy-purposes" in exc.value.message_vi


def test_load_purposes_invalid_json_raises(monkeypatch, tmp_path):
    import engine.phong_thuy as pt

    pt._load_purposes.cache_clear()
    (tmp_path / "phong-thuy-purposes.json").write_text("not json", encoding="utf-8")
    monkeypatch.setattr(pt, "_seed_root", lambda: tmp_path)
    with pytest.raises(PhongThuySeedError) as exc:
        pt._load_purposes()
    assert "phong-thuy-purposes" in exc.value.message_vi


def test_load_couple_remedies_missing_file_raises(monkeypatch, tmp_path):
    import engine.phong_thuy as pt

    pt._load_couple_remedies.cache_clear()
    monkeypatch.setattr(pt, "_seed_root", lambda: tmp_path)
    with pytest.raises(PhongThuySeedError) as exc:
        pt._load_couple_remedies()
    assert "couple-remedies" in exc.value.message_vi
