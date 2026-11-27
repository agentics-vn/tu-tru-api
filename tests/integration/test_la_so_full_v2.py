"""POST /v1/la-so-full nhận ``dung_than_rule`` và ``co_gio`` (kế hoạch Task 3, câu chốt 19/10/2026).

Ba điều canh ở đây:

1. **Hợp đồng v1 không đổi.** Lời gọi không mang hai trường mới đã do golden
   ``tests/golden/v1_http.json`` canh (``test_golden_v1_http``). Ở đây thêm: gửi tường minh
   ``dung_than_rule="v1"``, ``co_gio=true`` cũng ra đúng golden từng byte (dạng chính tắc).
2. **Thiếu giờ, mức phản hồi HTTP.** ``co_gio=false`` thì ``birth_time`` chỉ là giữ chỗ: đổi nó
   qua đủ 13 khung giờ, TOÀN BỘ thân phản hồi (sau chuẩn hoá golden: bỏ ``computed_at``) phải
   giống hệt, không trừ trường nào. Trường nào khác v1 thì phải nằm trong hợp đồng
   ``THIEU_GIO_MENH_BAN`` / ``THIEU_GIO_GOC``; trường ``ba_tru``/``theo_ngay`` được tính lại và đối
   chiếu bằng đường riêng; nguồn ``hanh_thieu`` của sản phẩm (``ngu_hanh``) là ba trụ.
3. **Đầu vào sai trên đường mới trả 422, không 500.** "Đường mới" = thân yêu cầu có khoá
   ``dung_than_rule`` hoặc ``co_gio``. Lời gọi không có hai khoá ấy giữ nguyên mã lỗi cũ (400).
"""

from __future__ import annotations

import copy
import json
from fractions import Fraction

import pytest

from api.routes.la_so_full import THIEU_GIO_GOC
from engine.chart_bundle import THIEU_GIO_MENH_BAN
from engine.hoa_hop import detect_stem_transformations, effective_stem_hanh
from engine.pillars import get_tu_tru
from engine.tiet_khi_meta import get_tiet_khi_at_date
from tests.golden import v1
from tests.unit.test_dung_than_v2 import KHOA_81, _chinh_xac

PATH = "/v1/la-so-full"
RULE_V2 = "2026-10.1"
DATA = json.loads(v1.FILE_HTTP.read_text(encoding="utf-8"))
FULL_OK = [c for c in DATA["cases"] if c["path"] == PATH and not c["id"].startswith("err-")]
FULL_LOI = [c for c in DATA["cases"] if c["path"] == PATH and c["id"].startswith("err-")]

# Ngày đo thiếu giờ: mọi ngày sinh của golden (giờ 0/23, 29/02, quanh Lập Xuân, 1901…) cộng sáu
# ngày có tiết bắt đầu trong ngày hoặc có cặp hợp hoá ngày–giờ; cả hai giới ở sáu ngày thêm.
# `test_thieu_gio_khong_suong` đòi tập này thật sự chạm đủ các nhánh đọc giờ của v1.
THEM = ["06/01/2015", "08/10/2020", "07/12/1995", "05/04/2010", "22/12/2023", "23/10/2024"]
NGAY = [(bd, g) for bd, _bt, g, _ in v1.HS] + [(bd, g) for bd in THEM for g in (1, -1)]


@pytest.fixture(scope="module")
def client():
    return v1.app_client()


@pytest.fixture
def frozen(monkeypatch):
    v1.dong_bang(monkeypatch.setattr)


def _goi(client, body):
    r = client.post(PATH, json=body)
    return r.status_code, v1.chuan_hoa(r.json()) if r.headers["content-type"].startswith(
        "application/json") else r.text


def _than(bd, slot, g, **them):
    return {"birth_date": bd, "birth_time": slot, "gender": g, "num_dai_van": 10,
            "num_luu_nien": 20, **them}


def _iso(bd: str) -> str:
    d, m, y = bd.split("/")
    return f"{y}-{int(m):02d}-{int(d):02d}"


def _la(x, p=(), out=None):
    """Thân phản hồi → {đường (tuple): giá trị lá}; danh sách đánh chỉ số, kèm độ dài."""
    out = {} if out is None else out
    if isinstance(x, dict) and x:
        for k, v in x.items():
            _la(v, p + (k,), out)
    elif isinstance(x, list) and x:
        out[p + ("#len",)] = len(x)
        for i, v in enumerate(x):
            _la(v, p + (i,), out)
    else:
        out[p] = x
    return out


