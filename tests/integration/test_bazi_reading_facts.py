"""Integration snapshot — phong-thuy v2 facts for bazi reading §04."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

pytestmark = pytest.mark.direction_c


def test_phong_thuy_full_has_phi_tinh_grid():
    r = client.get(
        "/v1/phong-thuy",
        params={
            "birth_date": "15/03/1984",
            "birth_time": 8,
            "year": 2026,
            "purpose": "NHA_O",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["version"] == 2
    assert len(data.get("phi_tinh") or []) == 9
    assert data["phi_tinh_year"] == 2026
    assert data.get("huong_tot_nam_nay")
    assert data.get("mau_may_man")
