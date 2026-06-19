#!/bin/sh
# Start API (loopback) + Next.js (public) on one Fly machine for testing.
set -e

API_PORT="${API_INTERNAL_PORT:-3001}"
WEB_PORT="${PORT:-3000}"

uvicorn app:app --host 127.0.0.1 --port "$API_PORT" &
UVICORN_PID=$!

NODE_PID=""

cleanup() {
  if [ -n "$NODE_PID" ]; then
    kill "$NODE_PID" 2>/dev/null || true
  fi
  kill "$UVICORN_PID" 2>/dev/null || true
}
trap cleanup INT TERM

# Avoid proxy 502s while uvicorn is still starting (Fly health check too).
for _ in $(seq 1 30); do
  if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${API_PORT}/health')" 2>/dev/null; then
    break
  fi
  sleep 1
done

cd /app/web
export PORT="$WEB_PORT"
export HOSTNAME="${HOSTNAME:-0.0.0.0}"
node server.js &
NODE_PID=$!

wait "$NODE_PID"
EXIT=$?
cleanup
exit "$EXIT"
