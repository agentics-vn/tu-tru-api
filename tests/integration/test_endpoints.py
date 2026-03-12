"""
test_endpoints.py — Integration tests for all API endpoints.

Uses FastAPI TestClient to test endpoints end-to-end.
Run with: python3 -m pytest tests/integration/test_endpoints.py -v
"""

import sys
import os

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from fastapi.testclient import TestClient

from app import app

# Set dev API key for testing
os.environ.setdefault("NODE_ENV", "development")

client = TestClient(app, headers={"X-API-Key": "test-key-dev"})


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

class TestHealth:

    def test_health_check(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


# ─────────────────────────────────────────────────────────────────────────────
# POST /v1/chon-ngay
# ─────────────────────────────────────────────────────────────────────────────

class TestChonNgay:

    def _valid_request(self, **overrides) -> dict:
        body = {
            "birth_date": "1984-03-15",
            "intent": "KHAI_TRUONG",
            "range_start": "2026-04-01",
            "range_end": "2026-04-30",
            "top_n": 3,
        }
        body.update(overrides)
        return body

    def test_success(self):
        r = client.post("/v1/chon-ngay", json=self._valid_request())
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert "recommended_dates" in data
        assert "dates_to_avoid" in data
        assert "meta" in data

    def test_recommended_dates_have_time_slots(self):
        """time_slots should now be populated (not empty)."""
        r = client.post("/v1/chon-ngay", json=self._valid_request())
        data = r.json()
        for d in data["recommended_dates"]:
            assert isinstance(d["time_slots"], list)
            # Should have 6 good hours per day
            assert len(d["time_slots"]) == 6
            # Each slot should be "HH:MM-HH:MM" format
            for slot in d["time_slots"]:
                assert "-" in slot

    def test_safety_invariant_severity3_not_in_recommended(self):
        """Severity=3 dates must NEVER appear in recommended_dates (TC-10)."""
        r = client.post("/v1/chon-ngay", json=self._valid_request())
        data = r.json()
        sev3_dates = {
            d["date"] for d in data.get("dates_to_avoid", [])
            if d.get("severity") == 3
        }
        rec_dates = {d["date"] for d in data.get("recommended_dates", [])}
        assert len(sev3_dates & rec_dates) == 0, (
            f"Safety violation: {sev3_dates & rec_dates}"
        )

    def test_meta_contains_bat_tu_summary(self):
        r = client.post("/v1/chon-ngay", json=self._valid_request())
        data = r.json()
        meta = data["meta"]
        assert "bat_tu_summary" in meta
        assert meta["bat_tu_summary"]["ngu_hanh_menh"] == "Kim"
        assert meta["bat_tu_summary"]["duong_than"] == "Thổ"
        assert meta["bat_tu_summary"]["ky_than"] == "Hỏa"

    def test_invalid_birth_date_future(self):
        r = client.post("/v1/chon-ngay", json=self._valid_request(
            birth_date="2099-01-01"
        ))
        assert r.status_code == 400
        assert r.json()["error_code"] == "INVALID_INPUT"

    def test_range_too_large(self):
        r = client.post("/v1/chon-ngay", json=self._valid_request(
            range_start="2026-01-01",
            range_end="2026-12-31",
        ))
        assert r.status_code == 400
        assert r.json()["error_code"] == "RANGE_TOO_LARGE"

    def test_cuoi_hoi_alias(self):
        """CUOI_HOI in API should map to DAM_CUOI internally."""
        r = client.post("/v1/chon-ngay", json=self._valid_request(
            intent="CUOI_HOI"
        ))
        assert r.status_code == 200

    def test_recommended_dates_sorted_by_score(self):
        r = client.post("/v1/chon-ngay", json=self._valid_request(top_n=5))
        data = r.json()
        scores = [d["score"] for d in data["recommended_dates"]]
        assert scores == sorted(scores, reverse=True)

    def test_grade_is_valid(self):
        r = client.post("/v1/chon-ngay", json=self._valid_request())
        data = r.json()
        for d in data["recommended_dates"]:
            assert d["grade"] in {"A", "B", "C", "D"}


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/ngay-hom-nay
# ─────────────────────────────────────────────────────────────────────────────

class TestNgayHomNay:

    def test_success_with_date(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "1984-03-15",
            "date": "2026-04-01",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["date"] == "2026-04-01"

    def test_has_can_chi(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "1984-03-15",
            "date": "2026-04-01",
        })
        data = r.json()
        assert "can_chi" in data
        assert "name" in data["can_chi"]
        assert "can_name" in data["can_chi"]
        assert "chi_name" in data["can_chi"]

    def test_has_hoang_dao_badge(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "1984-03-15",
            "date": "2026-04-01",
        })
        data = r.json()
        assert "hoang_dao" in data
        assert data["hoang_dao"]["badge"] in ("HOÀNG ĐẠO", "HẮC ĐẠO")
        assert isinstance(data["hoang_dao"]["is_hoang_dao"], bool)

    def test_has_gio_tot_xau(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "1984-03-15",
            "date": "2026-04-01",
        })
        data = r.json()
        assert len(data["gio_tot"]) == 6
        assert len(data["gio_xau"]) == 6
        for g in data["gio_tot"]:
            assert "chi_name" in g
            assert "range" in g

    def test_has_good_for_avoid_for(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "1984-03-15",
            "date": "2026-04-01",
        })
        data = r.json()
        assert isinstance(data["good_for"], list)
        assert isinstance(data["avoid_for"], list)

    def test_has_daily_advice(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "1984-03-15",
            "date": "2026-04-01",
        })
        data = r.json()
        assert "daily_advice" in data
        assert "nen_lam" in data["daily_advice"]
        assert "nen_tranh" in data["daily_advice"]

    def test_has_lunar_info(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "1984-03-15",
            "date": "2026-04-01",
        })
        data = r.json()
        assert "lunar" in data
        assert "display" in data["lunar"]
        assert data["lunar"]["day"] >= 1

    def test_invalid_birth_date(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "invalid",
            "date": "2026-04-01",
        })
        assert r.status_code == 400

    def test_defaults_to_today(self):
        """When no 'date' param, should use today."""
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "1984-03-15",
        })
        assert r.status_code == 200
        data = r.json()
        assert "date" in data


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/lich-thang
# ─────────────────────────────────────────────────────────────────────────────

