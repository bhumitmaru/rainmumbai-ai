#!/bin/bash
# RainMumbai AI — double-click launcher for macOS.
# Starts the FastAPI backend and the React frontend, then opens the dashboard.

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT" || exit 1

# Use a project-local npm cache so a broken/root-owned ~/.npm never blocks startup.
export npm_config_cache="$ROOT/.npm-cache"

echo ""
echo "══════════════════════════════════════════════"
echo "   RainMumbai AI"
echo "══════════════════════════════════════════════"
echo ""

# ── 1. Locate Python 3.11+ ──────────────────────
PYTHON=""
for c in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$c" >/dev/null 2>&1 \
     && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PYTHON="$c"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "✗ Python 3.11+ was not found."
  echo "  Install it from https://www.python.org or run: brew install python"
  read -r -n 1 -s -p "Press any key to close…"
  echo ""
  exit 1
fi
echo "✓ Python: $($PYTHON --version 2>&1)"

# ── 2. Backend: virtualenv + dependencies ───────
if [ ! -x ".venv/bin/uvicorn" ]; then
  echo "→ Setting up backend (first run only)…"
  "$PYTHON" -m venv .venv || { echo "✗ Could not create the virtual environment."; exit 1; }
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install -r backend/requirements.txt || {
    echo "✗ Backend dependency installation failed. See the error above."
    read -r -n 1 -s -p "Press any key to close…"
    echo ""
    exit 1
  }
fi
echo "✓ Backend ready"

# ── 3. Frontend: Node + dependencies ────────────
if ! command -v node >/dev/null 2>&1; then
  echo "✗ Node.js was not found."
  echo "  Install it from https://nodejs.org or run: brew install node"
  read -r -n 1 -s -p "Press any key to close…"
  echo ""
  exit 1
fi
if [ ! -d "frontend/node_modules" ]; then
  echo "→ Installing frontend dependencies (first run only)…"
  (cd frontend && npm install) || {
    echo "✗ Frontend dependency installation failed. See the error above."
    read -r -n 1 -s -p "Press any key to close…"
    echo ""
    exit 1
  }
fi
echo "✓ Frontend ready"

# ── 4. Start the services ───────────────────────
echo ""
echo "→ Starting backend  on http://localhost:8000 …"
.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "→ Starting frontend on http://localhost:5173 …"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

cleanup() {
  echo ""
  echo "Stopping RainMumbai AI…"
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
}
trap cleanup INT TERM

# ── 5. Open the dashboard once the frontend is up ──
for _ in $(seq 1 30); do
  if curl -s http://localhost:5173 >/dev/null 2>&1; then break; fi
  sleep 1
done
open "http://localhost:5173" 2>/dev/null || true

echo ""
echo "──────────────────────────────────────────────"
echo "  RainMumbai AI is running"
echo "    Frontend  http://localhost:5173"
echo "    Backend   http://localhost:8000   (docs: /docs)"
echo "    Admin     admin@rainmumbai.ai  /  change-me-admin"
echo ""
echo "  Press Ctrl+C (or close this window) to stop."
echo "──────────────────────────────────────────────"
echo ""

wait "$BACKEND_PID" "$FRONTEND_PID"
