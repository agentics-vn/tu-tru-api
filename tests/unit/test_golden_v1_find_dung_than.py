"""Golden v1 của `find_dung_than`: 60 lá số, đầu ra của `main` 88b7a66.

Dùng làm nền cho `test_mac_dinh_v1_khong_doi` khi cài luật `2026-10.1`:
lời gọi mặc định phải trả y hệt từng byte. Sinh bằng ``tests/golden/v1.py --ghi``.
"""

from __future__ import annotations

import json
from collections import Counter

import pytest

from engine.dung_than import find_dung_than
from engine.pillars import get_tu_tru
from tests.golden import v1

CASES = json.loads(v1.FILE_DUNG.read_text(encoding="utf-8"))["cases"]


def test_golden_dung_than_contract():
    assert len(CASES) == 60
    assert [(c["id"], c["birth_date"], c["birth_time"]) for c in CASES] == v1.tao_la_so_dung()
    # Phủ cả ba nhãn cường nhược và ca dụng trùng kỵ của v1 (giữ nguyên, không sửa ở đây).
    assert set(Counter(c["ket_qua"]["strength"] for c in CASES)) == {"nhược", "cân bằng", "vượng"}
    assert sum(c["ket_qua"]["dung_than"] == c["ket_qua"]["ky_than"] for c in CASES) == 5


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_golden_tu_tru_input(case):
    tt = get_tu_tru(case["birth_date"], case["birth_time"])
    assert v1.chuoi(json.loads(json.dumps(tt))) == v1.chuoi(case["tu_tru"])


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_golden_find_dung_than_v1(case):
    tt = get_tu_tru(case["birth_date"], case["birth_time"])
    out = json.loads(json.dumps(find_dung_than(tt)))
    assert v1.chuoi(out) == v1.chuoi(case["ket_qua"])
