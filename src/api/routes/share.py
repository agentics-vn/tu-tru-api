"""
GET /v1/share/{token} — Resolve a shareable result token (T5-01).

Decodes the HMAC-signed token and re-runs the original query, returning
a read-only result without exposing the user's birth data in the URL.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.errors import error_response
from api.share import decode_share_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["share"])


@router.get("/{token}")
async def resolve_share_token(token: str) -> JSONResponse:
    """Decode a share token and replay the original request."""
    payload = decode_share_token(token)
    if payload is None:
        return error_response(
            400, "INVALID_INPUT",
            message_vi="Token không hợp lệ hoặc đã hết hạn.",
            message_en="Invalid or expired share token.",
        )

    endpoint = payload.get("ep", "")
    birth_date = payload.get("bd")
    birth_time = payload.get("bt")
    gender = payload.get("g")

    try:
        if endpoint == "chon-ngay":
            from api.parse_date import parse_dmy
            from calendar_service import get_day_info, get_user_chart
            from engine.hoang_dao import get_gio_hoang_dao
            from filter import apply_layer2_filter
            from scoring import compute_score

            intent = payload.get("in", "MAC_DINH")
            range_start = payload.get("rs")
            range_end = payload.get("re")

            if not all([birth_date, range_start, range_end]):
                return error_response(400, "INVALID_INPUT", message_vi="Token thiếu dữ liệu.")

            # Reuse the chon-ngay engine inline (read-only replay)
            from datetime import date, timedelta
            import json
            from pathlib import Path

            birth_date_str = parse_dmy(birth_date).isoformat()
            gender_str = str(gender) if gender is not None else None
            user_chart = get_user_chart(birth_date_str, birth_time, gender_str)

            rules_path = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "seed" / "intent-rules.json"
            with open(rules_path) as f:
                intent_rules = json.load(f)

            from api.routes.chon_ngay import INTENT_ALIAS
            rule_key = INTENT_ALIAS.get(intent, intent)
            intent_rule = intent_rules.get(rule_key, intent_rules.get("MAC_DINH", {"bonus_sao": [], "forbidden_sao": []}))

            start = parse_dmy(range_start)
            end = parse_dmy(range_end)
            all_dates = []
            cur = start
            while cur <= end:
                all_dates.append(cur)
                cur += timedelta(days=1)

            scored_days = []
            for d in all_dates:
                ds = d.isoformat()
                day_info = get_day_info(ds)
                if not day_info["is_layer1_pass"]:
                    continue
                filter_result = apply_layer2_filter(day_info, user_chart, rule_key)
                if not filter_result["pass"]:
                    continue
                score_result = compute_score(day_info, user_chart, rule_key, intent_rule, filter_result)
                scored_days.append({"day_info": day_info, "score_result": score_result})

            scored_days.sort(key=lambda x: x["score_result"]["score"], reverse=True)
            top_days = scored_days[:3]

            recommended = [
                {
                    "date": d["day_info"]["date"],
                    "score": d["score_result"]["score"],
                    "grade": d["score_result"]["grade"],
                    "summary_vi": d["score_result"]["summary_vi"],
                    "time_slots": [
                        {"chi_name": g["chi_name"], "range": f"{g['start']}-{g['end']}"}
                        for g in get_gio_hoang_dao(d["day_info"]["day_chi_idx"])
                    ],
                }
                for d in top_days
            ]

            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "shared": True,
                    "endpoint": endpoint,
                    "meta": {
                        "intent": intent,
                        "range_scanned": {"from": range_start, "to": range_end},
                        "birth_hash": payload.get("bh", ""),
                    },
                    "recommended_dates": recommended,
                },
            )

        return error_response(
            400, "INVALID_INPUT",
            message_vi=f"Endpoint '{endpoint}' không hỗ trợ chia sẻ.",
            message_en=f"Endpoint '{endpoint}' does not support sharing.",
        )

    except Exception:
        logger.exception("Error resolving share token")
        return error_response(500, "INTERNAL_ERROR")
