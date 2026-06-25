"""Golden fixture: tuvivietnam.vn chart 19/06/2026 09:57 nam."""

from __future__ import annotations

import pytest

from engine.chart_bundle import build_full_chart
from engine.pillars import get_tu_tru


@pytest.fixture
def golden_chart():
    tu_tru = get_tu_tru("2026-06-19", 10)
    return build_full_chart(
        tu_tru, "2026-06-19", 1, 10, 57, name="NGUYỄN VĂN T",
    )


def test_golden_tu_tru_display(golden_chart):
    assert golden_chart["tu_tru_display"] == "Bính Ngọ | Giáp Ngọ | Giáp Tý | Kỷ Tỵ"


def test_golden_khoi_van(golden_chart):
    dv = golden_chart["dai_van"]
    assert dv["start_age"] == 7
    assert dv["khoi_van_date"] == "2032-06-13"
    assert dv["cycles"][0]["display"] == "Ất Mùi"
    assert dv["cycles"][0]["age_label"] == "7-16t"
    assert dv["cycles"][0]["start_year"] == 2032


def test_golden_dai_van_year_sequence(golden_chart):
    # Cycles advance by 10 years each (not 20).
    years = [c["start_year"] for c in golden_chart["dai_van"]["cycles"]]
    assert years == [2032, 2042, 2052, 2062, 2072, 2082, 2092, 2102, 2112, 2122]


def test_golden_solar_display(golden_chart):
    assert golden_chart["header"]["duong_lich_display"] == "19/6/2026 - 9:57 (GMT+7)"


def test_golden_hour_tang_can_display_order(golden_chart):
    # Tỵ shown in Uyên Hải Tử Bình order: Bính, Mậu, Canh (not Bính, Canh, Mậu).
    hour = golden_chart["pillars"]["hour"]
    assert [t["can_name"] for t in hour["tang_can"]] == ["Bính", "Mậu", "Canh"]
    assert [p["short_label"] for p in hour["pho_tinh"]] == ["Thực", "T.Tài", "Sát"]


def test_golden_menh_thai_tuan(golden_chart):
    assert golden_chart["menh_cung"]["display"] == "Giáp Ngọ"
    assert golden_chart["thai_nguyen"]["display"] == "Ất Dậu"
    assert golden_chart["tuan_khong"]["nien_khong"]["display"] == "Dần - Mão"
    assert golden_chart["tuan_khong"]["nhat_khong"]["display"] == "Tuất - Hợi"


def test_golden_truong_sinh(golden_chart):
    p = golden_chart["pillars"]
    assert p["year"]["truong_sinh"]["label_vi"] == "Tử"
    assert p["month"]["truong_sinh"]["label_vi"] == "Tử"
    assert p["day"]["truong_sinh"]["label_vi"] == "Mộc Dục"
    assert p["hour"]["truong_sinh"]["label_vi"] == "Bệnh"


def test_golden_than_sat(golden_chart):
    p = golden_chart["pillars"]
    assert [s["name"] for s in p["year"]["than_sat"]] == [
        "Văn Xương", "Tướng Tinh", "Hồng Diễm",
    ]
    assert [s["name"] for s in p["day"]["than_sat"]] == [
        "Tướng Tinh", "Tai Sát",
    ]
    assert [s["name"] for s in p["hour"]["than_sat"]] == [
        "Văn Xương", "Kiếp Sát", "Vong Thần",
    ]


def test_thien_loc_and_view_year_1990():
    # tuvivietnam chart 21/3/1990 05:15 nam: day master Ất → Thiên Lộc on Mão.
    tu_tru = get_tu_tru("1990-03-21", 6)
    chart = build_full_chart(tu_tru, "1990-03-21", 1, 6, 15, view_year=2026)
    p = chart["pillars"]
    assert [s["name"] for s in p["month"]["than_sat"]] == [
        "Thiên Lộc", "Đào Hoa", "Thiên Hỷ",
    ]
    assert [s["name"] for s in p["hour"]["than_sat"]] == [
        "Thiên Lộc", "Đào Hoa", "Thiên Hỷ",
    ]
    assert [s["name"] for s in p["day"]["than_sat"]] == [
        "Tướng Tinh", "Hồng Loan",
    ]
    assert [s["name"] for s in p["year"]["than_sat"]] == [
        "Văn Xương", "Tướng Tinh", "Đào Hoa", "Hồng Loan",
    ]
    # view_year drives the lưu niên strip and marks the selected year.
    luu = chart["luu_nien"]
    assert luu[0]["year"] == 2026
    assert luu[0]["display"] == "Bính Ngọ"
    assert luu[0]["selected"] is True
    assert sum(1 for r in luu if r.get("selected")) == 1
    # Time-aware tiết khí: Xuân Phân moment (~04:19) precedes birth 05:15.
    assert chart["header"]["tiet_khi"]["name"] == "Xuân Phân"
    assert chart["header"]["nguyet_lenh"] == "Mão"
    # Exact 起运 day matches tuvivietnam (5/4/1995), start age 6.
    assert chart["dai_van"]["khoi_van_date"] == "1995-04-05"
    assert chart["dai_van"]["start_age"] == 6
    assert chart["dai_van"]["cycles"][0]["start_year"] == 1995


def test_golden_pho_tinh(golden_chart):
    labels = [
        x["short_label"]
        for x in golden_chart["pillars"]["year"]["pho_tinh"]
    ]
    assert labels == ["Thương", "Tài"]


def test_golden_header(golden_chart):
    h = golden_chart["header"]
    assert h["tiet_khi"]["name"] == "Mang Chủng"
    assert h["am_lich"]["display"] == "5/5/2026"
    assert h["nguyet_lenh"] == "Ngọ"
