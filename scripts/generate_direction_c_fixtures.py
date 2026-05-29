#!/usr/bin/env python3
"""Generate Direction C fixture JSON from live API responses."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from app import app

OUT = Path(__file__).resolve().parents[1] / "docs" / "fixtures" / "direction-c"
OUT.mkdir(parents=True, exist_ok=True)

client = TestClient(app)


def save(name: str, response) -> None:
    path = OUT / name
    path.write_text(json.dumps(response.json(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path}")


def main() -> None:
    save("day-detail-generic.json", client.get("/v1/day-detail", params={"date": "2026-05-28", "mode": "generic"}))

    birth = {"birth_date": "15/03/1984", "birth_time": 8, "gender": 1}

    p35 = {**birth, "date": "2026-05-28", "mode": "personalized", "intent": "MAC_DINH"}
    save("day-detail-personalized-35.json", client.get("/v1/day-detail", params=p35))

    p76 = {**birth, "date": "2026-06-26", "mode": "personalized", "intent": "MAC_DINH"}
    save("day-detail-personalized-76.json", client.get("/v1/day-detail", params=p76))

    save(
        "chon-ngay-happy.json",
        client.post(
            "/v1/chon-ngay",
            json={
                "birth_date": "15/03/1984",
                "intent": "KHAI_TRUONG",
                "range_start": "01/04/2026",
                "range_end": "30/04/2026",
                "top_n": 3,
            },
        ),
    )

    save(
        "chon-ngay-empty.json",
        client.post(
            "/v1/chon-ngay",
            json={
                "birth_date": "15/03/1984",
                "intent": "KHAI_TRUONG",
                "range_start": "13/08/2026",
                "range_end": "19/08/2026",
                "top_n": 3,
            },
        ),
    )

    luan_params = {"birth_date": "15/03/1984", "birth_time": 8, "gender": 1, "date": "2026-05-28"}
    save("day-luan-context.json", client.get("/v1/day-detail/luan-context", params=luan_params))

    save(
        "day-compare.json",
        client.get(
            "/v1/day-compare",
            params={
                "birth_date": "15/03/1984",
                "date_a": "2026-05-28",
                "date_b": "2026-05-29",
            },
        ),
    )

    save(
        "la-so-full.json",
        client.get("/v1/la-so", params={"birth_date": "15/03/1984", "birth_time": 8, "gender": 1}),
    )

    save(
        "la-so-luu-nien-2026.json",
        client.get(
            "/v1/la-so/luu-nien",
            params={"birth_date": "15/03/1984", "birth_time": 8, "gender": 1, "year": 2026},
        ),
    )

    save(
        "phong-thuy-year-2026.json",
        client.get(
            "/v1/phong-thuy",
            params={"birth_date": "15/03/1984", "year": 2026},
        ),
    )


if __name__ == "__main__":
    main()
