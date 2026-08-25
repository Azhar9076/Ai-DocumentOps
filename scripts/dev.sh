#!/usr/bin/env bash
# Start the API and the Vite dev server together.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cleanup() {
  kill 0 2>/dev/null || true
}
trap cleanup EXIT

"$ROOT/backend/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --app-dir "$ROOT/backend" &
npm --prefix "$ROOT/frontend" run dev -- --host 0.0.0.0 --port 5173 &

wait
