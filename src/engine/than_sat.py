"""
than_sat.py — Thần sát grouped by pillar for Mệnh Bàn.

Each star resolves to a target Địa Chi computed from the year/day 三合 triad;
a pillar earns the star only when its branch equals that target (no blanket
per-position assignment).

Source: docs/algorithm.md §22.8, docs/seed/than-sat.json
"""

from __future__ import annotations

from engine.seed_loader import load_seed_json

# Order stars appear within a pillar cell
_STAR_ORDER = (
    "thien_at",
    "thien_loc",
    "van_xuong",
    "tuong_tinh",
    "tai_sat",
    "kiep_sat",
    "vong_than",
    "dao_hoa",
    "dich_ma",
)

# Stars keyed off the day stem → target branch(es); each maps star_key → seed key.
_DAY_STEM_STARS: dict[str, str] = {
    "van_xuong": "van_xuong_by_day_stem",
    "thien_at": "thien_at_by_day_stem",
    "thien_loc": "thien_loc_by_day_stem",
}


def _group_for_branch(chi_idx: int, groups: list[dict]) -> dict | None:
    for group in groups:
        if chi_idx in group["branches"]:
            return group
    return None


def _build_target_map(tu_tru: dict, data: dict) -> dict[int, list[str]]:
    """Map target Địa Chi index → list of star keys (deduped, ordered later)."""
    groups: list[dict] = data["san_he_groups"]
    tao_hua: dict[str, int] = data["tao_hua"]
    yi_ma: dict[str, int] = data["yi_ma"]

    year_chi = tu_tru["year"]["chi_idx"]
    day_chi = tu_tru["day"]["chi_idx"]
    yg = _group_for_branch(year_chi, groups)
    dg = _group_for_branch(day_chi, groups)

    targets: dict[int, set[str]] = {}

    def add(chi: int | None, key: str) -> None:
        if chi is None:
            return
        targets.setdefault(chi, set()).add(key)

    # Tướng Tinh (将星): cardinal of year & day triads
    add(yg["jiang_xing"], "tuong_tinh")
    add(dg["jiang_xing"], "tuong_tinh")
    # Tai Sát (災煞): branch clashing the year triad's 将星
    add((yg["jiang_xing"] + 6) % 12, "tai_sat")
    # Kiếp Sát (劫煞): 劫煞 of the day triad
    add(dg["jie_sha"], "kiep_sat")
    # Vong Thần (亡神): 亡神 of the year triad
    add(yg["wang_shen"], "vong_than")
    # Đào Hoa (咸池) & Dịch Mã (驛馬): from both year & day triads
    add(tao_hua[yg["key"]], "dao_hoa")
    add(tao_hua[dg["key"]], "dao_hoa")
    add(yi_ma[yg["key"]], "dich_ma")
    add(yi_ma[dg["key"]], "dich_ma")

    return {chi: keys for chi, keys in targets.items()}


def analyze_than_sat(tu_tru: dict) -> dict[str, list[dict]]:
    data = load_seed_json("than-sat.json")
    stars_meta: dict = data["stars"]
    day_can = tu_tru["day"]["can_idx"]

    target_map = _build_target_map(tu_tru, data)

    # Day-stem stars: star_key → set of target branches for this day master.
    day_stem_targets: dict[str, set[int]] = {}
    for star_key, seed_key in _DAY_STEM_STARS.items():
        table = {int(k): v for k, v in data[seed_key].items()}
        day_stem_targets[star_key] = set(table.get(day_can, []))

    result: dict[str, list[dict]] = {}
    for pillar_key in ("year", "month", "day", "hour"):
        chi_idx = tu_tru[pillar_key]["chi_idx"]
        keys: set[str] = set(target_map.get(chi_idx, set()))
        for star_key, targets in day_stem_targets.items():
            if chi_idx in targets:
                keys.add(star_key)
        stars = [
            {"key": k, "name": stars_meta[k]["name"]}
            for k in _STAR_ORDER
            if k in keys
        ]
        result[pillar_key] = stars
    return result