def _lay(x, duong: str):
    for k in duong.split("."):
        x = x[k]
    return x


def _thuoc_hop_dong(duong: tuple) -> bool:
    if duong[0] in THIEU_GIO_GOC:
        return True
    if duong[0] != "menh_ban":
        return False
    con = duong[1:]
    return any(tuple(k.split(".")) == con[:len(k.split("."))] for k in THIEU_GIO_MENH_BAN)


# ─── 1. Hợp đồng v1 ────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("case", FULL_OK, ids=[c["id"] for c in FULL_OK])
def test_khong_tham_so_y_het(client, frozen, case):
    """Gửi tường minh dung_than_rule="v1", co_gio=true: bằng golden từng byte."""
    st, body = _goi(client, {**case["json"], "dung_than_rule": "v1", "co_gio": True})
    assert st == case["ket_qua"]["status"] == 200
    assert v1.chuoi(body) == v1.chuoi(case["ket_qua"]["body"])


def test_mau_so_hop_dong_v1():
    assert len(FULL_OK) == 26 and len(FULL_LOI) == 5
    assert all("dung_than_rule" not in c["json"] and "co_gio" not in c["json"] for c in DATA["cases"]
               if c["json"])


# ─── 2. Luật mới, có giờ: chỉ dung_than_info khác v1 ──────────────────────────────────────

@pytest.mark.parametrize("case", FULL_OK, ids=[c["id"] for c in FULL_OK])
def test_v2_du_truong(client, frozen, case):
    st, body = _goi(client, {**case["json"], "dung_than_rule": RULE_V2})
    assert st == 200
    dti = body["menh_ban"]["chart_analysis"]["dung_than_info"]
    assert KHOA_81 | {"strength", "analysis"} == set(dti)
    assert dti["rule_version"] == RULE_V2 and dti["co"]["thieu_gio"] is False
    assert dti["strength"] == dti["cuong_nhuoc"] and dti["analysis"] is not None
    ky = copy.deepcopy(case["ket_qua"]["body"])
    ky["menh_ban"]["chart_analysis"]["dung_than_info"] = dti
    assert v1.chuoi(body) == v1.chuoi(ky)            # mọi trường khác: đúng v1 từng byte


# ─── 3. Luật mới, thiếu giờ ────────────────────────────────────────────────────────────────

def _thieu_gio(client, bd, slot, g, **them):
    st, body = _goi(client, _than(bd, slot, g, dung_than_rule=RULE_V2, co_gio=False, **them))
    assert st == 200, body
    return body


def test_co_gio_false(client, frozen):
    body = _thieu_gio(client, "06/05/1994", 8, 1)
    dti = body["menh_ban"]["chart_analysis"]["dung_than_info"]
    assert dti["co"]["thieu_gio"] is True and dti["analysis"] is None
    assert "thieu_gio" in dti["ly_do"]
    assert not any("hour" in m or "giờ" in m for m in dti["ly_do"])      # không mã nào của trụ giờ
    assert body["birth_time"] is None and body["html"] is None
    assert body["menh_ban"]["pillars"]["hour"] is None


@pytest.mark.parametrize("bd,g", NGAY, ids=[f"{bd}-{g}" for bd, g in NGAY])
def test_thieu_gio_bat_bien_13_khung(client, frozen, bd, g):
    """Đổi birth_time giữ chỗ qua 13 khung: thân chuẩn hoá giống hệt, không trừ trường nào."""
    ra = {s: v1.chuoi(_thieu_gio(client, bd, s, g)) for s in v1.SLOTS}
    assert len(set(ra.values())) == 1, bd
    # Phép kiểm không xanh suông: cùng ngày, v1 và v2 có giờ thì thân ĐỔI theo giờ.
    assert len({v1.chuoi(_goi(client, _than(bd, s, g))[1]) for s in v1.SLOTS}) == 13
    assert len({v1.chuoi(_goi(client, _than(bd, s, g, dung_than_rule=RULE_V2))[1])
                for s in v1.SLOTS}) == 13


