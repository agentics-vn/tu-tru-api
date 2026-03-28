"""Integration: POST /v1/hop-tuoi v1 vs v2."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_hop_tuoi_v1_default():
    r = client.post(
        "/v1/hop-tuoi",
        json={
            "person1_birth_date": "15/05/1990",
            "person2_birth_date": "20/03/1992",
            "person1_birth_time": 8,
            "person2_birth_time": 10,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data.get("version") == 1
    assert "overall_score" in data
    assert "grade" in data


def test_hop_tuoi_v2_phu_the():
    r = client.post(
        "/v1/hop-tuoi",
        json={
            "person1_birth_date": "15/05/1990",
            "person2_birth_date": "20/03/1992",
            "person1_birth_time": 8,
            "person2_birth_time": 10,
            "relationship_type": "PHU_THE",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "success"
    assert data.get("version") == 2
    assert data["relationship_type"] == "PHU_THE"
    assert data["relationship_label"] == "Phu Thê"
    assert "verdict" in data
    assert "verdict_level" in data
    assert isinstance(data["criteria"], list)
    for c in data["criteria"]:
        assert c["sentiment"] in ("positive", "neutral", "negative")
        assert "name" in c and "description" in c
    assert data["reading"]
    assert data["advice"]


def test_hop_tuoi_v2_phu_the_with_genders():
    r = client.post(
        "/v1/hop-tuoi",
        json={
            "person1_birth_date": "15/05/1990",
            "person2_birth_date": "20/03/1992",
            "person1_birth_time": 8,
            "person2_birth_time": 10,
            "person1_gender": 1,
            "person2_gender": -1,
            "relationship_type": "PHU_THE",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("version") == 2
    gioi = next(c for c in data["criteria"] if c["name"] == "Giới tính (phu thê)")
    assert gioi["sentiment"] == "positive"


def test_hop_tuoi_v2_invalid_relationship():
    r = client.post(
        "/v1/hop-tuoi",
        json={
            "person1_birth_date": "15/05/1990",
            "person2_birth_date": "20/03/1992",
            "relationship_type": "UNKNOWN",
        },
    )
    assert r.status_code == 400
