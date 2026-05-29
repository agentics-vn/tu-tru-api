"""
POST /v1/profile — Server-side hashed birth profile (T5-03).

Stores birth data keyed by a SHA-256 hash so the user doesn't need to
re-enter it on every request.  Other endpoints accept an optional
``profile_id`` query param to look up saved data.

Storage: Redis when `REDIS_URL` is reachable; otherwise in-memory (cleared on restart).
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.errors import error_response
from api.parse_date import parse_dmy

logger = logging.getLogger(__name__)

router = APIRouter(tags=["profile"])

from api.profile_store import get_profile, memory_profile_count, save_profile


def _make_profile_id(birth_date: str, birth_time: int | None, gender: int | None) -> str:
    raw = f"{birth_date}|{birth_time}|{gender}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


# ─────────────────────────────────────────────────────────────────────────────
# POST /v1/profile — Save birth profile
# ─────────────────────────────────────────────────────────────────────────────

@router.post("")
@router.post("/", include_in_schema=False)
async def save_profile(
    birth_date: str = Query(..., description="Ngày sinh dd/mm/yyyy"),
    birth_time: Optional[int] = Query(None, description="Giờ sinh"),
    gender: Optional[int] = Query(None, description="Giới tính: 1 (nam) hoặc -1 (nữ)"),
) -> JSONResponse:
    try:
        bd = parse_dmy(birth_date)
        profile_id = _make_profile_id(birth_date, birth_time, gender)

        from cache.redis import get_redis_client

        if (
            get_profile(profile_id) is None
            and get_redis_client() is None
            and memory_profile_count() >= 10_000
        ):
            return error_response(
                503, "INTERNAL_ERROR",
                message_vi="Kho hồ sơ tạm thời đầy. Vui lòng thử lại sau.",
                message_en="Profile store is temporarily full. Please try again later.",
            )

        save_profile(profile_id, {
            "birth_date": birth_date,
            "birth_time": birth_time,
            "gender": gender,
        })

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "profile_id": profile_id,
                "message": "Hồ sơ đã được lưu.",
                "message_en": "Profile saved.",
            },
        )
    except ValueError as e:
        return error_response(400, "INVALID_INPUT", message_vi=str(e))
    except Exception:
        logger.exception("Internal error in save_profile")
        return error_response(500, "INTERNAL_ERROR")


# ─────────────────────────────────────────────────────────────────────────────
# GET /v1/profile/{profile_id} — Retrieve birth profile
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{profile_id}")
async def get_profile_endpoint(profile_id: str) -> JSONResponse:
    profile = get_profile(profile_id)
    if profile is None:
        return error_response(
            404, "INVALID_INPUT",
            message_vi="Không tìm thấy hồ sơ.",
            message_en="Profile not found.",
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "profile_id": profile_id,
            "birth_date": profile["birth_date"],
            "birth_time": profile["birth_time"],
            "gender": profile["gender"],
        },
    )
