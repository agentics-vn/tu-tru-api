# Lá số Bát Tự — Web UI

Next.js frontend for `POST /v1/la-so-full`.

## Dev

```bash
# Terminal 1 — API
uvicorn src.app:app --reload --port 3000

# Terminal 2 — Web
cd web && npm install && npm run dev
```

Open http://localhost:3001

Optional: `web/.env.local` with `API_URL=http://127.0.0.1:3000` if API is not on port 3000.

## Production deploy (Vercel)

1. Project root directory: **`web/`**
2. Environment variable: **`API_URL`** = production API base URL (no trailing slash), e.g. `https://tu-tru-api.fly.dev`
3. Build: `npm run build` (default Next.js settings)

Browser requests go to `/api/v1/la-so-full`; Next.js rewrites to `$API_URL/v1/la-so-full`.

## Files to commit

Source only — `web/.gitignore` excludes `.next/`, `node_modules/`, and build artifacts.
