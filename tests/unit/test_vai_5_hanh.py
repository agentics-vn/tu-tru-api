"""Unit tests cho phân vai trọn 5 hành (BT285 Rule 0 Bước 4).

Bất biến quan trọng nhất: KHÔNG hành nào được thiếu vai. Một hành lửng lơ khiến
mỗi mục luận giải tự diễn giải lại và sinh mâu thuẫn giữa các mục.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from engine.dung_than import (  # noqa: E402
    KHAC_BY,
    KHAC_TARGET,
    NGU_HANH,
    SINH_BY,
    SINH_TARGET,
    assign_vai_5_hanh,
    find_dung_than,
)
from engine.pillars import get_tu_tru  # noqa: E402

VAI_HOP_LE = {"Dụng", "Hỉ", "Kỵ", "Cừu"}


def moi_to_hop():
    """Mọi (Nhật Chủ, Dụng thần) có thể xảy ra — Dụng chạy đủ 5 hành."""
    for dm in NGU_HANH:
        for dung in NGU_HANH:
            yield dm, dung


@pytest.mark.parametrize("dm,dung", list(moi_to_hop()))
def test_du_5_hanh_va_dung_moi_vai_hop_le(dm, dung):
    vai = assign_vai_5_hanh(dm, dung)
    assert set(vai) == set(NGU_HANH), f"thiếu hành: {set(NGU_HANH) - set(vai)}"
    assert set(vai.values()) <= VAI_HOP_LE
    assert [h for h, v in vai.items() if v == "Dụng"] == [dung]


@pytest.mark.parametrize("dm", NGU_HANH)
def test_than_vuong_an_la_ky_ty_kiep_la_cuu(dm):
    """Thân vượng: Ấn nuôi thân đã quá vượng = Kỵ, Tỷ Kiếp trợ thân = Cừu."""
    for dung in (SINH_TARGET[dm], KHAC_TARGET[dm], KHAC_BY[dm]):
        vai = assign_vai_5_hanh(dm, dung)
        assert vai[SINH_BY[dm]] == "Kỵ"
        assert vai[dm] == "Cừu"


@pytest.mark.parametrize("dm", NGU_HANH)
def test_quy_uoc_quan_sat(dm):
    """QUY ƯỚC QUAN SÁT — vai Quan Sát suy theo Dụng, không theo 'khắc thân'."""
    thuc_thuong, tai, quan_sat = SINH_TARGET[dm], KHAC_TARGET[dm], KHAC_BY[dm]

    # Dụng = Thực Thương → Thương Quan kiến Quan
    vai = assign_vai_5_hanh(dm, thuc_thuong)
    assert vai[tai] == "Hỉ"
    assert vai[quan_sat] == "Kỵ"

    # Dụng = Tài → Tài sinh Quan, dòng chảy thuận
    vai = assign_vai_5_hanh(dm, tai)
    assert vai[thuc_thuong] == "Hỉ"
    assert vai[quan_sat] == "Hỉ"

    # Dụng = Quan Sát → Thực Thương khắc Dụng, làm gãy dòng chảy
    vai = assign_vai_5_hanh(dm, quan_sat)
    assert vai[tai] == "Hỉ"
    assert vai[thuc_thuong] == "Kỵ"


@pytest.mark.parametrize("dm", NGU_HANH)
def test_than_nhuoc_phu_than_la_dung_hi(dm):
    """Thân nhược: hành phù thân còn lại phải là Hỉ, cả bộ ba kia đều bất lợi."""
    an, ty_kiep = SINH_BY[dm], dm
    for dung, con_lai in ((an, ty_kiep), (ty_kiep, an)):
        vai = assign_vai_5_hanh(dm, dung)
        assert vai[con_lai] == "Hỉ"
        for hanh in (SINH_TARGET[dm], KHAC_TARGET[dm], KHAC_BY[dm]):
            assert vai[hanh] in {"Kỵ", "Cừu"}, f"{hanh} phải bất lợi khi thân nhược"


@pytest.mark.parametrize("dm", NGU_HANH)
def test_than_nhuoc_hanh_khac_dung_va_khac_than_deu_la_ky(dm):
    for dung in (SINH_BY[dm], dm):
        vai = assign_vai_5_hanh(dm, dung)
        assert vai[KHAC_BY[dung]] == "Kỵ"
        assert vai[KHAC_BY[dm]] == "Kỵ"


@pytest.mark.parametrize("dm,dung", list(moi_to_hop()))
def test_cuu_khong_bao_gio_dung_chung_hanh_voi_dung(dm, dung):
    vai = assign_vai_5_hanh(dm, dung)
    assert vai[dung] == "Dụng"


def test_la_so_demo_1984_khop_rule_0_buoc_4():
    """Lá số demo của repo: Mậu Thổ thân nhược, Dụng Hỏa.

    Trước khi có vai_5_hanh, Kim không mang vai nào — đúng cái lỗ mà Rule 0
    Bước 4 gọi là 'hành lửng lơ'.
    """
    ket_qua = find_dung_than(get_tu_tru("1984-03-15", 8))
    assert ket_qua["dung_than"] == "Hỏa"
    assert ket_qua["strength"] == "nhược"
    assert ket_qua["vai_5_hanh"] == {
        "Mộc": "Kỵ",
        "Hỏa": "Dụng",
        "Thổ": "Hỉ",
        "Kim": "Cừu",
        "Thủy": "Kỵ",
    }


def test_moi_la_so_that_deu_duoc_phan_vai_du_5_hanh():
    """Quét lá số thật nhiều ngày/giờ — không ca nào để lọt hành nào."""
    ngay = ["1984-03-15", "1990-05-15", "1976-11-02", "2001-07-23", "1968-01-09"]
    for d in ngay:
        for gio in (0, 4, 8, 11, 16, 20):
            ket_qua = find_dung_than(get_tu_tru(d, gio))
            vai = ket_qua["vai_5_hanh"]
            assert set(vai) == set(NGU_HANH), f"{d} giờ {gio} thiếu hành"
            assert vai[ket_qua["dung_than"]] == "Dụng", f"{d} giờ {gio}"
