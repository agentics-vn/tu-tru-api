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
from api.intent_rules_loader import resolve_intent_key
from api.parse_date import parse_dmy
from api.routes.chon_ngay import run_chon_ngay_scan
from api.schemas.direction_c import (
    API_ERROR_RESPONSES,
    ShareChonNgayResponse,
    validate_chon_ngay_response,
)
from api.share import decode_share_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["share"])


@router.get(
    "/{token}",
    response_model=ShareChonNgayResponse,
    responses=API_ERROR_RESPONSES,
    summary="Giải mã share token và replay kết quả chon-ngay",
)
async def resolve_share_token(token: str):
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
            intent = payload.get("in", "MAC_DINH")
            range_start = payload.get("rs")
            range_end = payload.get("re")

            if not all([birth_date, range_start, range_end]):
                return error_response(400, "INVALID_INPUT", message_vi="Token thiếu dữ liệu.")

            resolve_intent_key(intent)
            gender_val = int(gender) if gender is not None else None

            content = run_chon_ngay_scan(
                birth_date_iso=parse_dmy(birth_date).isoformat(),
                birth_time=birth_time,
                gender=gender_val,
                intent=intent,
                range_start_dmy=range_start,
                range_end_dmy=range_end,
                top_n=3,
            )
            content["meta"]["birth_hash"] = payload.get("bh", "")
            validated = validate_chon_ngay_response(content)
            return ShareChonNgayResponse.model_validate({
                **validated.model_dump(),
                "shared": True,
                "endpoint": endpoint,
            })

        return error_response(
            400, "INVALID_INPUT",
            message_vi=f"Endpoint '{endpoint}' không hỗ trợ chia sẻ.",
            message_en=f"Endpoint '{endpoint}' does not support sharing.",
        )

    except Exception:
        logger.exception("Error resolving share token")
        return error_response(500, "INTERNAL_ERROR")
