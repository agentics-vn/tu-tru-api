"""
tests/unit/test_dung_than_vai.py — Bất biến bốn vai của Dụng Thần (docs/algorithm.md §21.6).

Dụng, Hỷ, Kỵ, Cừu phải là bốn hành khác nhau. Trước §21.6 có ba ca trùng:
vượng chọn Quan làm Dụng (Cừu = Dụng), cân bằng có Kỵ = Tài (Cừu = Dụng),
cân bằng có Thực nhiều nhất (Kỵ = Dụng, Cừu = Hỷ).
"""

from __future__ import annotations

import os
import random
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from engine.dung_than import KHAC_BY, KHAC_TARGET, SINH_BY, SINH_TARGET, find_dung_than
from engine.pillars import get_tu_tru

HANH = ["Kim", "Mộc", "Thủy", "Hỏa", "Thổ"]
SLOTS = [0, 2, 4, 6, 8, 10, 11, 14, 16, 18, 20, 22, 23]


def _analysis(strength: str, dm: str, counts: dict) -> dict:
    return {"strength": strength, "day_master_hanh": dm, "element_counts": counts}


def _vai(r: dict) -> tuple:
    return r["dung_than"], r["hi_than"], r["ky_than"], r["cuu_than"]


def _counts(dm: str, **theo_vai) -> dict:
    """Dựng element_counts theo vai so với DM: ty, an, thuc, tai, quan."""
    hanh = {
        "ty": dm, "an": SINH_BY[dm], "thuc": SINH_TARGET[dm],
        "tai": KHAC_TARGET[dm], "quan": KHAC_BY[dm],
    }
    base = {h: 1.0 for h in HANH}
    for vai, v in theo_vai.items():
        base[hanh[vai]] = v
    return base


@pytest.mark.parametrize("dm", HANH)
class TestBonVaiTungNhanh:
    def test_nhuoc_khong_doi(self, dm):
        r = find_dung_than({}, _analysis("nhược", dm, _counts(dm)))
        assert _vai(r) == (SINH_BY[dm], dm, KHAC_BY[dm], KHAC_TARGET[dm])

    def test_vuong_dung_thuc_khong_doi(self, dm):
        r = find_dung_than({}, _analysis("vượng", dm, _counts(dm, thuc=0.5, quan=2.0)))
        assert _vai(r) == (SINH_TARGET[dm], KHAC_TARGET[dm], SINH_BY[dm], KHAC_BY[dm])

    def test_vuong_dung_quan_cuu_thanh_ty(self, dm):
        # Trước §21.6: Cừu = hành sinh Ấn = Quan = trùng Dụng.
        r = find_dung_than({}, _analysis("vượng", dm, _counts(dm, thuc=2.0, quan=0.5)))
        assert _vai(r) == (KHAC_BY[dm], KHAC_TARGET[dm], SINH_BY[dm], dm)

    def test_can_bang_ky_tai_cuu_thanh_quan(self, dm):
        # Trước §21.6: Cừu = hành sinh Tài = Thực = trùng Dụng.
        r = find_dung_than({}, _analysis("cân bằng", dm, _counts(dm, tai=3.0)))
        assert _vai(r) == (SINH_TARGET[dm], dm, KHAC_TARGET[dm], KHAC_BY[dm])

    def test_can_bang_thuc_nhieu_nhat_ky_khong_la_dung(self, dm):
        # Trước §21.6: Kỵ = Thực = Dụng, Cừu = Tỷ = Hỷ.
        r = find_dung_than({}, _analysis("cân bằng", dm, _counts(dm, thuc=3.0, an=2.0)))
        assert _vai(r) == (SINH_TARGET[dm], dm, SINH_BY[dm], KHAC_BY[dm])

    def test_can_bang_ky_an_va_quan_khong_doi(self, dm):
        r1 = find_dung_than({}, _analysis("cân bằng", dm, _counts(dm, an=3.0)))
        assert _vai(r1) == (SINH_TARGET[dm], dm, SINH_BY[dm], KHAC_BY[dm])
        r2 = find_dung_than({}, _analysis("cân bằng", dm, _counts(dm, quan=3.0)))
        assert _vai(r2) == (SINH_TARGET[dm], dm, KHAC_BY[dm], KHAC_TARGET[dm])


def test_la_so_that_bon_vai_luon_khac_nhau():
    """400 lá số thật, ngày–giờ ngẫu nhiên có hạt giống cố định."""
    rng = random.Random(2026)
    goc = date(1950, 1, 1)
    gap = 0
    for _ in range(400):
        d = goc + timedelta(days=rng.randrange(0, 365 * 60))
        tu_tru = get_tu_tru(d.isoformat(), rng.choice(SLOTS))
        r = find_dung_than(tu_tru)
        vai = _vai(r)
        assert len(set(vai)) == 4, (d, vai, r["strength"])
        gap += 1
    assert gap == 400
