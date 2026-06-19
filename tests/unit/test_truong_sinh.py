from engine.pillars import get_tu_tru
from engine.truong_sinh import get_truong_sinh_stage


def test_giap_at_ngo_is_tu():
    assert get_truong_sinh_stage(0, 6)["label_vi"] == "Tử"


def test_giap_at_ty_is_moc_duc():
    assert get_truong_sinh_stage(0, 0)["label_vi"] == "Mộc Dục"
