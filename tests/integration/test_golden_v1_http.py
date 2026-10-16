"""Golden v1 qua HTTP: lời gọi không yêu cầu luật mới phải trả y hệt `main` 88b7a66.

Dữ liệu và cách chuẩn hoá: xem ``tests/golden/v1.py``. So từng byte của JSON
chính tắc (``sort_keys``, không khoảng trắng) sau khi bỏ ``computed_at`` và
``meta.share_token``.
"""

from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path

import pytest

from tests.golden import v1

DATA = json.loads(v1.FILE_HTTP.read_text(encoding="utf-8"))
CASES = DATA["cases"]
SIX_ROUTES = {"/v1/la-so-full", "/v1/la-so", "/v1/la-so/luu-nien", "/v1/hop-tuoi",
              "/v1/phong-thuy", "/v1/chon-ngay"}


@pytest.fixture(scope="module")
def client():
    return v1.app_client()


@pytest.fixture
def frozen(monkeypatch):
    v1.dong_bang(monkeypatch.setattr)


def test_golden_contract():
    # Mẫu số: đọc nó, đừng chỉ đọc dòng xanh.
    assert len(CASES) == 88
    assert DATA["ngay_dong_bang"] == v1.NGAY_DONG_BANG
    assert DATA["bo_khi_chuan_hoa"] == ["computed_at", "meta.share_token"]
    assert set(Counter(c["path"] for c in CASES)) == SIX_ROUTES
    assert [{k: c[k] for k in ("id", "method", "path", "params", "json")} for c in CASES] \
        == v1.tao_yeu_cau()
    statuses = Counter(c["ket_qua"]["status"] for c in CASES)
    assert statuses == {200: 88}


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_golden_v1_http(client, frozen, case):
    actual = v1.goi(client, case)
    assert actual["status"] == case["ket_qua"]["status"]
    assert v1.chuoi(actual["body"]) == v1.chuoi(case["ket_qua"]["body"])


def _clock_reads() -> set[tuple[str, str]]:
    src = Path(v1.ROOT / "src")
    found = set()
    for path in src.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("today", "now")):
                found.add((str(path.relative_to(src)), node.func.attr))
    return found


def test_clock_reads_are_all_frozen():
    """Một chỗ đọc đồng hồ mới mà `dong_bang` không biết = golden sẽ trôi theo ngày."""
    assert _clock_reads() == {
        ("api/tz.py", "now"),                 # today_in_tz → đóng băng
        ("api/version.py", "now"),            # utc_now_iso → computed_at, bị bỏ khi chuẩn hoá
        ("api/routes/la_so.py", "today"),
        ("api/routes/la_so_luu_nien.py", "today"),
        ("api/routes/la_so_full.py", "today"),
        ("api/routes/tu_tru.py", "today"),
        ("api/routes/hop_tuoi.py", "today"),
        ("engine/dai_van.py", "today"),
    }
