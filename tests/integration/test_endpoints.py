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

client = TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

class TestHealth:

    def test_health_check(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "engine_version" in data


# ─────────────────────────────────────────────────────────────────────────────
# POST /v1/chon-ngay
# ─────────────────────────────────────────────────────────────────────────────

class TestChonNgay:

    def _valid_request(self, **overrides) -> dict:
        body = {
            "birth_date": "15/03/1984",
            "intent": "KHAI_TRUONG",
            "range_start": "01/04/2026",
            "range_end": "30/04/2026",
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
            # Each slot should be {"chi_name": "...", "range": "HH:MM-HH:MM"}
            for slot in d["time_slots"]:
                assert "chi_name" in slot
                assert "-" in slot["range"]

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

    def test_safety_invariant_severity3_not_in_ranked_days(self):
        """Direction C: severity=3 must never appear in ranked_days."""
        r = client.post("/v1/chon-ngay", json=self._valid_request())
        data = r.json()
        sev3_dates = {
            d["date"] for d in data.get("dates_to_avoid", [])
            if d.get("severity") == 3
        }
        ranked_dates = {d["date"] for d in data.get("ranked_days", [])}
        assert len(sev3_dates & ranked_dates) == 0, (
            f"Safety violation in ranked_days: {sev3_dates & ranked_dates}"
        )

    def test_invalid_intent_returns_400(self):
        """TC-06: unknown intent → 400 INVALID_INPUT (via validation handler)."""
        r = client.post(
            "/v1/chon-ngay",
            json=self._valid_request(intent="BAO_GIO_CUNG_DUOC"),
        )
        assert r.status_code == 400
        assert r.json()["error_code"] == "INVALID_INPUT"

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
            birth_date="01/01/2099"
        ))
        assert r.status_code == 400
        assert r.json()["error_code"] == "INVALID_INPUT"

    def test_range_too_large(self):
        r = client.post("/v1/chon-ngay", json=self._valid_request(
            range_start="01/01/2026",
            range_end="31/12/2026",
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
# GET /v1/share/{token}
# ─────────────────────────────────────────────────────────────────────────────

class TestShare:

    def test_chon_ngay_token_replay_matches_original(self):
        r = client.post("/v1/chon-ngay", json=TestChonNgay()._valid_request())
        assert r.status_code == 200
        orig = r.json()
        token = orig["meta"]["share_token"]

        r2 = client.get(f"/v1/share/{token}")
        assert r2.status_code == 200
        shared = r2.json()
        assert shared["shared"] is True
        assert shared["endpoint"] == "chon-ngay"
        assert shared["ranked_days"]
        assert {d["date"] for d in shared["ranked_days"]} == {
            d["date"] for d in orig["ranked_days"]
        }
        for d in shared["ranked_days"]:
            assert len(d["time_slots"]) == 6
            assert "chi" in d["time_slots"][0]

    def test_share_safety_invariant_severity3_not_in_ranked_days(self):
        r = client.post("/v1/chon-ngay", json=TestChonNgay()._valid_request())
        token = r.json()["meta"]["share_token"]
        shared = client.get(f"/v1/share/{token}").json()
        sev3_dates = {
            d["date"] for d in shared.get("dates_to_avoid", [])
            if d.get("severity") == 3
        }
        ranked_dates = {d["date"] for d in shared.get("ranked_days", [])}
        assert len(sev3_dates & ranked_dates) == 0

    def test_invalid_share_token_returns_400(self):
        r = client.get("/v1/share/not-a-valid-token")
        assert r.status_code == 400
        assert r.json()["error_code"] == "INVALID_INPUT"


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/weekly-summary (deprecated)
# ─────────────────────────────────────────────────────────────────────────────

class TestWeeklySummary:

    def test_invalid_intent_returns_400(self):
        r = client.get(
            "/v1/weekly-summary",
            params={
                "birth_date": "15/03/1984",
                "intent": "BAO_GIO_CUNG_DUOC",
            },
        )
        assert r.status_code == 400
        assert r.json()["error_code"] == "INVALID_INPUT"


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/ngay-hom-nay
# ─────────────────────────────────────────────────────────────────────────────

class TestNgayHomNay:

    def test_success_with_date(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "15/03/1984",
            "date": "2026-04-01",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["date"] == "2026-04-01"

    def test_has_can_chi(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "15/03/1984",
            "date": "2026-04-01",
        })
        data = r.json()
        assert "can_chi" in data
        assert "name" in data["can_chi"]
        assert "can_name" in data["can_chi"]
        assert "chi_name" in data["can_chi"]

    def test_has_hoang_dao_badge(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "15/03/1984",
            "date": "2026-04-01",
        })
        data = r.json()
        assert "hoang_dao" in data
        assert data["hoang_dao"]["badge"] in ("HOÀNG ĐẠO", "HẮC ĐẠO")
        assert isinstance(data["hoang_dao"]["is_hoang_dao"], bool)

    def test_has_gio_tot_xau(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "15/03/1984",
            "date": "2026-04-01",
        })
        data = r.json()
        assert len(data["gio_tot"]) == 6
        assert len(data["gio_xau"]) == 6
        for g in data["gio_tot"]:
            assert "chi_name" in g
            assert "range" in g
            assert "start_hour" in g
            assert "end_hour" in g

    def test_has_good_for_avoid_for(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "15/03/1984",
            "date": "2026-04-01",
        })
        data = r.json()
        assert isinstance(data["good_for"], list)
        assert isinstance(data["avoid_for"], list)

    def test_has_daily_advice(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "15/03/1984",
            "date": "2026-04-01",
        })
        data = r.json()
        assert "daily_advice" in data
        assert "nen_lam" in data["daily_advice"]
        assert "nen_tranh" in data["daily_advice"]

    def test_has_lunar_info(self):
        r = client.get("/v1/ngay-hom-nay", params={
            "birth_date": "15/03/1984",
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
            "birth_date": "15/03/1984",
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
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["month"] == "2026-03"

    def test_correct_day_count_march(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        data = r.json()
        assert len(data["days"]) == 31  # March has 31 days

    def test_correct_day_count_february(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "15/03/1984",
            "month": "2026-02",
        })
        data = r.json()
        assert len(data["days"]) == 28  # 2026 is not a leap year

    def test_day_has_hoang_dao_badge(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        data = r.json()
        for d in data["days"]:
            assert d["badge"] in ("hoang_dao", "hac_dao")
            assert isinstance(d["is_hoang_dao"], bool)
            assert "star_name" in d

    def test_day_has_truc_and_layer1(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        data = r.json()
        for d in data["days"]:
            assert "truc_name" in d
            assert "is_layer1_pass" in d
            assert "can_chi_name" in d

    def test_has_user_menh(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        data = r.json()
        assert data["user_menh"]["hanh"] == "Kim"

    def test_day_has_gio_tot_slots(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        data = r.json()
        for d in data["days"]:
            assert "gio_tot" in d
            assert len(d["gio_tot"]) == 6
            for g in d["gio_tot"]:
                assert "chi_name" in g
                assert "range" in g
                assert "label_vi" in g

    def test_day_has_sao_28(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        data = r.json()
        for d in data["days"]:
            assert "sao_28" in d
            assert "name" in d["sao_28"]
            assert "hanh" in d["sao_28"]
            assert d["sao_28"]["tot_xau"] in ("tốt", "xấu", "vừa")

    def test_day_has_summary(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        data = r.json()
        for d in data["days"]:
            assert "summary" in d
            assert isinstance(d["summary"]["tot"], list)
            assert isinstance(d["summary"]["xau"], list)
            assert d["summary"]["rating"] in ("tốt", "xấu", "bình thường")

    def test_sao_28_cycles_every_28_days(self):
        """28 Tú should cycle: day 1 and day 29 should have same star."""
        r = client.get("/v1/lich-thang", params={
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        data = r.json()
        # Day 1 (Mar 1) and Day 29 (Mar 29) should have same 28 Tu
        assert data["days"][0]["sao_28"]["name"] == data["days"][28]["sao_28"]["name"]

    def test_invalid_month_format(self):
        r = client.get("/v1/lich-thang", params={
            "birth_date": "15/03/1984",
            "month": "2026",
        })
        assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/tieu-van
# ─────────────────────────────────────────────────────────────────────────────

class TestTieuVan:

    def test_success(self):
        r = client.get("/v1/tieu-van", params={
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["month"] == "2026-03"

    def test_has_pillar(self):
        r = client.get("/v1/tieu-van", params={
            "birth_date": "15/03/1984",
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
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        data = r.json()
        assert data["user_menh"]["hanh"] == "Kim"
        assert data["user_menh"]["name"] == "Hải Trung Kim"

    def test_has_element_relation(self):
        r = client.get("/v1/tieu-van", params={
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        data = r.json()
        assert data["element_relation"] in {
            "tuong_sinh", "bi_sinh", "tuong_khac", "bi_khac", "binh_hoa"
        }

    def test_has_reading_and_tags(self):
        r = client.get("/v1/tieu-van", params={
            "birth_date": "15/03/1984",
            "month": "2026-03",
        })
        data = r.json()
        assert isinstance(data["reading"], str)
        assert len(data["reading"]) > 20
        assert isinstance(data["tags"], list)
        assert len(data["tags"]) > 0

    def test_invalid_month_format(self):
        r = client.get("/v1/tieu-van", params={
            "birth_date": "15/03/1984",
            "month": "March-2026",
        })
        assert r.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# POST /v1/tu-tru
# ─────────────────────────────────────────────────────────────────────────────

class TestTuTru:

    def test_basic_no_birth_time(self):
        """Without birth_time, returns year-level Nạp Âm info only."""
        r = client.post("/v1/tu-tru", json={
            "birth_date": "15/03/1984",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["birth_year_can_chi"] == "Giáp Tý"
        assert data["menh"]["hanh"] == "Kim"
        assert data["menh"]["nap_am_name"] == "Hải Trung Kim"
        assert "_note" in data
        assert "pillars" not in data
        assert "element_counts" not in data

    def test_full_with_birth_time(self):
        """With birth_time, returns full Tứ Trụ analysis."""
        r = client.post("/v1/tu-tru", json={
            "birth_date": "15/03/1984",
            "birth_time": 8,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert "pillars" in data
        assert "year" in data["pillars"]
        assert "month" in data["pillars"]
        assert "day" in data["pillars"]
        assert "hour" in data["pillars"]
        assert "tu_tru_display" in data
        assert "nhat_chu" in data
        assert "chart_strength" in data
        assert data["chart_strength"] in ("vượng", "nhược", "cân bằng")
        assert "dung_than" in data
        assert "hi_than" in data
        assert "ky_than" in data
        assert "cuu_than" in data
        assert "thap_than" in data
        ec = data["element_counts"]
        assert set(ec.keys()) == {"Kim", "Mộc", "Thủy", "Hỏa", "Thổ"}
        assert all(isinstance(ec[k], (int, float)) for k in ec)
        assert "support_ratio" in data
        assert 0.0 <= data["support_ratio"] <= 1.0

    def test_pillar_structure(self):
        """Each pillar should have can_chi, can, chi, nap_am."""
        r = client.post("/v1/tu-tru", json={
            "birth_date": "15/03/1984",
            "birth_time": 8,
        })
        data = r.json()
        for key in ("year", "month", "day", "hour"):
            p = data["pillars"][key]
            assert "can_chi" in p
            assert "can" in p and "idx" in p["can"] and "name" in p["can"]
            assert "chi" in p and "idx" in p["chi"] and "name" in p["chi"]
            assert "nap_am" in p and "hanh" in p["nap_am"] and "name" in p["nap_am"]

    def test_thap_than_structure(self):
        """Thập Thần should have year/month/hour gods + dominant."""
        r = client.post("/v1/tu-tru", json={
            "birth_date": "15/03/1984",
            "birth_time": 8,
        })
        data = r.json()
        tt = data["thap_than"]
        for key in ("year", "month", "hour"):
            assert "key" in tt[key]
            assert "name" in tt[key]
            assert "category" in tt[key]
        assert "dominant" in tt
        assert "key" in tt["dominant"]
        assert "name" in tt["dominant"]

    def test_dai_van_with_gender(self):
        """With birth_time + gender, returns Đại Vận cycles."""
        r = client.post("/v1/tu-tru", json={
            "birth_date": "15/03/1984",
            "birth_time": 8,
            "gender": 1,
        })
        assert r.status_code == 200
        data = r.json()
        assert "dai_van" in data
        assert "current" in data["dai_van"]
        assert "cycles" in data["dai_van"]
        assert len(data["dai_van"]["cycles"]) == 8  # default 8 cycles
        for c in data["dai_van"]["cycles"]:
            assert "display" in c
            assert "hanh" in c
            assert "age_range" in c

    def test_no_dai_van_without_gender(self):
        """Without gender, should not include Đại Vận."""
        r = client.post("/v1/tu-tru", json={
            "birth_date": "15/03/1984",
            "birth_time": 8,
        })
        data = r.json()
        assert "dai_van" not in data

    def test_invalid_birth_date_future(self):
        r = client.post("/v1/tu-tru", json={
            "birth_date": "01/01/2099",
        })
        assert r.status_code in (400, 422)

    def test_invalid_birth_time(self):
        r = client.post("/v1/tu-tru", json={
            "birth_date": "15/03/1984",
            "birth_time": 7,
        })
        assert r.status_code in (400, 422)

    def test_invalid_gender(self):
        r = client.post("/v1/tu-tru", json={
            "birth_date": "15/03/1984",
            "birth_time": 8,
            "gender": "other",
        })
        assert r.status_code in (400, 422)

    def test_birth_time_label(self):
        r = client.post("/v1/tu-tru", json={
            "birth_date": "15/03/1984",
            "birth_time": 23,
        })
        data = r.json()
        assert data["birth_time_label"] == "Giờ Tý Muộn (23h-23h59)"


# ─────────────────────────────────────────────────────────────────────────────
# POST /v1/la-so-full
# ─────────────────────────────────────────────────────────────────────────────

class TestLaSoFull:

    def _valid_request(self, **overrides) -> dict:
        body = {
            "birth_date": "19/06/2026",
            "birth_time": 10,
            "gender": 1,
            "birth_minute": 57,
            "name": "NGUYỄN VĂN T",
        }
        body.update(overrides)
        return body

    def test_success(self):
        r = client.post("/v1/la-so-full", json=self._valid_request())
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert "engine_version" in data
        mb = data["menh_ban"]
        assert mb["tu_tru_display"] == "Bính Ngọ | Giáp Ngọ | Giáp Tý | Kỷ Tỵ"
        assert set(mb["pillars"].keys()) == {"year", "month", "day", "hour"}
        assert mb["dai_van"]["khoi_van_date"] == "2032-06-13"
        assert len(mb["luu_nien"]) == 10
        assert mb["header"]["tiet_khi"]["name"] == "Mang Chủng"
        # One call returns both structured data (for LLM) and embeddable HTML.
        assert "mbtt" in data["html"]
        assert "Mệnh Bàn Tứ Trụ" in data["html"]

    def test_view_year(self):
        r = client.post("/v1/la-so-full", json=self._valid_request(
            birth_date="21/03/1990",
            birth_time=6,
            birth_minute=15,
            view_year=2026,
        ))
        assert r.status_code == 200
        mb = r.json()["menh_ban"]
        assert mb["header"]["tiet_khi"]["name"] == "Xuân Phân"
        assert mb["dai_van"]["khoi_van_date"] == "1995-04-05"
        luu = mb["luu_nien"]
        assert luu[0]["year"] == 2026
        assert luu[0]["display"] == "Bính Ngọ"
        assert luu[0]["selected"] is True

    def test_invalid_birth_date_future(self):
        r = client.post("/v1/la-so-full", json=self._valid_request(
            birth_date="01/01/2099",
        ))
        assert r.status_code in (400, 422)

    def test_deterministic(self):
        body = self._valid_request()
        r1 = client.post("/v1/la-so-full", json=body)
        r2 = client.post("/v1/la-so-full", json=body)
        assert r1.json() == r2.json()

    def test_format_html(self):
        r = client.post("/v1/la-so-full", json={
            **self._valid_request(
                birth_date="21/03/1990",
                birth_time=6,
                birth_minute=15,
                view_year=2026,
            ),
            "format": "html",
        })
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        assert "mbtt" in r.text
        assert "Mệnh Bàn Tứ Trụ" in r.text
        assert "Canh" in r.text


# ─────────────────────────────────────────────────────────────────────────────
# Purity: same input → same output across all endpoints
# ─────────────────────────────────────────────────────────────────────────────

class TestEndpointPurity:

    def test_chon_ngay_deterministic(self):
        body = {
            "birth_date": "15/03/1984",
            "intent": "KHAI_TRUONG",
            "range_start": "01/04/2026",
            "range_end": "15/04/2026",
            "top_n": 3,
        }
        r1 = client.post("/v1/chon-ngay", json=body)
        r2 = client.post("/v1/chon-ngay", json=body)
        assert r1.json() == r2.json()

    def test_ngay_hom_nay_deterministic(self):
        params = {"birth_date": "15/03/1984", "date": "2026-04-01"}
        r1 = client.get("/v1/ngay-hom-nay", params=params)
        r2 = client.get("/v1/ngay-hom-nay", params=params)
        assert r1.json() == r2.json()

    def test_lich_thang_deterministic(self):
        params = {"birth_date": "15/03/1984", "month": "2026-03"}
        r1 = client.get("/v1/lich-thang", params=params)
        r2 = client.get("/v1/lich-thang", params=params)
        assert r1.json() == r2.json()

    def test_tu_tru_deterministic(self):
        body = {"birth_date": "15/03/1984", "birth_time": 8, "gender": 1}
        r1 = client.post("/v1/tu-tru", json=body)
        r2 = client.post("/v1/tu-tru", json=body)
        assert r1.json() == r2.json()
