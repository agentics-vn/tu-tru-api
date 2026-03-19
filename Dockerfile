# ── Stage 1: install dependencies ────────────────────────────────────────────
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install only dependencies (cached layer — re-runs only when lock changes)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# ── Stage 2: runtime (no uv) ────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code and static data
COPY src/ ./src/
COPY docs/seed/ ./docs/seed/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
