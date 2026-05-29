"""Unit tests for P1/P2 helper modules."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from api.day_score_response import build_purpose_rows, good_and_avoid_from_purpose_rows
from api.profile_store import get_profile, memory_profile_count, save_profile
from calendar_service import get_day_info, get_user_chart


def test_good_and_avoid_from_purpose_rows():
    day_info = get_day_info("2026-05-28")
    user_chart = get_user_chart("1984-03-15", 8, 1)
    rows = build_purpose_rows(day_info, user_chart)
    good_for, avoid_for = good_and_avoid_from_purpose_rows(rows)
    assert isinstance(good_for, list)
    assert isinstance(avoid_for, list)
    assert "Mặc định" not in good_for
    assert "Mặc định" not in avoid_for


def test_profile_store_memory_roundtrip():
    pid = "test-profile-abc"
    data = {"birth_date": "15/03/1984", "birth_time": 8, "gender": 1}
    save_profile(pid, data)
    loaded = get_profile(pid)
    assert loaded == data
    assert memory_profile_count() >= 1
