#!/usr/bin/env bash
# ─── TaskDog · Start all services ───────────────────────────────────────
# Usage:  bash scripts/start.sh
#
# Starts the 3 services in background, writes PIDs, opens the dashboard.
#          bash scripts/stop.sh   — kills everything
#──────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_DIR/.taskdog_pids"

# ── Prerequisite checks ──────────────────────────────────────────────
check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    echo "❌ $1 not found. Install it first."
    exit 1
  fi
}

PYTHON="$PROJECT_DIR/taskdog-backend/venv/bin/python"
if [ ! -f "$PYTHON" ]; then
  echo "❌ Python venv not found. Run: cd taskdog-backend && python3 -m venv venv && venv/bin/pip install -r requirements.txt"
  exit 1
fi

NODE_MODULES="$PROJECT_DIR/taskdog-frontend/node_modules"
if [ ! -d "$NODE_MODULES" ]; then
  echo "❌ node_modules not found. Run: cd taskdog-frontend && npm install"
  exit 1
fi

# ── Stop any existing services on these ports ────────────────────────
for port in 3001 5173; do
  pids=$(lsof -ti:$port 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "⚠️  Port $port in use (pid $pids). Killing…"
    kill -9 $pids 2>/dev/null || true
    sleep 0.3
  fi
done

# Remove stale PID file
rm -f "$PID_FILE"

echo ""
echo "═══════════════════════════════════════════"
echo "  TaskDog — Starting services"
echo "═══════════════════════════════════════════"
echo ""
echo "  Backend + frontend starting now."
echo "  WhatsApp bridge starts after API key entry."
echo ""

# ── Start Backend ────────────────────────────────────────────────────
echo "→ Starting Flask backend (port 3001)…"
nohup "$PYTHON" "$PROJECT_DIR/taskdog-backend/app.py" > /tmp/taskdog_backend.log 2>&1 &
BACKEND_PID=$!
echo "  PID $BACKEND_PID"
echo "$BACKEND_PID backend" >> "$PID_FILE"

# ── Start Frontend ───────────────────────────────────────────────────
echo "→ Starting Vite frontend (port 5173)…"
(cd "$PROJECT_DIR/taskdog-frontend" && nohup npm run dev) > /tmp/taskdog_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  PID $FRONTEND_PID"
echo "$FRONTEND_PID frontend" >> "$PID_FILE"

# ── Wait for services to come up ─────────────────────────────────────
echo ""
echo "→ Waiting for services…"

wait_for_port() {
  local port=$1 name=$2 timeout=${3:-15}
  local elapsed=0
  while [ $elapsed -lt $timeout ]; do
    if lsof -ti:$port >/dev/null 2>&1; then
      echo "  ✅ $name ready (port $port)"
      return 0
    fi
    sleep 0.5
    elapsed=$((elapsed + 1))
  done
  echo "  ⏳ $name still starting (port $port not open yet — it'll come up shortly)"
  return 1
}

wait_for_port 3001 "Backend"
wait_for_port 5173 "Frontend"

# ── Done ─────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo "  TaskDog started."
echo ""
echo "  Dashboard → http://localhost:5173/"
echo "  Backend   → http://localhost:3001/"
echo ""
echo "  The WhatsApp bridge starts automatically after you enter"
echo "  your Gemini API key (Gate A in the onboarding flow)."
echo ""
echo "  Stop:  bash scripts/stop.sh"
echo "  Reset: bash scripts/reset_first_time.sh"
echo "  Logs:  /tmp/taskdog_*.log"
echo "═══════════════════════════════════════════"
echo ""

# Auto-open browser
if command -v open &>/dev/null; then
  open "http://localhost:5173/"
elif command -v xdg-open &>/dev/null; then
  xdg-open "http://localhost:5173/"
fi