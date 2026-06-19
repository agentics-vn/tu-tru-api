from engine.pillars import get_tu_tru
from engine.tuan_khong import analyze_tuan_khong


def test_golden_tuan_khong():
    t = get_tu_tru("2026-06-19", 10)
    tk = analyze_tuan_khong(t)
    assert tk["nien_khong"]["display"] == "Dần - Mão"
    assert tk["nhat_khong"]["display"] == "Tuất - Hợi"
