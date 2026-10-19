"""Golden v1 của `find_dung_than`, đầu ra của `main` 88b7a66.

Dùng làm nền cho `test_mac_dinh_v1_khong_doi` khi cài luật `2026-10.1`: lời gọi
mặc định phải trả y hệt. "Từng byte" là từng byte của dạng chính tắc
``v1.chuoi()`` (``sort_keys``). Sinh bằng ``tests/golden/v1.py --ghi``.

Ba lớp canh:
- ``cases``: 60 lá số (24 hồ sơ của golden HTTP + 36 ngày 1931–2026, đủ 13 khung giờ);
- ``theo_nhanh``: 63 lá số, 3 lá số cho MỖI nhánh trong 21 nhánh của bản cài thử
  ``2026-10.1`` (gồm mọi ``DB-*``, ``CB-DH-*``, ``CB-TQ``) — chỗ luật mới rẽ riêng, nơi
  một lỗi rò "chạy luật mới dù gọi v1" sẽ lộ ra;
- vân tay toàn mẫu tổng hợp đặc tả mục 11 (6.786 lá số), bắt cả thay đổi chỉ chạm
  một lá số không có trong hai danh sách trên.
"""

from __future__ import annotations

import json
from collections import Counter

import pytest

from engine.dung_than import find_dung_than
from engine.pillars import get_tu_tru
from tests.golden import v1

# Ghim: sinh lại bằng `--ghi` thì phải sửa hai dòng này, có dấu vết trong diff.
SHA_GOLDEN_DUNG = "ee1026c2bf801014f881800f0a58360b1d4f8ce88488f174623967cef3cab351"
VAN_TAY_MAU = {"n": 6786, "sha256": "6f15a1ca726a345ec0c4300be12521c2ba5586ce12a9f8d65c9b90fbd70f8c95"}

DATA = json.loads(v1.FILE_DUNG.read_text(encoding="utf-8"))
CASES = DATA["cases"]
THEO_NHANH = DATA["theo_nhanh"]
NHANH_21 = {
    "CB-DH-HAN", "CB-DH-NHIET", "CB-N-QS", "CB-N-TAI", "CB-N-TT", "CB-TQ", "CB-V-AN",
    "CB-V-TK-QS", "DB-HOA", "DB-NHAT-HANH", "DB-TONG-CUONG", "DB-TONG-NHI", "DB-TONG-SAT",
    "DB-TONG-TAI", "DB-TONG-VUONG", "N-QS", "N-TAI", "N-TT", "V-AN", "V-TK-QS", "V-TK-TT",
}


def test_golden_file_pinned():
    assert v1.sha_tep(v1.FILE_DUNG) == SHA_GOLDEN_DUNG


def test_golden_dung_than_contract():
    assert len(CASES) == 60
    assert [(c["id"], c["birth_date"], c["birth_time"]) for c in CASES] == v1.tao_la_so_dung()
    # Phủ cả ba nhãn cường nhược và ca dụng trùng kỵ của v1 (giữ nguyên, không sửa ở đây).
    assert set(Counter(c["ket_qua"]["strength"] for c in CASES)) == {"nhược", "cân bằng", "vượng"}
    assert sum(c["ket_qua"]["dung_than"] == c["ket_qua"]["ky_than"] for c in CASES) == 5


def test_golden_theo_nhanh_contract():
    # Độ phủ không được tự tụt: đủ 21 nhánh, mỗi nhánh ≥ 2 (đang là 3).
    assert len(THEO_NHANH) == 63
    assert [(c["birth_date"], c["birth_time"], c["nhanh_ban_cai_thu"]) for c in THEO_NHANH] \
        == list(v1.LA_SO_THEO_NHANH)
    dem = Counter(c["nhanh_ban_cai_thu"] for c in THEO_NHANH)
    assert set(dem) == NHANH_21
    assert min(dem.values()) >= 2
    assert DATA["dem_theo_nhanh"] == dict(dem)
    assert DATA["dem_nhanh_mau_tong_hop"] == v1.DEM_NHANH_MAU
    assert set(v1.DEM_NHANH_MAU) == NHANH_21 and sum(v1.DEM_NHANH_MAU.values()) == 6786
    # Golden chỉ lưu đầu ra v1: không khoá nào của luật mới.
    assert all(set(c["ket_qua"]) == {"dung_than", "hi_than", "ky_than", "cuu_than", "strength", "analysis"}
               for c in CASES + THEO_NHANH)


ALL = CASES + THEO_NHANH


@pytest.mark.parametrize("case", ALL, ids=[c["id"] for c in ALL])
def test_golden_tu_tru_input(case):
    tt = get_tu_tru(case["birth_date"], case["birth_time"])
    assert v1.chuoi(json.loads(json.dumps(tt))) == v1.chuoi(case["tu_tru"])


@pytest.mark.parametrize("case", ALL, ids=[c["id"] for c in ALL])
def test_golden_find_dung_than_v1(case):
    tt = get_tu_tru(case["birth_date"], case["birth_time"])
    out = json.loads(json.dumps(find_dung_than(tt)))
    assert v1.chuoi(out) == v1.chuoi(case["ket_qua"])


def test_van_tay_mau_tong_hop():
    assert DATA["van_tay_mau"] == VAN_TAY_MAU
    assert v1.van_tay_mau() == VAN_TAY_MAU
