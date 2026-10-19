"""Đối chiếu Phi Tinh với sách nguồn, KHÔNG với chính engine.

Nguồn: 'Cải vận mệnh khuyết' — Lý Cư Minh. Sách in chín lưới cửu cung (mỗi sao
nhập trung một lưới) và các bảng 'CÁC NĂM MÀ SAO … VÀO CUNG GIỮA'. Mọi con số
dưới đây chép từ sách. Nếu engine đổi mà sách không đổi thì test phải đỏ — đó
là điểm khác biệt với việc test giá trị do chính engine sinh ra.

Quy ước đọc lưới trong sách — Nam ở trên:
    Đông Nam | Nam  | Tây Nam
    Đông     | T.tâm| Tây
    Đông Bắc | Bắc  | Tây Bắc
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from engine.phi_tinh import (  # noqa: E402
    annual_center_star,
    build_phi_tinh_payload,
    fly_nine_palaces,
    load_year_center_overrides,
)

DOC_LUOI = [
    "Đông Nam", "Nam", "Tây Nam",
    "Đông", "Trung Tâm", "Tây",
    "Đông Bắc", "Bắc", "Tây Bắc",
]

# Tám lưới chép trực tiếp từ sách. Lưới của sao 1 (Nhất Bạch) bị lỗi in — ô
# lưới của nó in trùng lưới Lục Bạch — nên suy ra từ quy tắc thuận phi mà tám
# lưới kia đã xác nhận, và được khóa thêm bởi test_ngu_hoang_2026_o_cung_nam.
LUOI_TRONG_SACH: dict[int, list[int]] = {
    1: [9, 5, 7, 8, 1, 3, 4, 6, 2],  # suy ra, không chép từ sách
    2: [1, 6, 8, 9, 2, 4, 5, 7, 3],
    3: [2, 7, 9, 1, 3, 5, 6, 8, 4],
    4: [3, 8, 1, 2, 4, 6, 7, 9, 5],
    5: [4, 9, 2, 3, 5, 7, 8, 1, 6],
    6: [5, 1, 3, 4, 6, 8, 9, 2, 7],
    7: [6, 2, 4, 5, 7, 9, 1, 3, 8],
    8: [7, 3, 5, 6, 8, 1, 2, 4, 9],
    9: [8, 4, 6, 7, 9, 2, 3, 5, 1],
}
LUOI_CHEP_TU_SACH = sorted(set(LUOI_TRONG_SACH) - {1})

# Các bảng 'CÁC NĂM MÀ SAO … VÀO CUNG GIỮA'. Chép đủ, trừ bảng Bát Bạch:
# bảng đó in trùng nguyên văn danh sách của Thất Xích (2002, 2011, 2020…) nên
# là lỗi in. Bát Bạch thật sự rơi vào 2001, 2010, 2019, 2028 — chính văn của
# sách xác nhận gián tiếp: 'năm 2010 phía tây nam là phía hung… hóa Ngũ Hoàng
# của phương này', và Ngũ Hoàng chỉ ở Tây Nam khi nhập trung là 8.
NAM_TRONG_SACH: dict[int, list[int]] = {
    9: [2000, 2009, 2018, 2027, 2036, 2045, 2054, 2063, 2072, 2081],
    7: [2002, 2011, 2020, 2029, 2038, 2047, 2056, 2065, 2074, 2083],
    6: [2003, 2012, 2021, 2030, 2039, 2048, 2057, 2066, 2075, 2084],
    5: [2004, 2013, 2022, 2031, 2040, 2049, 2058, 2067, 2076, 2085],
    4: [1996, 2005, 2014, 2023, 2032, 2041, 2050, 2059, 2068, 2077],
    3: [1997, 2006, 2015, 2024, 2033, 2042, 2051, 2060, 2069, 2078],
    2: [1998, 2007, 2016, 2025, 2034, 2043, 2052, 2061, 2070, 2079],
    # sách in '1017 Đinh Dậu' — Đinh Dậu là 2017, lỗi OCR một chữ số
    1: [1999, 2008, 2017, 2026, 2035, 2044, 2053, 2062, 2071, 2080],
}

MOI_NAM = sorted((nam, sao) for sao, ds in NAM_TRONG_SACH.items() for nam in ds)


@pytest.mark.parametrize("nam,sao", MOI_NAM)
def test_nhap_trung_khop_bang_nam_trong_sach(nam, sao):
    assert annual_center_star(nam) == sao, (
        f"Năm {nam}: sách xếp vào bảng sao {sao}, engine tính {annual_center_star(nam)}"
    )


def test_2026_la_nhat_bach_khong_phai_ngu_hoang():
    """Chốt riêng ca từng bị seed ghi đè sai.

    Sách xếp '2026 Bính Ngọ' vào bảng NHẤT BẠCH. Nhập trung 5 (Ngũ Hoàng) là
    của '2031 Tân Hợi'.
    """
    assert annual_center_star(2026) == 1
    assert annual_center_star(2031) == 5


def test_seed_khong_con_override_vo_can_cu():
    assert load_year_center_overrides() == {}


@pytest.mark.parametrize("center", LUOI_CHEP_TU_SACH)
def test_luoi_cuu_cung_khop_sach(center):
    grid = fly_nine_palaces(center)
    assert [grid[p] for p in DOC_LUOI] == LUOI_TRONG_SACH[center]


@pytest.mark.parametrize("center", LUOI_CHEP_TU_SACH)
def test_bay_nghich_khong_khop_bat_ky_luoi_nao(center):
    """Chốt lý do bỏ nhánh nghịch phi: sai ở mọi lưới, không phải vài ca lẻ."""
    nghich = {"Trung Tâm": center}
    for i, p in enumerate(
        ["Tây Bắc", "Tây", "Đông Bắc", "Nam", "Bắc", "Tây Nam", "Đông", "Đông Nam"],
        start=1,
    ):
        nghich[p] = ((center - 1 - i) % 9) + 1
    assert [nghich[p] for p in DOC_LUOI] != LUOI_TRONG_SACH[center]


@pytest.mark.parametrize("nam", [2024, 2025, 2026, 2027, 2031])
def test_payload_that_khop_luoi_sach(nam):
    """Đi qua build_phi_tinh_payload — bắt cả lỗi ở tầng lắp ráp response."""
    payload = build_phi_tinh_payload(nam)
    got = {row["direction"]: row["star"] for row in payload["phi_tinh"]}
    assert [got[p] for p in DOC_LUOI] == LUOI_TRONG_SACH[annual_center_star(nam)]


def test_nam_can_am_van_bay_thuan():
    """2025 là năm can âm. Engine cũ bay nghịch, lệch sách ở cả tám cung ngoài."""
    got = {r["direction"]: r["star"] for r in build_phi_tinh_payload(2025)["phi_tinh"]}
    assert [got[p] for p in DOC_LUOI] == LUOI_TRONG_SACH[2]


@pytest.mark.parametrize(
    "nam,cung_ngu_hoang",
    [
        (2010, "Tây Nam"),  # 'năm 2010 phía tây nam là phía hung'
        (2011, "Đông"),     # 'năm 2011, Ngũ Hoàng nhập phía chính đông'
        (2012, "Đông Nam"), # 'năm 2012 ở phía đông nam'
    ],
)
def test_vi_tri_ngu_hoang_khop_chinh_van_cua_sach(nam, cung_ngu_hoang):
    """Ba mốc sách nói thẳng vị trí Ngũ Hoàng — kiểm chéo độc lập với bảng năm."""
    payload = build_phi_tinh_payload(nam)
    vi_tri = {row["star"]: row["direction"] for row in payload["phi_tinh"]}
    assert vi_tri[5] == cung_ngu_hoang


def test_ngu_hoang_2026_o_cung_nam():
    """Hệ quả trực tiếp cho mục 257/258 của BT285."""
    vi_tri = {r["star"]: r["direction"] for r in build_phi_tinh_payload(2026)["phi_tinh"]}
    assert vi_tri[5] == "Nam"
    assert vi_tri[1] == "Trung Tâm"
