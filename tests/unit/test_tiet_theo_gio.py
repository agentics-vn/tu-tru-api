"""
Trụ năm / trụ tháng đổi đúng THỜI KHẮC giao tiết (节), không đổi theo ngày.

Khiếu nại thật (Huyền Cơ Thuận Mệnh, 27/11/2026): sinh 21–23h ngày 4/2/1986.
Lập Xuân 1986 ≈ 09:56 (UTC+7) cùng ngày, nên trụ năm là Bính Dần, tháng Canh
Dần. Engine cũ đọc kinh độ mặt trời lúc 0h nên trả Ất Sửu · Kỷ Sửu. Đo bằng
lịch thiên văn: 23/23 tiết của 1986 và 1995 đều đổi muộn một ngày.

Mốc giờ của mỗi khung là đầu khung (BIRTH_SLOT_HOUR), cùng quy ước với
compute_khoi_van — khung chứa đúng thời khắc giao tiết vẫn mập mờ ±1 khung
(vd Hàn Lộ 1986: mô hình lich_hnd cho 21:02, lịch thiên văn 20:55).
"""

from __future__ import annotations

import math
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from engine.bazi_solar import bazi_cycle_year
from engine.can_chi import get_menh_nap_am_from_date
from engine.dai_van import compute_khoi_van, get_dai_van_direction
from engine.pillars import get_tu_tru


def _nam_thang(d, slot):
    t = get_tu_tru(d, slot)["display"].split(" | ")
    return t[0], t[1]


class TestLapXuanTheoGio:
    def test_khieu_nai_4_2_1986_gio_hoi(self):
        assert get_tu_tru("1986-02-04", 22)["display"] == "Bính Dần | Canh Dần | Kỷ Mão | Ất Hợi"

    def test_truoc_thoi_khac_cung_ngay_van_nam_cu(self):
        # giờ Thìn (07h) — trước 09:56
        assert _nam_thang("1986-02-04", 8) == ("Ất Sửu", "Kỷ Sửu")

    @pytest.mark.parametrize("slot,ky_vong", [
        (14, ("Quý Mão", "Ất Sửu")),    # 13h — Lập Xuân 2024 ≈ 15:27 UTC+7
        (18, ("Giáp Thìn", "Bính Dần")),  # 17h — đã qua
    ])
    def test_lap_xuan_2024(self, slot, ky_vong):
        assert _nam_thang("2024-02-04", slot) == ky_vong

    def test_khong_gio_giu_quy_uoc_ngay_cu(self):
        # caller chỉ có ngày (lịch, danh sách lưu niên) — hành vi cũ giữ nguyên
        assert bazi_cycle_year(1986, 2, 4) == 1985
        assert bazi_cycle_year(1986, 2, 4, hour=21) == 1986
        assert bazi_cycle_year(1986, 2, 4, hour=7) == 1985

    def test_menh_nap_am_theo_gio_khop_tru_nam(self):
        # Bính Dần → Lò Trung Hỏa; Ất Sửu → Hải Trung Kim
        assert get_menh_nap_am_from_date(1986, 2, 4, birth_time=22)["name"] == "Lò Trung Hỏa"
        assert "Hải Trung" in get_menh_nap_am_from_date(1986, 2, 4)["name"]


class TestTietDoiThangTheoGio:
    @pytest.mark.parametrize("d,slot,thang", [
        ("1986-03-06", 2, "Canh Dần"),   # Kinh Trập ≈ 04:00 — 01h còn tháng Dần
        ("1986-03-06", 6, "Tân Mão"),    # 05h đã sang tháng Mão
        ("1995-01-06", 4, "Đinh Sửu"),   # Tiểu Hàn ≈ 02:30 — 03h đã sang tháng Sửu
        ("1986-12-07", 14, "Kỷ Hợi"),    # Đại Tuyết ≈ 16:50 — 13h còn tháng Hợi
        ("1986-12-07", 18, "Canh Tý"),   # 17h đã sang tháng Tý
    ])
    def test_thang_doi_dung_thoi_khac(self, d, slot, thang):
        assert _nam_thang(d, slot)[1] == thang


class TestTuoiKhoiVanKhopNgayKhoiVan:
    """start_age phải khớp khoi_van_date (vốn đã tính theo thời khắc). Bản cũ
    dò ngày giao tiết từ ngày sinh nên người sinh ngay sau một tiết bị lệch
    ~10 tuổi (vd 5/2/1955 giờ Dậu: khởi vận 18/5/1955 mà start_age = 10)."""

    @pytest.mark.parametrize("d,slot,gioi", [
        ("1955-02-05", 18, 1), ("1984-04-05", 11, -1), ("1987-03-07", 10, 1),
        ("2007-12-07", 23, -1), ("1957-09-08", 14, -1), ("2002-10-08", 22, 1),
        ("2010-05-06", 6, -1), ("1986-02-04", 22, -1), ("1986-02-04", 22, 1),
    ])
    def test_start_age_khop_ngay_khoi_van(self, d, slot, gioi):
        tt = get_tu_tru(d, slot)
        k = compute_khoi_van(d, get_dai_van_direction(tt["year"]["can_idx"], gioi), slot)
        nam = (date.fromisoformat(k["khoi_van_date"]) - date.fromisoformat(d)).days / 365.2422
        assert abs(k["start_age"] - max(1, math.ceil(nam))) <= 1