def test_thieu_gio_xem_nam_va_so_van(client, frozen):
    """Các tham số hiển thị khác (view_year, số vận) không mở lại đường đọc giờ."""
    for them in ({"view_year": 2026}, {"num_dai_van": 8, "num_luu_nien": 12, "view_year": 2025},
                 {"name": "Lê Minh Anh"}):
        ra = {v1.chuoi(_thieu_gio(client, "29/02/2000", s, -1, **them)) for s in v1.SLOTS}
        assert len(ra) == 1, them


@pytest.mark.parametrize("bd,g", NGAY, ids=[f"{bd}-{g}" for bd, g in NGAY])
def test_thieu_gio_khac_v1_dung_hop_dong(client, frozen, bd, g):
    """Khác v1 (cùng giờ giữ chỗ) chỉ ở đường trong hợp đồng; trường `null` là null; trường tính lại
    khớp phép tính riêng; mọi trường còn lại đúng v1 từng giá trị."""
    iso = _iso(bd)
    tt = get_tu_tru(iso, 8)
    moi = _thieu_gio(client, bd, 8, g)
    cu = _goi(client, _than(bd, 8, g))[1]
    a, b = _la(cu), _la(moi)
    lech = {p for p in set(a) | set(b) if a.get(p, "∅") != b.get(p, "∅")}
    assert all(_thuoc_hop_dong(p) for p in lech), sorted(p for p in lech if not _thuoc_hop_dong(p))

    for k, cach in THIEU_GIO_GOC.items():
        assert cach == "null" and moi[k] is None
    mb, mb1 = moi["menh_ban"], cu["menh_ban"]
    for k, cach in THIEU_GIO_MENH_BAN.items():
        if cach == "null":
            assert _lay(mb, k) is None, k

    # ba_tru: tính lại trên năm–tháng–ngày, đối chiếu bằng đường riêng.
    x = _chinh_xac(tt, False)
    ba = {h: float(x["L"][h]) for h in ("Kim", "Mộc", "Thủy", "Hỏa", "Thổ")}
    assert mb["ngu_hanh"] == ba and mb["element_counts"] == ba
    assert list(mb["ngu_hanh"]) == list(mb1["ngu_hanh"])               # cùng thứ tự khoá v1
    hh = [t for t in detect_stem_transformations(tt) if "hour" not in (t["pillar_a"], t["pillar_b"])]
    st_ba = [e for e in mb1["stem_transformations"] if "hour" not in e["pillars"]]
    assert mb["stem_transformations"] == st_ba == mb["chart_analysis"]["stem_transformations"]
    assert len(st_ba) == len(hh)
    assert mb["tu_tru_display"] == " | ".join(mb1["tu_tru_display"].split(" | ")[:3])
    for p in ("year", "month", "day"):
        eh, da = effective_stem_hanh(p, tt[p]["can_idx"], hh)
        ky = {**mb1["pillars"][p]["can"], "effective_hanh": eh, "transformed": da}
        assert mb["pillars"][p]["can"] == ky, p
    dti = mb["chart_analysis"]["dung_than_info"]
    assert dti["co"]["thieu_gio"] is True and set(dti) == KHOA_81 | {"strength", "analysis"}
    assert dti["co"]["ty_le"] == float(int(x["r"] * 1000 + Fraction(1, 2))) / 1000

    # theo_ngay: chế độ không giờ sẵn có của engine (cùng kinh độ Mặt Trời với trụ tháng).
    y, m, d = map(int, iso.split("-"))
    assert mb["header"]["tiet_khi"] == get_tiet_khi_at_date(y, m, d)
    assert mb["header"]["duong_lich_display"] == f"{d}/{m}/{y} (GMT+7)"


def test_thieu_gio_khong_suong(client, frozen):
    """Mẫu số: tập ngày đo phải chạm mọi nhánh đọc giờ của v1, và mọi dòng hợp đồng phải khác v1 ở ít
    nhất một ngày (dòng hợp đồng không bao giờ khác v1 là dòng thừa, hoặc tập ngày nghèo)."""
    da_khac = set()
    for bd, g in NGAY:
        cu = {s: _goi(client, _than(bd, s, g))[1] for s in v1.SLOTS}
        moi = _thieu_gio(client, bd, 8, g)
        for s, c in cu.items():
            a, b = _la(c), _la(moi)
            for p in set(a) | set(b):
                if a.get(p, "∅") != b.get(p, "∅"):
                    da_khac.add(p)
    phu = {k for k in THIEU_GIO_GOC if any(p[0] == k for p in da_khac)}
    phu |= {k for k in THIEU_GIO_MENH_BAN
            if any(p[0] == "menh_ban" and p[1:1 + len(k.split("."))] == tuple(k.split(".")) for p in da_khac)}
    assert phu == set(THIEU_GIO_GOC) | set(THIEU_GIO_MENH_BAN), \
        sorted(set(THIEU_GIO_GOC) | set(THIEU_GIO_MENH_BAN) - phu)
    assert len(NGAY) == 36


