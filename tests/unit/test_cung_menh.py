from engine.cung_menh import get_menh_cung, get_thai_nguyen
from engine.pillars import get_tu_tru


def test_thai_nguyen_giap_ngo():
    assert get_thai_nguyen(0, 6)["display"] == "Ất Dậu"


def test_menh_cung_golden():
    t = get_tu_tru("2026-06-19", 10)
    m = get_menh_cung(
        t["year"]["can_idx"],
        t["month"]["chi_idx"],
        t["hour"]["chi_idx"],
    )
    assert m["display"] == "Giáp Ngọ"
