"""Integration tests — Direction C day-score parity and contract."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

pytestmark = pytest.mark.direction_c


class TestDayScoreParity:

    def test_ngay_hom_nay_matches_day_detail_score(self):
        params = {
            "birth_date": "15/03/1984",
            "birth_time": 8,
            "gender": 1,
            "date": "2026-05-28",
            "intent": "MAC_DINH",
        }
        home = client.get("/v1/ngay-hom-nay", params=params)
        detail = client.get("/v1/day-detail", params={**params, "mode": "personalized"})
        assert home.status_code == 200
        assert detail.status_code == 200
        h, d = home.json(), detail.json()
        assert h["score"] == d["score"]
        assert h["grade"] == d["grade"]

    def test_chon_ngay_detail_matches_day_detail(self):
        body = {
            "birth_date": "15/03/1984",
            "birth_time": 8,
            "gender": 1,
            "intent": "KHAI_TRUONG",
            "date": "15/04/2026",
        }
        detail_post = client.post("/v1/chon-ngay/detail", json=body)
        detail_get = client.get(
            "/v1/day-detail",
            params={
                "birth_date": body["birth_date"],
                "birth_time": body["birth_time"],
                "gender": body["gender"],
                "date": "2026-04-15",
                "intent": body["intent"],
                "mode": "personalized",
            },
        )
        assert detail_post.status_code == 200
        assert detail_get.status_code == 200
        p, g = detail_post.json(), detail_get.json()
        assert p["score"] == g["score"]
        assert p["grade"] == g["grade"]
        assert len(p["breakdown"]) == 4
        assert [x["id"] for x in p["breakdown"]] == [x["id"] for x in g["breakdown"]]
        for a, b in zip(p["breakdown"], g["breakdown"]):
            assert a["points"] == b["points"]
            assert a["type"] == b["type"]


class TestDirectionCEndpoints:

    def test_generic_day_detail_no_birth(self):
        r = client.get("/v1/day-detail", params={"date": "2026-05-28", "mode": "generic"})
        assert r.status_code == 200
        data = r.json()
        assert data["personalized"] is False
        assert len(data["breakdown_generic"]) == 4

    def test_chon_ngay_ranked_days(self):
        r = client.post(
            "/v1/chon-ngay",
            json={
                "birth_date": "15/03/1984",
                "intent": "KHAI_TRUONG",
                "range_start": "01/04/2026",
                "range_end": "30/04/2026",
                "top_n": 3,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert "ranked_days" in data
        assert "intent_label_vi" in data
        assert "range_start" in data
        assert data["empty_reason_vi"] is None
        if data["ranked_days"]:
            row = data["ranked_days"][0]
            assert row["reason_vi"] == row["summary_vi"]

    def test_breakdown_sum_equals_score_day_detail(self):
        params = {
            "birth_date": "15/03/1984",
            "birth_time": 8,
            "gender": 1,
            "date": "2026-05-28",
            "mode": "personalized",
            "intent": "MAC_DINH",
        }
        r = client.get("/v1/day-detail", params=params)
        assert r.status_code == 200
        data = r.json()
        assert sum(x["points"] for x in data["breakdown"]) == data["score"]

    def test_breakdown_sum_equals_score_chon_ngay_detail(self):
        r = client.post(
            "/v1/chon-ngay/detail",
            json={
                "birth_date": "15/03/1984",
                "birth_time": 8,
                "gender": 1,
                "intent": "MAC_DINH",
                "date": "28/05/2026",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert sum(x["points"] for x in data["breakdown"]) == data["score"]

    def test_day_compare_cuoi_hoi_matches_day_detail(self):
        base = {
            "birth_date": "15/03/1984",
            "birth_time": 8,
            "gender": 1,
            "date": "2026-08-28",
            "mode": "personalized",
        }
        detail_cuoi = client.get("/v1/day-detail", params={**base, "intent": "CUOI_HOI"})
        detail_dam = client.get("/v1/day-detail", params={**base, "intent": "DAM_CUOI"})
        compare = client.get(
            "/v1/day-compare",
            params={
                "birth_date": "15/03/1984",
                "birth_time": 8,
                "gender": 1,
                "date_a": "2026-08-27",
                "date_b": "2026-08-28",
                "intent": "CUOI_HOI",
            },
        )
        assert detail_cuoi.status_code == 200
        assert detail_dam.status_code == 200
        assert compare.status_code == 200
        assert detail_cuoi.json()["score"] == detail_dam.json()["score"]
        assert compare.json()["score_b"] == detail_cuoi.json()["score"]

    def test_chon_ngay_safety_ranked_days_no_sev3(self):
        r = client.post(
            "/v1/chon-ngay",
            json={
                "birth_date": "15/03/1984",
                "intent": "KHAI_TRUONG",
                "range_start": "01/04/2026",
                "range_end": "30/04/2026",
                "top_n": 5,
            },
        )
        assert r.status_code == 200
        data = r.json()
        sev3 = {d["date"] for d in data.get("dates_to_avoid", []) if d.get("severity") == 3}
        ranked = {d["date"] for d in data.get("ranked_days", [])}
        assert not (sev3 & ranked)

    def test_chon_ngay_invalid_intent_post_400(self):
        r = client.post(
            "/v1/chon-ngay",
            json={
                "birth_date": "15/03/1984",
                "intent": "BAO_GIO_CUNG_DUOC",
                "range_start": "01/04/2026",
                "range_end": "30/04/2026",
            },
        )
        assert r.status_code == 400
        assert r.json()["error_code"] == "INVALID_INPUT"

    def test_luan_context_mirror(self):
        params = {
            "birth_date": "15/03/1984",
            "birth_time": 8,
            "gender": 1,
            "date": "2026-05-28",
            "intent": "MAC_DINH",
        }
        detail = client.get("/v1/day-detail", params={**params, "mode": "personalized"})
        luan = client.get("/v1/day-detail/luan-context", params=params)
        assert detail.status_code == 200
        assert luan.status_code == 200
        d, l = detail.json(), luan.json()
        for a, b in zip(d["breakdown"], l["breakdown_summary"]):
            assert a["id"] == b["id"]
            assert a["type"] == b["verdict_vi"]
            assert a["reason_vi"] == b["reason_vi"]
            assert a["points"] == b["points"]

    def test_luan_context_gio_labels_backward_compat(self):
        r = client.get(
            "/v1/day-detail/luan-context",
            params={
                "birth_date": "15/03/1984",
                "date": "2026-05-28",
                "intent": "MAC_DINH",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["gio_tot"]) == 6
        assert len(data["gio_tot_labels"]) == 6
        assert all(isinstance(x, str) for x in data["gio_tot_labels"])

    def test_luan_context_invalid_intent(self):
        r = client.get(
            "/v1/day-detail/luan-context",
            params={
                "birth_date": "15/03/1984",
                "date": "2026-05-28",
                "intent": "BAO_GIO_CUNG_DUOC",
            },
        )
        assert r.status_code == 400
        assert r.json()["error_code"] == "INVALID_INPUT"

    def test_day_compare_delta(self):
        r = client.get(
            "/v1/day-compare",
            params={
                "birth_date": "15/03/1984",
                "date_a": "2026-05-28",
                "date_b": "2026-05-29",
                "intent": "MAC_DINH",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["delta_score"] == data["score_b"] - data["score_a"]

    def test_chon_ngay_empty_returns_200(self):
        r = client.post(
            "/v1/chon-ngay",
            json={
                "birth_date": "15/03/1984",
                "intent": "KHAI_TRUONG",
                "range_start": "13/08/2026",
                "range_end": "19/08/2026",
                "top_n": 3,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["ranked_days"] == []
        assert data["empty_reason_vi"]
        assert "Không tìm được ngày tốt" in data["empty_reason_vi"]

    def test_fixture_scores_personalized(self):
        birth = {
            "birth_date": "15/03/1984",
            "birth_time": 8,
            "gender": 1,
            "mode": "personalized",
            "intent": "MAC_DINH",
        }
        r35 = client.get("/v1/day-detail", params={**birth, "date": "2026-05-28"})
        r76 = client.get("/v1/day-detail", params={**birth, "date": "2026-06-26"})
        assert r35.status_code == 200 and r35.json()["score"] == 35
        assert r76.status_code == 200 and r76.json()["score"] == 76

    def test_invalid_intent_rejected(self):
        r = client.get(
            "/v1/day-detail",
            params={
                "date": "2026-05-28",
                "mode": "personalized",
                "birth_date": "15/03/1984",
                "intent": "BAO_GIO_CUNG_DUOC",
            },
        )
        assert r.status_code == 400
        assert r.json()["error_code"] == "INVALID_INPUT"

    def test_lich_thang_score_matches_day_detail(self):
        params = {
            "birth_date": "15/03/1984",
            "birth_time": 8,
            "gender": 1,
            "month": "2026-05",
        }
        lt = client.get("/v1/lich-thang", params=params)
        detail = client.get(
            "/v1/day-detail",
            params={
                "birth_date": "15/03/1984",
                "birth_time": 8,
                "gender": 1,
                "date": "2026-05-28",
                "mode": "personalized",
                "intent": "MAC_DINH",
            },
        )
        assert lt.status_code == 200 and detail.status_code == 200
        day = next(d for d in lt.json()["days"] if d["date"] == "2026-05-28")
        assert day["score"] == detail.json()["score"]
        assert day["grade"] == detail.json()["grade"]

    def test_chon_ngay_perf_smoke(self):
        import time

        start = time.perf_counter()
        r = client.post(
            "/v1/chon-ngay",
            json={
                "birth_date": "15/03/1984",
                "intent": "MAC_DINH",
                "range_start": "01/01/2026",
                "range_end": "31/03/2026",
                "top_n": 5,
            },
        )
        elapsed = time.perf_counter() - start
        assert r.status_code == 200
        assert elapsed < 8.0, f"p95 smoke failed: {elapsed:.2f}s"