def test_hanh_thieu_ba_tru(client, frozen):
    """Nguồn `hanh_thieu` của sản phẩm (`hoso_con._hanh_cuc`: min trên `ngu_hanh`) là ba trụ: cùng
    một hành ở mọi khung giờ giữ chỗ, và là hành có L ba trụ nhỏ nhất (hoà: khoá đứng trước)."""
    doi = 0
    for bd, g in NGAY:
        tt = get_tu_tru(_iso(bd), 8)
        x = _chinh_xac(tt, False)
        thieu = {min(nh, key=nh.get) for nh in
                 (_thieu_gio(client, bd, s, g)["menh_ban"]["ngu_hanh"] for s in v1.SLOTS)}
        ky = min(("Kim", "Mộc", "Thủy", "Hỏa", "Thổ"), key=lambda h: x["L"][h])
        assert thieu == {ky}, bd
        bon = {min(nh, key=nh.get) for nh in
               (_goi(client, _than(bd, s, g))[1]["menh_ban"]["ngu_hanh"] for s in v1.SLOTS)}
        doi += bon != {ky}
    assert doi > 0           # ở v1 bốn trụ, hành thiếu thật sự đổi theo giờ giả ở một số ngày


# ─── 4. Đầu vào sai ───────────────────────────────────────────────────────────────────────

GOC = {"birth_date": "06/05/1994", "birth_time": 8, "gender": 1}
SAI_422 = [
    ("rule-la", {"dung_than_rule": "x"}),
    ("rule-null", {"dung_than_rule": None}),
    ("rule-so", {"dung_than_rule": 1}),
    ("rule-hoa", {"dung_than_rule": "V1"}),
    ("co-gio-chuoi", {"dung_than_rule": RULE_V2, "co_gio": "false"}),
    ("co-gio-so", {"dung_than_rule": RULE_V2, "co_gio": 0}),
    ("co-gio-null", {"dung_than_rule": RULE_V2, "co_gio": None}),
    ("v1-thieu-gio", {"dung_than_rule": "v1", "co_gio": False}),
    ("mac-dinh-thieu-gio", {"co_gio": False}),
    ("html-thieu-gio", {"dung_than_rule": RULE_V2, "co_gio": False, "format": "html"}),
    ("v2-ngay-sai", {"dung_than_rule": RULE_V2, "birth_date": "31/02/2020"}),
    ("v2-gio-sai", {"dung_than_rule": RULE_V2, "co_gio": False, "birth_time": 7}),
    ("v2-thieu-birth-time", {"dung_than_rule": RULE_V2, "co_gio": False, "birth_time": None}),
    ("v1-tuong-minh-gioi-sai", {"dung_than_rule": "v1", "gender": 0}),
]


@pytest.mark.parametrize("ten,them", SAI_422, ids=[t for t, _ in SAI_422])
def test_rule_la(client, frozen, ten, them):
    body = {**GOC, **them}
    body = {k: v for k, v in body.items() if not (k == "birth_time" and v is None)}
    r = client.post(PATH, json=body)
    assert r.status_code == 422, (ten, r.status_code, r.text)
    j = r.json()
    assert j["status"] == "error" and j["error_code"] == "INVALID_INPUT" and j["message"]


@pytest.mark.parametrize("case", FULL_LOI, ids=[c["id"] for c in FULL_LOI])
def test_loi_v1_giu_ma_cu(client, frozen, case):
    """Lời gọi lỗi KHÔNG có trường mới: đúng golden từng byte, kể cả mã 400."""
    st, body = _goi(client, case["json"])
    assert (st, v1.chuoi(body)) == (case["ket_qua"]["status"], v1.chuoi(case["ket_qua"]["body"]))
    assert st == 400
