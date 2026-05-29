"""Unit tests — la-so / tu-tru chart contract parity (P2-04)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

pytestmark = pytest.mark.direction_c


class TestLaSoParity:

    def test_la_so_and_tu_tru_share_pillars(self):
        params = {"birth_date": "15/03/1984", "birth_time": 8, "gender": 1}
        la_so = client.get("/v1/la-so", params=params)
        tu_tru = client.post("/v1/tu-tru", json=params)
        assert la_so.status_code == 200
        assert tu_tru.status_code == 200
        a, b = la_so.json(), tu_tru.json()
        for key in ("pillars", "nhat_chu", "dung_than", "cuong_nhuoc", "thap_than"):
            assert key in a
            assert key in b
        assert a["pillars"]["year"]["can"]["name"] == b["pillars"]["year"]["can"]["name"]
        assert a["engine_version"] == b["engine_version"]
        assert a["element_counts"] == b["element_counts"]
        assert a["ngu_hanh"] == b["ngu_hanh"]

    def test_la_so_personality_traits(self):
        r = client.get(
            "/v1/la-so",
            params={"birth_date": "15/03/1984", "birth_time": 8, "gender": 1},
        )
        assert r.status_code == 200
        traits = r.json()["personality_traits"]
        assert len(traits) == 4
        assert {t["id"] for t in traits} == {"diem_manh", "ca_tinh", "luu_y", "tinh_cam"}

    def test_la_so_year_nap_am_mo_ta(self):
        r = client.get("/v1/la-so", params={"birth_date": "15/03/1984", "birth_time": 8})
        assert r.status_code == 200
        mo_ta = r.json()["pillars"]["year"]["nap_am"]["mo_ta"]
        assert isinstance(mo_ta, str) and len(mo_ta) > 5

    def test_luu_nien_mvp(self):
        r = client.get(
            "/v1/la-so/luu-nien",
            params={
                "birth_date": "15/03/1984",
                "birth_time": 8,
                "gender": 1,
                "year": 2026,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["year_label_vi"]
        assert len(data["month_scores"]) == 12
        assert len(data["life_areas"]) == 4
        assert data["quy_nhan"]["tuoi_hop"]
        assert data["quy_nhan"]["huong_quy_nhan"]
        assert data["dai_van_next"]
        assert len(data["month_score_values"]) == 12
        assert data["assumptions_vi"]
