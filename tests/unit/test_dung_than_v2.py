"""Luật dụng–hỷ–kỵ–cừu `2026-10.1` (``engine.dung_than_v2``) và cổng chọn phiên bản.

Đặc tả: repo nuoiconthuanmenh.vn, ``docs/superpowers/specs/2026-10-14-dung-ky-dac-ta-thuat-toan.md``
(mục 3–9; 8.1 là hợp đồng đầu ra). Bản cài thử kèm đặc tả (``…-ban-cai-thu.py``, sha
sửa theo đặc tả 3.1) là đặc tả chạy được: các trường luật phải trùng nó, ở 73 ca chuẩn
(``tests/fixtures/dung_ky_ca_chuan.json``, chép nguyên) và ở toàn mẫu tổng hợp mục 11.

Đặc tả 3.1 (chốt 16/10/2026): luật mới đếm lực bằng số nguyên đơn vị 0,1 và so mọi ngưỡng, mọi
hoà trên số nguyên. Hai bản cùng đếm thì cùng sai được, nên ``test_chinh_xac_doc_lap`` tính lại
bằng ``Fraction`` theo một đường riêng, và ``test_ranh_gioi`` ghim từng loại hoà, từng ngưỡng.

Luật v1 (mặc định) KHÔNG được đổi: golden ``tests/golden/v1_find_dung_than.json`` canh.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from collections import Counter
from fractions import Fraction
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
# Chép nguyên `docs/superpowers/specs/2026-10-14-dung-ky-ca-chuan.json` (repo nuoiconthuanmenh.vn,
# nhánh claude/dung-ky-do-15-ten) ở phiên bản bộ ca PHIEN_BAN_CA. sha256 cả tệp ghim ở đây và ở
# kịch bản mốc 4; bộ ca tự mang phiên bản và sha256 của danh sách ca. Đổi tệp là sửa ba dòng này.
PHIEN_BAN_CA = "2026-10-16.1"
SHA_FIXTURE = "4a73b7b24df69664f7887be334ad6ca3d3de8e2ba9d58f100257e41f74829a39"
SHA_CA = "ad77d3804783e1574827809a7b0498e0954d173469917400c6a2fa30e7e9fd0a"
BO_CA = json.loads(FIXTURE.read_text(encoding="utf-8"))
CA = BO_CA["ca"]

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
# Đo 16/10/2026: bản cài thử SỐ NGUYÊN (sha 404ddf8a…, đặc tả 3.1) trên engine của nhánh này (nền
# main 88b7a66). Vân tay của bản số thực cũ (f849245b) là d67bf934…; hai bản lệch ở 34 lá số có giờ
# (32 đổi vai, 2 chỉ đổi cờ) và 30 dòng không giờ (chỉ đổi cờ/ty_le), báo cáo Task 2 vòng sửa 1.
VAN_TAY_BAN_CAI_THU = {"n": 13572, "sha256": "eb74707275b8210346424553d01d30816d0fa96e27abf3918417ec0c4e56c33f"}
# Đếm nhánh trên mẫu có giờ khi tính đúng. `v1.DEM_NHANH_MAU` (golden, không sửa) là đếm của bản
# số thực: khác ở mười nhánh, cùng tổng 6.786.
DEM_NHANH_SO_NGUYEN = {
    "CB-DH-HAN": 102, "CB-DH-NHIET": 89, "CB-N-QS": 537, "CB-N-TAI": 407, "CB-N-TT": 486,
    "CB-TQ": 113, "CB-V-AN": 380, "CB-V-TK-QS": 354, "DB-HOA": 57, "DB-NHAT-HANH": 37,
    "DB-TONG-CUONG": 23, "DB-TONG-NHI": 32, "DB-TONG-SAT": 14, "DB-TONG-TAI": 22,
    "DB-TONG-VUONG": 5, "N-QS": 786, "N-TAI": 642, "N-TT": 718, "V-AN": 893,
    "V-TK-QS": 881, "V-TK-TT": 208,
}
# Tám lá số mẫu có r ĐÚNG một ngưỡng mà nhãn `strength` của v1 (cộng số thực) lệch giá trị đúng.
# v1 giữ nguyên (đặc tả 3.1); luật mới ra nhãn đúng.
V1_LECH_NHAN = {
    ("2006-06-10", 14): "nhược", ("2007-09-08", 22): "nhược", ("2024-11-09", 22): "nhược",
    ("2009-06-13", 22): "vượng", ("2015-08-15", 22): "vượng", ("2019-05-11", 22): "vượng",
    ("2019-06-01", 22): "vượng", ("2019-08-03", 22): "vượng",
}


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
    assert (BO_CA["phien_ban_ca"], BO_CA["rule_version"], BO_CA["so_ca"]) == (PHIEN_BAN_CA, RULE_V2, len(CA))
    sha_ca = hashlib.sha256(json.dumps(CA, ensure_ascii=False, sort_keys=True,
                                       separators=(",", ":")).encode("utf-8")).hexdigest()
    assert sha_ca == BO_CA["sha256_ca"] == SHA_CA
    assert len(CA) == 73
    dem = Counter(c["loai"] for c in CA)
    assert dem["sach"] == 26 and dem["nhanh"] == 21 and dem["loi_that"] == 6 and dem["thieu_gio"] == 2
    assert dem["hoi_quy"] == 2 and dem["ranh_gioi"] == 4
    assert all(dem[f"sat_nguong_{x}"] == 2 for x in ("0.4", "0.55", "0.7"))
    assert {c["nhanh"] for c in CA if c["loai"] == "nhanh"} == v2.NHANH_HOP_LE


@pytest.mark.parametrize("ca", [c for c in CA if c["loai"] == "hoi_quy"], ids=lambda c: c["ngay"])
def test_hoi_quy_co_giai_trinh(ca):
    """Hai ca chuẩn cũ mang kỳ vọng do nhiễu số thực: giữ làm hồi quy, kỳ vọng cũ ghi lại."""
    assert set(ca["giai_trinh"]) == {"gia_tri_dung", "cau_dac_ta", "so_thuc_gay_loi", "sua"}
    kq = v2.tinh(_dung_ca(ca))
    assert kq["nhanh"] == ca["nhanh"] != ca["ky_vong_cu"]["nhanh"]


@pytest.mark.parametrize("ca", CA, ids=[f"{i:02d}-{c['loai']}-{c['nhanh']}" for i, c in enumerate(CA)])
def test_ca_chuan(ca):
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
    assert v2.kiem_bat_bien(kq, tt) == []


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
        lu = v2.luc(tt, co_gio=co_gio)
        assert kq["co"]["dung_vang"] is (lu["L"][kq["dung_than"]] < 10)      # L < 1,0
        assert set(kq["co"]) <= {"ty_le", "thieu_gio", "dieu_hau", "dung_vang"}
        r = Fraction(lu["ho"], lu["tong"])
        assert kq["cuong_nhuoc"] == ("vượng" if r >= Fraction(55, 100) else
                                     "nhược" if r <= Fraction(40, 100) else "cân bằng")
        assert all(v2.ly_do_hop_le(x) for x in kq["ly_do"]), kq["ly_do"]
        assert kq["co"]["ty_le"] == float(_tron3(r))
        assert set(kq["vai_5_hanh"]) == set(HANH) and set(kq["vai_5_hanh"].values()) <= VAI
    assert n == 2 * 630 + len(CA)


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
    for key, tt in TT_MAU.items():
        lu = v2.luc(tt, co_gio=True)
        a = analyze_chart_strength(tt)
        assert set(lu["L"]) == set(HANH)
        assert all(isinstance(x, int) for x in [*lu["L"].values(), *lu["W"].values(), lu["ho"], lu["tong"]])
        for h in HANH:
            assert lu["L"][h] / 10 == pytest.approx(a["element_counts"].get(h, 0.0), abs=1e-9)
        w = analyze_god_groups(tt)["weights"]
        ten = {"TK": "ty_kiep", "AN": "an_tinh", "TT": "thuc_thuong", "TAI": "tai_tinh", "QS": "quan_sat"}
        assert set(w) == set(ten.values())
        for k, g in ten.items():
            assert lu["W"][k] / 10 == pytest.approx(w[g], abs=1e-9)
        assert lu["r"] == pytest.approx(a["support_ratio"], abs=5e-4 + 1e-12)
        assert v2.tinh(tt)["cuong_nhuoc"] == V1_LECH_NHAN.get(key, a["strength"])


@pytest.mark.parametrize("key", sorted(V1_LECH_NHAN), ids=lambda k: f"{k[0]}-{k[1]}")
def test_v1_lech_nhan_o_nguong(key):
    """r đúng bằng 0,40 hoặc 0,55 (hộ/tổng nguyên). Luật mới ra nhãn đúng; v1 (số thực) ra
    "cân bằng" và giữ nguyên như thế (đặc tả 3.1, golden v1 không sửa)."""
    tt = get_tu_tru(*key)
    lu = v2.luc(tt)
    pct = 40 if V1_LECH_NHAN[key] == "nhược" else 55
    assert 100 * lu["ho"] == pct * lu["tong"]
    kq = v2.tinh(tt)
    assert kq["cuong_nhuoc"] == V1_LECH_NHAN[key] == find_dung_than(tt, rule=RULE_V2)["strength"]
    assert not kq["nhanh"].startswith("CB-")
    a = analyze_chart_strength(tt)
    assert (a["strength"], a["support_ratio"]) == ("cân bằng", pct / 100)
    assert find_dung_than(tt)["strength"] == "cân bằng"


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
    assert dict(dem) == DEM_NHANH_SO_NGUYEN
    khac_v1 = {k for k in v1.DEM_NHANH_MAU if v1.DEM_NHANH_MAU[k] != DEM_NHANH_SO_NGUYEN[k]}
    assert khac_v1 == {"CB-DH-NHIET", "CB-N-QS", "CB-N-TAI", "CB-N-TT", "DB-TONG-TAI", "N-QS",
                       "N-TAI", "V-AN", "V-TK-QS", "V-TK-TT"} and sum(dem.values()) == 6786
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
    # I1: thiếu giờ thì không đặt phân tích bốn trụ cạnh nhãn ba trụ, kể cả khi người gọi truyền vào
    assert khong_gio["analysis"] is None
    assert khong_gio["strength"] == khong_gio["cuong_nhuoc"]
    assert find_dung_than(tt, analysis=analyze_chart_strength(tt), rule=RULE_V2, co_gio=False)["analysis"] is None
    assert find_dung_than({p: tt[p] for p in TRU[:3]}, rule=RULE_V2, co_gio=False)["analysis"] is None
    with pytest.raises(ValueError):
        find_dung_than(tt, rule="2026-10")
    with pytest.raises(ValueError):
        find_dung_than(tt, rule="v1", co_gio=False)   # v1 không có nhánh thiếu giờ
    with pytest.raises(ValueError):
        v2.tinh({p: tt[p] for p in TRU[:3]}, co_gio=True)   # B0: có giờ mà thiếu trụ giờ


# ─── Số học chính xác: kiểm độc lập với bản cài thử (đặc tả 3.1) ─────────────

from engine.can_chi import CAN_HANH, CHI_HANH  # noqa: E402
from engine.cuong_nhuoc import _seasonal_bonus  # noqa: E402
from engine.dung_than import KHAC_BY, KHAC_TARGET, SINH_BY, SINH_TARGET  # noqa: E402
from engine.hoa_hop import detect_stem_transformations, effective_stem_hanh  # noqa: E402
from engine.tang_can import get_tang_can  # noqa: E402

F = Fraction


def _tron3(r: Fraction) -> Fraction:
    """Làm tròn ba chữ số, nửa lên, trên số hữu tỉ."""
    n = r * 1000
    return Fraction(int(n + Fraction(1, 2)), 1000) if n >= 0 else -_tron3(-r)


def _chinh_xac(tt: dict, co_gio: bool) -> dict:
    """L, W, r bằng Fraction, dựng lại từ tứ trụ thô theo chữ của đặc tả mục 3.

    KHÔNG nhập hàm nào của ``dung_than_v2`` hay của bản cài thử (không ``_dem``, ``_ty_le``,
    ``luc``, ``_lon_nhat``, ``_so_sanh``, ``_dieu_hau``, ``_thong_quan``…): phép đếm, phép so ngưỡng,
    thứ tự hoà ở đây viết riêng. Những gì DÙNG CHUNG với module, và vì sao an toàn:
    - bảng dữ liệu: ``get_tang_can`` (tàng can và trọng số 1,0/0,6/0,3, đọc qua ``str`` thành 1, 3/5,
      3/10), ``CAN_HANH``, ``CHI_NAMES``, bốn bảng sinh/khắc của module v1 (``SINH_BY``…);
    - ``_seasonal_bonus``: chỉ đọc GIÁ TRỊ (+2/+1/−0,5/−1) như một bảng (tháng, nhật chủ) → số;
    - ``detect_stem_transformations`` / ``effective_stem_hanh``: luật hợp hoá của engine, mà đặc tả
      mục 3 định nghĩa là ĐẦU VÀO ("can hiệu lực theo luật engine"), không phải phép đếm hay phép so.
    Sai ở các bảng ấy là sai đầu vào cho cả hai bên; thứ phép kiểm này soi là cách đếm và cách so."""
    tru = TRU if co_gio else TRU[:3]
    nen = tt if co_gio else {**{p: tt[p] for p in TRU[:3]}, "hour": dict(tt["day"])}
    hh = [t for t in detect_stem_transformations(nen) if co_gio or "hour" not in (t["pillar_a"], t["pillar_b"])]
    dm = CAN_HANH[tt["day"]["can_idx"]]
    g = {"TK": dm, "AN": SINH_BY[dm], "TT": SINH_TARGET[dm], "TAI": KHAC_TARGET[dm], "QS": KHAC_BY[dm]}
    nhom = {h: k for k, h in g.items()}
    L = {h: F(0) for h in HANH}
    W = {k: F(0) for k in g}
    for p in tru:
        eh, ok = effective_stem_hanh(p, tt[p]["can_idx"], hh)
        eh = eh if ok else CAN_HANH[tt[p]["can_idx"]]
        L[eh] += 1
        if p != "day":
            W[nhom[eh]] += 1
        for an in get_tang_can(tt[p]["chi_idx"]):
            L[an["hanh"]] += F(str(an["weight"]))
            W[nhom[an["hanh"]]] += F(str(an["weight"]))
    b = F(str(_seasonal_bonus(dm, tt["month"]["chi_idx"])))
    ho = L[dm] + L[g["AN"]]
    chong = sum(L.values()) - ho
    ho, chong = ho + max(0, b), chong + max(0, -b)
    return {"g": g, "L": L, "W": W, "r": ho / (ho + chong)}


def _dieu_hau_dung(tt: dict, x: dict) -> str | None:
    L, thang = x["L"], CHI_NAMES[tt["month"]["chi_idx"]]
    lanh, am = L["Kim"] + L["Thủy"], L["Mộc"] + L["Hỏa"]
    if thang in ("Tý", "Sửu", "Dần") and L["Hỏa"] < 1 and lanh > am:
        return "HAN"
    if thang in ("Tỵ", "Ngọ", "Mùi") and L["Thủy"] < 1 and am > lanh:
        return "NHIET"
    return None


def _nhanh_chinh_cach(tt: dict, x: dict) -> str:
    """Nhánh chính cách (mục 6) từ số hữu tỉ; đặc tả đọc thẳng, không qua bảng của module."""
    L, W, r = x["L"], x["W"], x["r"]
    thang = CHI_NAMES[tt["month"]["chi_idx"]]

    def nhuoc():
        return "N-" + max(("QS", "TT", "TAI"), key=lambda k: W[k])      # hoà: QS, TT, TAI

    def vuong():
        if W["AN"] > W["TK"]:
            return "V-AN"
        return "V-TK-TT" if r >= F(70, 100) else "V-TK-QS"

    if r >= F(55, 100):
        return vuong()
    if r <= F(40, 100):
        return nhuoc()
    lanh, am = L["Kim"] + L["Thủy"], L["Mộc"] + L["Hỏa"]
    if thang in ("Tý", "Sửu", "Dần") and L["Hỏa"] < 1 and lanh > am:
        return "CB-DH-HAN"
    if thang in ("Tỵ", "Ngọ", "Mùi") and L["Thủy"] < 1 and am > lanh:
        return "CB-DH-NHIET"
    xep = sorted(HANH, key=lambda h: -L[h])
    a, b = xep[0], xep[1]
    tong = sum(L.values())
    if (KHAC_BY[b] == a or KHAC_BY[a] == b) and L[a] >= F(30, 100) * tong and L[b] >= F(30, 100) * tong \
            and L[a] - L[b] <= F(15, 100) * L[a]:
        return "CB-TQ"
    return "CB-" + (nhuoc() if r < F(1, 2) else vuong())


def _cuong_nhuoc_dung(r: Fraction) -> str:
    return "vượng" if r >= F(55, 100) else "nhược" if r <= F(40, 100) else "cân bằng"


@pytest.mark.parametrize("co_gio", [True, False])
def test_chinh_xac_doc_lap(co_gio):
    """Toàn mẫu mục 11: nhãn của luật mới bằng nhãn tính bằng số hữu tỉ (đường riêng)."""
    n = Counter()
    for iso, hour in v1.mau_tong_hop():
        tt = get_tu_tru(iso, hour)
        x = _chinh_xac(tt, co_gio)
        kq = v2.tinh(tt, co_gio=co_gio)
        lu = v2.luc(tt, co_gio=co_gio)
        assert {h: F(lu["L"][h], 10) for h in HANH} == x["L"]
        assert {k: F(lu["W"][k], 10) for k in lu["W"]} == x["W"]
        assert F(lu["ho"], lu["tong"]) == x["r"]
        assert kq["cuong_nhuoc"] == _cuong_nhuoc_dung(x["r"]), (iso, hour)
        assert kq["co"]["ty_le"] == float(_tron3(x["r"])), (iso, hour)
        nh = kq["nhanh"]
        if nh.startswith("DB-"):
            assert co_gio
            if nh in ("DB-HOA", "DB-TONG-TAI", "DB-TONG-SAT", "DB-TONG-NHI"):
                assert x["r"] <= F(40, 100), (iso, hour)
            if nh.startswith("DB-TONG-") and nh not in ("DB-TONG-VUONG", "DB-TONG-CUONG"):
                theo = max(("QS", "TAI", "TT"), key=lambda k: x["W"][k])      # hoà: QS, TAI, TT
                assert nh == {"QS": "DB-TONG-SAT", "TAI": "DB-TONG-TAI", "TT": "DB-TONG-NHI"}[theo]
            if nh in ("DB-TONG-VUONG", "DB-TONG-CUONG"):
                assert x["r"] >= F(55, 100)
                assert (nh == "DB-TONG-VUONG") is (x["W"]["AN"] < x["W"]["TK"] / 2), (iso, hour)
            n["db"] += 1
        else:
            assert nh == _nhanh_chinh_cach(tt, x), (iso, hour)
            n["chinh"] += 1
            if not nh.startswith("CB-"):                 # 6.4: cờ điều hậu ở vượng/nhược
                dh = _dieu_hau_dung(tt, x)
                assert kq["co"].get("dieu_hau", "").split(":")[0] == (dh or ""), (iso, hour)
    assert sum(n.values()) == 6786 and (n["db"] > 0) is co_gio


# Mỗi dòng: (ngày, giờ, nhánh mong đợi, ranh giới, phép kiểm rằng lá số NẰM ĐÚNG trên ranh giới).
# Chọn từ mẫu mục 11 và từ dò mỗi ngày 1940–2019 (scratchpad Task 2, tim_ranh.py).
RANH_GIOI = [
    ("2005-06-04", 10, "V-TK-QS", "6.2 hoà W[AN] = W[TK] → TK", lambda x: x["W"]["AN"] == x["W"]["TK"]),
    ("2005-01-08", 10, "N-QS", "6.1 hoà W[QS] = W[TT] → QS", lambda x: x["W"]["QS"] == x["W"]["TT"]),
    ("2011-01-08", 10, "N-QS", "6.1 hoà W[QS] = W[TAI] → QS", lambda x: x["W"]["QS"] == x["W"]["TAI"]),
    ("2018-09-01", 14, "N-TT", "6.1 hoà W[TT] = W[TAI] → TT", lambda x: x["W"]["TT"] == x["W"]["TAI"]),
    ("1942-08-07", 6, "DB-TONG-SAT", "5.3 hoà W[QS] = W[TAI] → QS", lambda x: x["W"]["QS"] == x["W"]["TAI"]),
    ("1941-10-24", 20, "DB-TONG-TAI", "5.3 hoà W[TAI] = W[TT] → TAI", lambda x: x["W"]["TAI"] == x["W"]["TT"]),
    ("2014-05-31", 14, "N-QS", "5.3 hoà W[QS] = W[TAI] → QS, tháng không phải QS → không tòng",
     lambda x: x["W"]["QS"] == x["W"]["TAI"]),
    ("1947-12-20", 6, "DB-TONG-CUONG", "5.4 W[AN] = W[TK]/2 → không < → Tòng Cường",
     lambda x: 2 * x["W"]["AN"] == x["W"]["TK"]),
    ("2006-01-14", 14, "N-QS", "6.4 lạnh = ấm → không điều hậu",
     lambda x: x["L"]["Kim"] + x["L"]["Thủy"] == x["L"]["Mộc"] + x["L"]["Hỏa"]),
    ("2024-06-15", 18, "CB-V-TK-QS", "6.3.1 lạnh = ấm → không điều hậu (và W[AN] = W[TK])",
     lambda x: x["L"]["Kim"] + x["L"]["Thủy"] == x["L"]["Mộc"] + x["L"]["Hỏa"]),
    ("2006-06-10", 14, "N-QS", "r = 0,40 → nhược", lambda x: x["r"] == F(2, 5)),
    ("1942-11-09", 4, "DB-HOA", "5.2 r = 0,40 → còn xét hoá khí", lambda x: x["r"] == F(2, 5)),
    ("2009-02-14", 10, "CB-V-AN", "6.3.3 r = 0,50 → nghiêng vượng", lambda x: x["r"] == F(1, 2)),
    ("2009-06-13", 22, "V-TK-QS", "r = 0,55 → vượng", lambda x: x["r"] == F(11, 20)),
    ("1945-09-28", 6, "V-TK-TT", "6.2 r = 0,70 → cực vượng", lambda x: x["r"] == F(7, 10)),
    ("1964-05-02", 8, "CB-TQ", "6.3.2 chênh đúng 15% → thông quan",
     lambda x: (lambda a, b: a - b == F(15, 100) * a)(*sorted(x["L"].values(), reverse=True)[:2])),
    ("1942-02-22", 8, "CB-TQ", "6.3.2 hành nhỏ đúng 30% tổng → thông quan",
     lambda x: sorted(x["L"].values(), reverse=True)[1] == F(30, 100) * sum(x["L"].values())),
    ("1959-05-10", 22, "CB-TQ", "6.3.2 hai hành bằng nhau, mỗi hành đúng 30% (hoà L theo Mộc → Thủy)",
     lambda x: sorted(x["L"].values(), reverse=True)[0] == F(30, 100) * sum(x["L"].values())),
]


@pytest.mark.parametrize("iso,gio,nhanh,ten,tren_ranh", RANH_GIOI, ids=[f"{r[0]}-{r[1]}" for r in RANH_GIOI])
def test_ranh_gioi(iso, gio, nhanh, ten, tren_ranh):
    tt = get_tu_tru(iso, gio)
    assert tren_ranh(_chinh_xac(tt, True)), f"lá số không còn nằm trên ranh giới: {ten}"
    kq = v2.tinh(tt)
    assert kq["nhanh"] == nhanh, ten
    if "lạnh = ấm" in ten:
        assert "dieu_hau" not in kq["co"], ten          # «lạnh lấn ấm» phải lấn thật, hoà thì không
    assert v2.kiem_bat_bien(kq, tt) == []


def test_ly_do_ngu_phap():
    """M1: mọi mã khớp ngữ pháp; ký hiệu so sánh của nguyên nhân đúng theo số nguyên."""
    assert not v2.ly_do_hop_le("r=0.4") and not v2.ly_do_hop_le("nguyen_nhan=QS:2.6>>TT:2.6")
    hoa = v2.tinh(get_tu_tru("2005-01-08", 10))["ly_do"]
    assert "nguyen_nhan=QS:2.6=TT:2.6" in hoa                     # hoà ghi "=", không ghi ">"
    assert "nguyen_nhan=TK:2.6=AN:2.6" in v2.tinh(get_tu_tru("2005-06-04", 10))["ly_do"]
    assert v2.tinh(get_tu_tru("2009-06-13", 22))["ly_do"][0] == "r=0.550"
    kq = v2.tinh(TT_MAU[MAU[0]])
    kq["ly_do"] = kq["ly_do"] + ["tu_do"]
    assert any("ly_do" in e for e in v2.kiem_bat_bien(kq))


def test_kiem_bat_bien_doi_chieu_nhat_chu():
    """M3: dòng bảng đúng nhưng dựng từ nhật chủ khác thì bị bắt khi có tứ trụ."""
    tt_a, tt_b = TT_MAU[MAU[0]], None
    kq_a = v2.tinh(tt_a)
    for tt in TT_MAU.values():
        if tt["day"]["can_idx"] % 5 != tt_a["day"]["can_idx"] % 5:
            tt_b = tt
            break
    assert v2.kiem_bat_bien(kq_a) == [] and v2.kiem_bat_bien(kq_a, tt_a) == []
    assert any("nhật chủ" in e for e in v2.kiem_bat_bien(kq_a, tt_b))


# ─── Thiếu giờ: trụ giờ giữ chỗ không được chạm tới đầu ra (vòng sửa 1, yêu cầu 3) ──────────

SLOT = (0, 2, 4, 6, 8, 10, 11, 14, 16, 18, 20, 22, 23)


def test_thieu_gio_khong_phu_thuoc_gio_gia():
    """co_gio=False: đổi trụ giờ giữ chỗ qua đủ 13 khung giờ, MỌI khoá của đầu ra v2 phải đứng yên —
    ở ``tinh``, ở ``find_dung_than(rule=2026-10.1)`` và ở ``build_chart_analysis().dung_than_info``.

    Ở cấp bundle, ``transforms``, ``strength_info``, ``thap_than``, ``stem_transformations`` vẫn là
    v1 bốn trụ và ĐỔI theo giờ giả: đó là trường v1, không thuộc đầu ra luật mới; tách chúng khỏi
    trụ giờ là việc của Task 3 (route nhận ``birth_time = null``). Phép kiểm ghi đúng danh sách ấy."""
    ngay = [iso for iso, h in MAU if h == 2][::4] + [c["ngay"] for c in CA if c["loai"] == "thieu_gio"]
    so_ngay = bo_qua = 0
    bundle_doi = set()
    for iso in ngay:
        bo = {s: get_tu_tru(iso, s) for s in SLOT}
        goc = bo[SLOT[0]]
        cung = {s: tt for s, tt in bo.items() if all(tt[p] == goc[p] for p in TRU[:3])}
        bo_qua += len(bo) - len(cung)            # khung giờ làm đổi trụ năm/tháng/ngày: không phải giờ giả
        assert len(cung) >= 10
        ra = {s: v1.chuoi(v2.tinh(tt, co_gio=False)) for s, tt in cung.items()}
        fd = {s: v1.chuoi(find_dung_than(tt, rule=RULE_V2, co_gio=False)) for s, tt in cung.items()}
        bd = {s: build_chart_analysis(tt, dung_than_rule=RULE_V2, co_gio=False) for s, tt in cung.items()}
        assert len(set(ra.values())) == 1, iso
        assert len(set(fd.values())) == 1, iso
        assert len({v1.chuoi(b["dung_than_info"]) for b in bd.values()}) == 1, iso
        for k in next(iter(bd.values())):
            if k != "dung_than_info" and len({v1.chuoi(json.loads(json.dumps(b[k], default=str)))
                                               for b in bd.values()}) > 1:
                bundle_doi.add(k)
        so_ngay += 1
    assert so_ngay >= 25
    assert bundle_doi <= {"transforms", "strength_info", "thap_than", "stem_transformations"}
    assert "strength_info" in bundle_doi          # v1 bốn trụ thật sự đọc giờ giả: phải thấy nó đổi