class TestLichThang:

    def test_success(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "1984-03-15",
            "month": "2026-03",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["month"] == "2026-03"

    def test_correct_day_count_march(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "1984-03-15",
            "month": "2026-03",
        })
        data = r.json()
        assert len(data["days"]) == 31  # March has 31 days

    def test_correct_day_count_february(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "1984-03-15",
            "month": "2026-02",
        })
        data = r.json()
        assert len(data["days"]) == 28  # 2026 is not a leap year

    def test_day_has_hoang_dao_badge(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "1984-03-15",
            "month": "2026-03",
        })
        data = r.json()
        for d in data["days"]:
            assert d["badge"] in ("hoang_dao", "hac_dao")
            assert isinstance(d["is_hoang_dao"], bool)
            assert "star_name" in d

    def test_day_has_truc_and_layer1(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "1984-03-15",
            "month": "2026-03",
        })
        data = r.json()
        for d in data["days"]:
            assert "truc_name" in d
            assert "is_layer1_pass" in d
            assert "can_chi_name" in d

    def test_has_user_menh(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "1984-03-15",
            "month": "2026-03",
        })
        data = r.json()
        assert data["user_menh"]["hanh"] == "Kim"

    def test_invalid_month_format(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "1984-03-15",
            "month": "2026",
        })
        assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/tieu-van
# ─────────────────────────────────────────────────────────────────────────────

class TestTieuVan:

    def test_success(self):
        r = client.get("/v1/tieu-van", params={
            "birth_date": "1984-03-15",
            "month": "2026-03",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["month"] == "2026-03"

    def test_has_pillar(self):
        r = client.get("/v1/tieu-van", params={
            "birth_date": "1984-03-15",
            "month": "2026-03",
        })
        data = r.json()
        pillar = data["tieu_van_pillar"]
        assert "can_name" in pillar
        assert "chi_name" in pillar
        assert "display" in pillar
        assert "nap_am_hanh" in pillar

    def test_has_user_menh(self):
        r = client.get("/v1/tieu-van", params={
            "birth_date": "1984-03-15",
            "month": "2026-03",
        })
        data = r.json()
        assert data["user_menh"]["hanh"] == "Kim"
        assert data["user_menh"]["name"] == "Hải Trung Kim"

    def test_has_element_relation(self):
        r = client.get("/v1/tieu-van", params={
            "birth_date": "1984-03-15",
            "month": "2026-03",
        })
        data = r.json()
        assert data["element_relation"] in {
            "tuong_sinh", "bi_sinh", "tuong_khac", "bi_khac", "binh_hoa"
        }

    def test_has_reading_and_tags(self):
        r = client.get("/v1/tieu-van", params={
            "birth_date": "1984-03-15",
            "month": "2026-03",
        })
        data = r.json()
        assert isinstance(data["reading"], str)
        assert len(data["reading"]) > 20
        assert isinstance(data["tags"], list)
        assert len(data["tags"]) > 0

    def test_invalid_month_format(self):
        r = client.get("/v1/tieu-van", params={
            "birth_date": "1984-03-15",
            "month": "March-2026",
        })
        assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# Purity: same input → same output across all endpoints
# ─────────────────────────────────────────────────────────────────────────────

class TestEndpointPurity:

    def test_chon_ngay_deterministic(self):
        body = {
            "birth_date": "1984-03-15",
            "intent": "KHAI_TRUONG",
            "range_start": "2026-04-01",
            "range_end": "2026-04-15",
            "top_n": 3,
        }
        r1 = client.post("/v1/chon-ngay", json=body)
        r2 = client.post("/v1/chon-ngay", json=body)
        assert r1.json() == r2.json()

    def test_ngay_hom_nay_deterministic(self):
        params = {"birth_date": "1984-03-15", "date": "2026-04-01"}
        r1 = client.get("/v1/ngay-hom-nay", params=params)
        r2 = client.get("/v1/ngay-hom-nay", params=params)
        assert r1.json() == r2.json()

    def test_lich_thang_deterministic(self):
        params = {"birth_date": "1984-03-15", "month": "2026-03"}
        r1 = client.get("/v1/lich-thang", params=params)
        r2 = client.get("/v1/lich-thang", params=params)
        assert r1.json() == r2.json()
