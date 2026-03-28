"""
Bat Tu Date Selection API — FastAPI application entry point.

Start:
    uvicorn src.app:app --reload --port 3000

Or run directly:
    python src/app.py
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.errors import error_response

# ─────────────────────────────────────────────────────────────────────────────
# Sentry — error tracking (no-op when SENTRY_DSN is unset)
# ─────────────────────────────────────────────────────────────────────────────

_sentry_dsn = os.environ.get("SENTRY_DSN", "")
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
    )
from api.routes.chon_ngay import router as chon_ngay_router
from api.routes.ngay_hom_nay import router as ngay_hom_nay_router
from api.routes.lich_thang import router as lich_thang_router
from api.routes.tieu_van import router as tieu_van_router
from api.routes.tu_tru import router as tu_tru_router
from api.routes.la_so import router as la_so_router
from api.routes.hop_tuoi import router as hop_tuoi_router
from api.routes.phong_thuy import router as phong_thuy_router
from api.routes.day_detail import router as day_detail_router
from api.routes.convert_date import router as convert_date_router
from api.routes.share import router as share_router
from api.routes.profile import router as profile_router
from api.routes.weekly_summary import router as weekly_summary_router

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("bat_tu_api")


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan (startup / shutdown hooks)
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting Bat Tu API")
    yield
    logger.info("Shutting down Bat Tu API")


# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="API Chọn Ngày Bát Tự",
    version="0.1.0",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────────────────────

# CORS — allow configured origins (default: all for dev, restrict in production)
_cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Exception handlers
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Map Pydantic / FastAPI validation errors to the API error contract."""
    errors = exc.errors()
    first = errors[0] if errors else {}
    msg = first.get("msg", "Dữ liệu không hợp lệ")
    field = " → ".join(str(loc) for loc in first.get("loc", []))

    # Detect RANGE_TOO_LARGE from our model_validator message
    if ("within" in msg and "days" in msg) or ("vượt quá" in msg and "ngày" in msg):
        return error_response(400, "RANGE_TOO_LARGE", message_vi=msg)

    detail_vi = f"{field}: {msg}" if field else msg
    return error_response(400, "INVALID_INPUT", message_vi=detail_vi)


@app.exception_handler(Exception)
async def generic_exception_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return error_response(500, "INTERNAL_ERROR")


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(chon_ngay_router, prefix="/v1/chon-ngay")
app.include_router(ngay_hom_nay_router, prefix="/v1/ngay-hom-nay")
app.include_router(lich_thang_router, prefix="/v1/lich-thang")
app.include_router(tieu_van_router, prefix="/v1/tieu-van")
app.include_router(tu_tru_router, prefix="/v1/tu-tru")
app.include_router(la_so_router, prefix="/v1/la-so")
app.include_router(hop_tuoi_router, prefix="/v1/hop-tuoi")
app.include_router(phong_thuy_router, prefix="/v1/phong-thuy")
app.include_router(day_detail_router, prefix="/v1/day-detail")
app.include_router(convert_date_router, prefix="/v1/convert-date")
app.include_router(share_router, prefix="/v1/share")
app.include_router(profile_router, prefix="/v1/profile")
app.include_router(weekly_summary_router, prefix="/v1/weekly-summary")


# ─────────────────────────────────────────────────────────────────────────────
# Run directly
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
