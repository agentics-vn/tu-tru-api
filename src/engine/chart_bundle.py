"""
chart_bundle.py — Single-pass Tứ Trụ chart analysis (hóa hợp + cường nhược + Thập Thần).

Avoids recomputing detect_stem_transformations() across la_so / tu_tru / dung_than.
"""

from __future__ import annotations

from typing import Any, Optional

from engine.cuong_nhuoc import analyze_chart_strength
from engine.dung_than import find_dung_than
from engine.hoa_hop import build_stem_transformations_payload, detect_stem_transformations
from engine.thap_than import analyze_thap_than


def build_chart_analysis(tu_tru: dict) -> dict[str, Any]:
    """
    Compute transforms, strength, dụng thần, thập thần once per request.

    Returns dict with keys: transforms, strength_info, dung_than_info, thap_than,
    stem_transformations (API payload).
    """
    transforms = detect_stem_transformations(tu_tru)
    strength_info = analyze_chart_strength(tu_tru, transforms)
    dung_than_info = find_dung_than(tu_tru, analysis=strength_info)
    thap_than = analyze_thap_than(tu_tru, transforms)
    stem_payload = build_stem_transformations_payload(tu_tru, transforms)
    return {
        "transforms": transforms,
        "strength_info": strength_info,
        "dung_than_info": dung_than_info,
        "thap_than": thap_than,
        "stem_transformations": stem_payload,
    }
