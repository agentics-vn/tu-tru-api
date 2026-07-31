"""Integration — hai endpoint phải trả CÙNG một bộ Dụng-Kỵ cho cùng một người.

Trước đây `/v1/phong-thuy` gọi thiếu birth_time sẽ rơi về đường nạp âm và trả
Dụng = Thổ, Kỵ = Hỏa, trong khi `/v1/la-so` của đúng người đó trả Dụng = Hỏa.
Hỏa vừa là Dụng vừa là Kỵ tùy endpoint — phần luận giải đọc cả hai sẽ tự mâu
thuẫn. Các test dưới đây khóa lại chuyện đó.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

NGUOI = {"birth_date": "15/03/1984", "birth_time": 8, "gender": 1}


def test_la_so_va_phong_thuy_cung_bo_dung_ky():
    la_so = client.get("/v1/la-so", params=NGUOI).json()
    phong_thuy = client.get("/v1/phong-thuy", params={**NGUOI, "year": 2026}).json()

    assert phong_thuy["dung_than_method"] == "tu_tru"
    assert phong_thuy["dung_than"] == la_so["dung_than"]
    assert phong_thuy["ky_than"] == la_so["ky_than"]
    assert phong_thuy["vai_5_hanh"] == la_so["vai_5_hanh"]


def test_duong_nap_am_khong_phat_vai_5_hanh():
    """Thiếu birth_time → vẫn trả lời được, nhưng KHÔNG kèm bảng phân vai.

    Bộ vai suy từ nạp âm năm sinh không cùng gốc với tứ trụ; phát nó ra là tạo
    bộ Dụng-Kỵ thứ hai.
    """
    r = client.get("/v1/phong-thuy", params={"birth_date": "15/03/1984"})
    assert r.status_code == 200
    payload = r.json()
    assert payload["dung_than_method"] == "nap_am"
    assert "vai_5_hanh" not in payload
    assert "precision_note" in payload


def test_vai_5_hanh_phu_tron_5_hanh_qua_api():
    payload = client.get("/v1/la-so", params=NGUOI).json()
    vai = payload["vai_5_hanh"]
    assert set(vai) == {"Mộc", "Hỏa", "Thổ", "Kim", "Thủy"}
    assert vai[payload["dung_than"]] == "Dụng"
    assert sorted(vai.values()).count("Dụng") == 1
