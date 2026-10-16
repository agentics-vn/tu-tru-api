"""Luật dụng–hỷ–kỵ–cừu `2026-10.1` (``engine.dung_than_v2``) và cổng chọn phiên bản.

Đặc tả: repo nuoiconthuanmenh.vn, ``docs/superpowers/specs/2026-10-14-dung-ky-dac-ta-thuat-toan.md``
(mục 3–9; 8.1 là hợp đồng đầu ra). Bản cài thử kèm đặc tả (``…-ban-cai-thu.py``, sha
``f849245b…``) là đặc tả chạy được: các trường luật phải trùng nó, ở 67 ca chuẩn
(``tests/fixtures/dung_ky_ca_chuan.json``, chép nguyên) và ở toàn mẫu tổng hợp mục 11.

Luật v1 (mặc định) KHÔNG được đổi: golden ``tests/golden/v1_find_dung_than.json`` canh.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from engine import dung_than_v2 as v2
from engine.can_chi import CAN_NAMES, CHI_NAMES
from engine.chart_bundle import build_chart_analysis
from engine.cuong_nhuoc import analyze_chart_strength
from engine.dung_than import RULE_V1, RULE_V2, find_dung_than
from engine.pillars import get_tu_tru
from engine.thap_than import analyze_god_groups
from tests.golden import v1

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "dung_ky_ca_chuan.json"
# Chép nguyên `2026-10-14-dung-ky-ca-chuan.json` (repo nuoiconthuanmenh.vn); đổi tệp là sửa dòng này.
SHA_FIXTURE = "95745d8dc932cdfb83dfd3480ce51b0cc095487583c1da24e795778d64ca7e51"
CA = json.loads(FIXTURE.read_text(encoding="utf-8"))

TRU = ("year", "month", "day", "hour")
HAN_CAN = "甲乙丙丁戊己庚辛壬癸"
HAN_CHI = "子丑寅卯辰巳午未申酉戌亥"
HANH = ("Mộc", "Hỏa", "Thổ", "Kim", "Thủy")
VAI = {"Dụng", "Hỉ", "Kỵ", "Cừu", "Nhàn"}
KHOA_81 = {
    "rule_version", "nhanh", "dung_than", "hi_than", "ky_than", "cuu_than", "hy_tap", "ky_tap",
    "nhan_tap", "vai_5_hanh", "cuong_nhuoc", "co", "ly_do",
}
KHOA_V1 = {"dung_than", "hi_than", "ky_than", "cuu_than", "strength", "analysis"}

# Vân tay của BẢN CÀI THỬ (không phải của module) trên mẫu tổng hợp mục 11 × {có giờ, không
# giờ} = 13.572 dòng: sha256 của ``v1.chuoi([iso, giờ, co_gio, trường_luật]) + "\n"`` nối theo
# thứ tự mẫu, trường luật = nhanh, bốn ô, ba tập, vai_5_hanh, co.{ty_le, thieu_gio, dieu_hau}.
# Đo 16/10/2026: bản cài thử f849245b chạy trên engine của nhánh này (nền main 88b7a66).
VAN_TAY_BAN_CAI_THU = {"n": 13572, "sha256": "d67bf9342a297fb53b2eb065fa579c52d71fb609f2d3f1e4f6178da55d6eaf12"}


def _tt_tu_han(han: str) -> dict:
    tru = han.split()
    assert len(tru) == 4 and all(len(t) == 2 for t in tru)
    return {p: {"can_idx": HAN_CAN.index(t[0]), "chi_idx": HAN_CHI.index(t[1])} for p, t in zip(TRU, tru)}


def _tt_tu_viet(chuoi: str) -> dict:
    tru = chuoi.split(" | ")
    assert len(tru) == 4
    return {p: {"can_idx": CAN_NAMES.index(t.split()[0]), "chi_idx": CHI_NAMES.index(t.split()[1])}
            for p, t in zip(TRU, tru)}


def _cot(tt: dict) -> dict:
    return {p: {"can_idx": tt[p]["can_idx"], "chi_idx": tt[p]["chi_idx"]} for p in TRU if p in tt}


def _dung_ca(ca: dict) -> dict:
    """Ca `sach` dựng từ chuỗi can chi Hán; ca khác từ ngày + khung giờ của engine."""
    if ca["loai"] == "sach":
        tt = _tt_tu_han(ca["han"])
        assert tt == _tt_tu_viet(ca["tu_tru"]), "chuỗi Hán và chuỗi Việt của ca sách lệch nhau"
        return tt
    tt = get_tu_tru(ca["ngay"], ca["slot"])
    viet = _tt_tu_viet(ca["tu_tru"])
    if ca["co_gio"]:
        assert _cot(tt) == viet
    else:
        # Hai ca `thieu_gio` ghi slot 11 nhưng chuỗi trụ mang giờ thật; trụ giờ bị bỏ nên
        # chỉ ba trụ đầu phải khớp.
        assert {p: _cot(tt)[p] for p in TRU[:3]} == {p: viet[p] for p in TRU[:3]}
    return tt


def mau_2015_2016():
    day = _dt.date(2015, 1, 1)
    while day <= _dt.date(2016, 12, 31):
        for hour in (2, 6, 10, 14, 18, 22):
            yield day.isoformat(), hour
        day += _dt.timedelta(days=7)


MAU = list(mau_2015_2016())
TT_MAU = {(iso, h): get_tu_tru(iso, h) for iso, h in MAU}


def _ket_qua_mau():
    for (iso, h), tt in TT_MAU.items():
        for co_gio in (True, False):
            yield iso, h, co_gio, tt, v2.tinh(tt, co_gio=co_gio)
    for ca in CA:
        tt = _dung_ca(ca)
        yield ca["loai"], ca.get("slot"), ca["co_gio"], tt, v2.tinh(tt, co_gio=ca["co_gio"])


# ─── Bộ ca chuẩn ─────────────────────────────────────────────────────────────

def test_fixture_chep_nguyen():
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == SHA_FIXTURE
    assert len(CA) == 67
    dem = Counter(c["loai"] for c in CA)
    assert dem["sach"] == 26 and dem["nhanh"] == 21 and dem["loi_that"] == 6 and dem["thieu_gio"] == 2
    assert {c["nhanh"] for c in CA if c["loai"] == "nhanh"} == v2.NHANH_HOP_LE


@pytest.mark.parametrize("ca", CA, ids=[f"{i:02d}-{c['loai']}-{c['nhanh']}" for i, c in enumerate(CA)])
def test_ca_chuan_67(ca):
    tt = _dung_ca(ca)
    kq = v2.tinh(tt, co_gio=ca["co_gio"])
    assert kq["nhanh"] == ca["nhanh"]
    assert kq["dung_than"] == ca["dung"]
    assert kq["ky_than"] == ca["ky"]
    assert kq["hy_tap"] == ca["hy"]
    assert kq["ky_tap"][1:] == ca["cuu"]
    assert kq["nhan_tap"] == ca["nhan"]
    assert kq["co"]["ty_le"] == ca["ty_le"]
    assert kq["co"]["thieu_gio"] is (not ca["co_gio"])
    if ca["loai"] == "sach":                  # ca sách: điều sách nói ("!X" = sách nói KHÔNG thành X)
        mong = ca["mong"]
        assert kq["nhanh"] != mong[1:] if mong.startswith("!") else kq["nhanh"] == mong
    assert v2.kiem_bat_bien(kq) == []


@pytest.mark.parametrize("ca", [c for c in CA if not c["co_gio"]], ids=lambda c: c["ngay"])
def test_thieu_gio_khong_doc_tru_gio(ca):
    """Không giờ: kết quả không phụ thuộc trụ giờ, kể cả khi tứ trụ không có khoá `hour`."""
    tt = _dung_ca(ca)
    ba_tru = {p: tt[p] for p in TRU[:3]}
    assert v2.tinh(ba_tru, co_gio=False) == v2.tinh(tt, co_gio=False)
    assert "thieu_gio" in v2.tinh(tt, co_gio=False)["ly_do"]
    # Có giờ thì đi cách đặc biệt nếu đủ điều kiện; ca thứ hai là nhất hành đắc khí khi đủ giờ.
    assert v2.tinh(_tt_tu_viet(ca["tu_tru"]), co_gio=True)["nhanh"] == ca["du_gio"]


# ─── Bất biến ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("co_gio", [True, False])
def test_bat_bien_mau(co_gio):
    loi = {k: v2.kiem_bat_bien(v2.tinh(tt, co_gio=co_gio)) for k, tt in TT_MAU.items()}
    assert len(loi) == len(MAU) == 630
    assert {k: e for k, e in loi.items() if e} == {}


def test_kiem_bat_bien_bat_duoc_loi():
    """Phép kiểm không được xanh vì thiếu dữ liệu: mỗi đột biến phải bị bắt."""
    goc = v2.tinh(TT_MAU[MAU[0]])
    assert v2.kiem_bat_bien(goc) == []

    def dot_bien(f):
        kq = json.loads(json.dumps(goc))
        f(kq)
        return v2.kiem_bat_bien(kq)

    hanh_khac = next(h for h in HANH if h not in (goc["dung_than"], goc["ky_than"]))
    ca = [
        lambda k: k.update(ky_than=k["dung_than"]),                           # dụng trùng kỵ
        lambda k: k["vai_5_hanh"].update({hanh_khac: "Dụng"}),                 # hai dụng
        lambda k: k["vai_5_hanh"].pop("Thổ"),                                 # thiếu hành
        lambda k: k.update(nhanh="CB-V-TK-TT"),                               # nhánh ngoài 21 mã
        lambda k: k.update(rule_version="v1"),                                # sai phiên bản
        lambda k: k["hy_tap"].append(k["ky_tap"][0]),                         # hỷ giao kỵ
        lambda k: k.update(hi_than=None),                                     # rỗng ngoài VAI_RONG_HOP_LE
        lambda k: k.update(nhanh="V-AN" if k["nhanh"] != "V-AN" else "N-QS"),  # bộ vai lệch dòng bảng
    ]
    for i, f in enumerate(ca):
        assert dot_bien(f), f"đột biến {i} lọt"


# ─── Hợp đồng 8.1 ────────────────────────────────────────────────────────────

def test_ly_do_va_phien_ban():
    n = 0
    for _a, _b, co_gio, tt, kq in _ket_qua_mau():
        n += 1
        assert set(kq) == KHOA_81
        assert kq["rule_version"] == "2026-10.1" == RULE_V2 == v2.RULE_VERSION
        assert isinstance(kq["ly_do"], list) and kq["ly_do"] and all(isinstance(x, str) and x for x in kq["ly_do"])
        assert kq["ly_do"][0] == f"r={kq['co']['ty_le']:.3f}"
        L = v2.luc(tt, co_gio=co_gio)["L"]
        assert kq["co"]["dung_vang"] is (L[kq["dung_than"]] < 1.0)
        assert set(kq["co"]) <= {"ty_le", "thieu_gio", "dieu_hau", "dung_vang"}
        r = v2.luc(tt, co_gio=co_gio)["r"]     # so ngưỡng trên giá trị CHƯA làm tròn
        assert kq["cuong_nhuoc"] == ("vượng" if r >= 0.55 else "nhược" if r <= 0.40 else "cân bằng")
        assert set(kq["vai_5_hanh"]) == set(HANH) and set(kq["vai_5_hanh"].values()) <= VAI
    assert n == 2 * 630 + 67


def test_rong_hop_le():
    gap = Counter()
    for *_x, kq in _ket_qua_mau():
        if kq["hi_than"] is None:
            assert kq["nhanh"] == "CB-TQ"
            gap["hi"] += 1
        if kq["cuu_than"] is None:
            assert kq["nhanh"] in {"DB-NHAT-HANH", "DB-HOA"}
            gap["cuu"] += 1
        if kq["nhanh"] == "CB-TQ":
            assert kq["hi_than"] is None
        if kq["nhanh"] in {"DB-NHAT-HANH", "DB-HOA"}:
            assert kq["cuu_than"] is None
    assert gap["hi"] > 0 and gap["cuu"] > 0     # mẫu có phủ cả hai trạng thái rỗng
    assert v2.VAI_RONG_HOP_LE == {("hi_than", "CB-TQ"), ("cuu_than", "DB-NHAT-HANH"), ("cuu_than", "DB-HOA")}


def test_luc_khop_engine():
    """Đặc tả mục 3: L, W, r đúng cách engine đếm (khi có giờ)."""
    for tt in TT_MAU.values():
        lu = v2.luc(tt, co_gio=True)
        a = analyze_chart_strength(tt)
        assert set(lu["L"]) == set(HANH)
        for h in HANH:
            assert lu["L"][h] == pytest.approx(a["element_counts"].get(h, 0.0), abs=1e-9)
        w = analyze_god_groups(tt)["weights"]
        ten = {"TK": "ty_kiep", "AN": "an_tinh", "TT": "thuc_thuong", "TAI": "tai_tinh", "QS": "quan_sat"}
        assert set(w) == set(ten.values())
        for k, g in ten.items():
            assert round(lu["W"][k], 2) == pytest.approx(w[g], abs=1e-9)
        assert round(lu["r"], 3) == a["support_ratio"]
        assert v2.tinh(tt)["cuong_nhuoc"] == a["strength"]


def test_nguong_so_tren_r_chinh_xac():
    """Một lá số của mẫu tổng hợp có r ĐÚNG 0,40 (4,8 / 12,0). Luật 2026-10.1 (và bản cài thử)
    cộng L theo thứ tự HANH nên r == 0.4 → nhược (≤ 0,40). Engine v1 cộng theo thứ tự khoá của
    ``element_counts`` nên ra 0.4000000000000001 → "cân bằng". Đo 16/10/2026: đây là lá số
    DUY NHẤT trong 6.786 mà nhãn hai bên lệch. Golden v1 giữ nguyên nhãn của v1."""
    tt = get_tu_tru("2024-11-09", 22)
    lu = v2.luc(tt)
    assert lu["r"] == 0.4
    kq = v2.tinh(tt)
    assert (kq["cuong_nhuoc"], kq["nhanh"]) == ("nhược", "N-QS")
    a = analyze_chart_strength(tt)
    assert (a["strength"], a["support_ratio"]) == ("cân bằng", 0.4)
    assert find_dung_than(tt, rule=RULE_V2)["strength"] == "nhược"


def test_van_tay_mau_tong_hop_khop_ban_cai_thu():
    """Toàn mẫu tổng hợp mục 11, có và không giờ: trường luật trùng bản cài thử từng byte."""
    h, n, dem = hashlib.sha256(), 0, Counter()
    for iso, hour in v1.mau_tong_hop():
        tt = get_tu_tru(iso, hour)
        for co_gio in (True, False):
            kq = v2.tinh(tt, co_gio=co_gio)
            r = {k: kq[k] for k in ("nhanh", "dung_than", "hi_than", "ky_than", "cuu_than",
                                    "hy_tap", "ky_tap", "nhan_tap", "vai_5_hanh")}
            r["co"] = {k: kq["co"][k] for k in ("ty_le", "thieu_gio", "dieu_hau") if k in kq["co"]}
            h.update((v1.chuoi([iso, hour, co_gio, r]) + "\n").encode("utf-8"))
            n += 1
            if co_gio:
                dem[kq["nhanh"]] += 1
                assert v2.kiem_bat_bien(kq) == []
    assert dict(dem) == v1.DEM_NHANH_MAU
    assert {"n": n, "sha256": h.hexdigest()} == VAN_TAY_BAN_CAI_THU


# ─── Cổng phiên bản ──────────────────────────────────────────────────────────

GOLDEN = json.loads(v1.FILE_DUNG.read_text(encoding="utf-8"))
GOLDEN_ALL = GOLDEN["cases"] + GOLDEN["theo_nhanh"]


@pytest.mark.parametrize("case", GOLDEN_ALL, ids=[c["id"] for c in GOLDEN_ALL])
def test_mac_dinh_v1_khong_doi(case):
    tt = get_tu_tru(case["birth_date"], case["birth_time"])
    out = json.loads(json.dumps(find_dung_than(tt, rule="v1")))
    assert v1.chuoi(out) == v1.chuoi(case["ket_qua"])
    assert set(build_chart_analysis(tt)["dung_than_info"]) == KHOA_V1


def test_cong_chon_phien_ban():
    assert RULE_V1 == "v1" and RULE_V2 == "2026-10.1"
    tt = TT_MAU[MAU[0]]
    kq = find_dung_than(tt, rule=RULE_V2)
    assert set(kq) == KHOA_81 | {"strength", "analysis"}
    assert {k: kq[k] for k in KHOA_81} == v2.tinh(tt)
    assert kq["strength"] == kq["cuong_nhuoc"]
    assert kq["analysis"] == analyze_chart_strength(tt)
    bundle = build_chart_analysis(tt, dung_than_rule=RULE_V2)
    assert bundle["dung_than_info"]["rule_version"] == RULE_V2
    assert bundle["dung_than_info"]["analysis"] is bundle["strength_info"]
    khong_gio = build_chart_analysis(tt, dung_than_rule=RULE_V2, co_gio=False)["dung_than_info"]
    assert khong_gio["co"]["thieu_gio"] is True
    assert {k: khong_gio[k] for k in KHOA_81} == v2.tinh(tt, co_gio=False)
    with pytest.raises(ValueError):
        find_dung_than(tt, rule="2026-10")
    with pytest.raises(ValueError):
        find_dung_than(tt, rule="v1", co_gio=False)   # v1 không có nhánh thiếu giờ
    with pytest.raises(ValueError):
        v2.tinh({p: tt[p] for p in TRU[:3]}, co_gio=True)   # B0: có giờ mà thiếu trụ giờ
