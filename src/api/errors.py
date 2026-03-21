"""
Standardized API error responses with bilingual messages (T3-04).

All error responses include:
  - status: "error"
  - error_code: machine-readable code
  - message: Vietnamese message (backward-compatible)
  - message_en: English translation
"""

from __future__ import annotations

from fastapi.responses import JSONResponse


# ─────────────────────────────────────────────────────────────────────────────
# Bilingual message catalog
# ─────────────────────────────────────────────────────────────────────────────

ERROR_MESSAGES: dict[str, dict[str, str]] = {
    "INVALID_INPUT": {
        "vi": "Dữ liệu không hợp lệ.",
        "en": "Invalid input data.",
    },
    "RANGE_TOO_LARGE": {
        "vi": "Khoảng thời gian vượt quá giới hạn cho phép.",
        "en": "Date range exceeds the allowed limit.",
    },
    "NO_DATES_FOUND": {
        "vi": "Không tìm được ngày tốt nào trong khoảng thời gian đã chọn.",
        "en": "No auspicious dates found in the selected range.",
    },
    "UNAUTHORIZED": {
        "vi": "Không có quyền truy cập.",
        "en": "Unauthorized.",
    },
    "RATE_LIMITED": {
        "vi": "Đã vượt giới hạn truy cập.",
        "en": "Rate limit exceeded.",
    },
    "INTERNAL_ERROR": {
        "vi": "Đã có lỗi xảy ra. Vui lòng thử lại sau.",
        "en": "An internal error occurred. Please try again later.",
    },
}


def error_response(
    status_code: int,
    error_code: str,
    message_vi: str | None = None,
    message_en: str | None = None,
    *,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build a standardized error JSONResponse.

    If message_vi/message_en are not provided, falls back to the catalog.
    The ``message`` field keeps the Vietnamese text for backward compatibility.
    """
    defaults = ERROR_MESSAGES.get(error_code, ERROR_MESSAGES["INTERNAL_ERROR"])
    vi = message_vi or defaults["vi"]
    en = message_en or defaults["en"]

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "error_code": error_code,
            "message": vi,
            "message_en": en,
        },
        headers=headers,
    )
