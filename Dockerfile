# ── Stage 1: Next.js build ───────────────────────────────────────────────────
FROM node:20-slim AS web-builder

WORKDIR /web

COPY web/package.json web/package-lock.json ./
RUN npm ci

COPY web/ ./

# Baked into rewrites at build time — API listens on loopback in combined runtime.
ARG API_URL=http://127.0.0.1:3001
ENV API_URL=${API_URL}
RUN npm run build

# ── Stage 2: Python dependencies ───────────────────────────────────────────
FROM python:3.11-slim AS py-builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# ── Stage 3: runtime (API + Next on one machine) ─────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Node binary for Next standalone (no apt nodesource — copy from web-builder).
COPY --from=web-builder /usr/local/bin/node /usr/local/bin/node

COPY --from=py-builder /app/.venv /app/.venv
COPY src/ ./src/
COPY docs/seed/ ./docs/seed/
COPY pyproject.toml ./pyproject.toml

COPY --from=web-builder /web/.next/standalone ./web/
COPY --from=web-builder /web/.next/static ./web/.next/static

COPY scripts/fly-start-combined.sh /app/fly-start-combined.sh
RUN chmod +x /app/fly-start-combined.sh

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/src
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
ENV API_INTERNAL_PORT=3001

EXPOSE 3000

CMD ["/app/fly-start-combined.sh"]
