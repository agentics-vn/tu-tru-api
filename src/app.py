"""
Bat Tu Date Selection API — FastAPI application entry point.

Start:
    uvicorn src.app:app --reload --port 3000

Or run directly:
    python src/app.py
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.routes.chon_ngay import router as chon_ngay_router
from api.routes.ngay_hom_nay import router as ngay_hom_nay_router
from api.routes.lich_thang import router as lich_thang_router
from api.routes.tieu_van import router as tieu_van_router

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
    title="Bat Tu Date Selection API",
    version="0.1.0",
    lifespan=lifespan,
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
    msg = first.get("msg", "Invalid input")
    field = " → ".join(str(loc) for loc in first.get("loc", []))

    # Detect RANGE_TOO_LARGE from our model_validator message
    if "within" in msg and "days" in msg:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "error_code": "RANGE_TOO_LARGE",
                "message": msg,
            },
        )

    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "error_code": "INVALID_INPUT",
            "message": f"{field}: {msg}" if field else msg,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": "INTERNAL_ERROR",
            "message": "Đã có lỗi xảy ra. Vui lòng thử lại sau.",
        },
    )


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


# ─────────────────────────────────────────────────────────────────────────────
# Run directly
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
