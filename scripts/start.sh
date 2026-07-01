#!/usr/bin/env bash
# ─── Mosaic · Start all services ─────────────────────────────────────────
# Usage:  bash scripts/start.sh
#
# Starts bridge, backend, and frontend. Prints logs if something fails.
#          bash scripts/stop.sh   — kills everything
#──────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_DIR/.mosaic_pids"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail_msg() { echo -e "  ${RED}✗${NC} $1"; }

# ── Prerequisite checks ──────────────────────────────────────────────
PYTHON="$PROJECT_DIR/taskdog-backend/venv/bin/python"
BRIDGE_BIN="$PROJECT_DIR/whatsapp-mcp/whatsapp-bridge/wa-bridge"
NODE_MODULES="$PROJECT_DIR/taskdog-frontend/node_modules"

if [ ! -f "$PYTHON" ]; then
  echo "❌ Python venv not found."
  echo "   Run:  bash install.sh"
  exit 1
fi

if [ ! -d "$NODE_MODULES" ]; then
  echo "❌ node_modules not found."
  echo "   Run:  bash install.sh"
  exit 1
fi

if [ ! -f "$BRIDGE_BIN" ]; then
  echo "❌ Go bridge binary not found."
  echo "   Run:  bash install.sh"
  exit 1
fi

# ── Kill existing services on our ports ──────────────────────────────
for port in 3001 5173 8080; do
  pids=$(lsof -ti:$port 2>/dev/null || true)
  if [ -n "$pids" ]; then
    for pid in $pids; do
      kill -9 "$pid" 2>/dev/null || true
    done
  fi
done
sleep 0.5

rm -f "$PID_FILE"

echo ""
echo -e "${BOLD}═══════════════════════════════════════════${NC}"
echo -e "${BOLD}  Mosaic — Starting services${NC}"
echo -e "${BOLD}═══════════════════════════════════════════${NC}"
echo ""

# ── Start Go bridge ──────────────────────────────────────────────────
echo "→ Starting WhatsApp bridge (port 8080)…"
(cd "$(dirname "$BRIDGE_BIN")" && nohup ./wa-bridge > /tmp/mosaic_bridge.log 2>&1) &
BRIDGE_PID=$!
echo "$BRIDGE_PID bridge" >> "$PID_FILE"
ok "Go bridge — PID $BRIDGE_PID"

# ── Start Flask backend ──────────────────────────────────────────────
echo "→ Starting Flask backend (port 3001)…"

# Quick smoke-test the backend first (check for import errors)
BACKEND_SMOKE=$("$PYTHON" -c "
import sys
sys.path.insert(0, '$PROJECT_DIR/taskdog-backend')
try:
    from dotenv import load_dotenv
    load_dotenv()
    from app import app
    print('OK')
except Exception as e:
    print(f'IMPORT_ERROR: {e}')
    sys.exit(1)
" 2>&1) || true

if [ "$BACKEND_SMOKE" != "OK" ]; then
  echo ""
  fail_msg "Backend import check failed. The app would crash on startup."
  echo ""
  echo -e "  Error: ${RED}$BACKEND_SMOKE${NC}"
  echo ""
  echo "  Likely causes:"
  echo "    1. Missing Python dependencies → run: venv/bin/pip install -r requirements.txt"
  echo "    2. Wrong Python version → check: python3 --version (needs 3.10+)"
  echo ""
  exit 1
fi

nohup "$PYTHON" "$PROJECT_DIR/taskdog-backend/app.py" > /tmp/mosaic_backend.log 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID backend" >> "$PID_FILE"
ok "Backend — PID $BACKEND_PID"

# ── Start Vite frontend ──────────────────────────────────────────────
echo "→ Starting frontend (port 5173)…"
(cd "$PROJECT_DIR/taskdog-frontend" && nohup npm run dev > /tmp/mosaic_frontend.log 2>&1) &
FRONTEND_PID=$!
echo "$FRONTEND_PID frontend" >> "$PID_FILE"
ok "Frontend — PID $FRONTEND_PID"

echo ""
echo "→ Waiting for services to come online…"

wait_for_http() {
  local port=$1 name=$2 timeout=${3:-20}
  local elapsed=0
  while [ $elapsed -lt $timeout ]; do
    if curl -s "http://localhost:$port" > /dev/null 2>&1; then
      ok "$name ready on port $port"
      return 0
    fi
    sleep 0.5
    elapsed=$((elapsed + 1))
  done

  warn "$name did not respond on port $port in ${timeout}s"
  echo ""
  local logfile
  case "$name" in
    Backend) logfile=/tmp/mosaic_backend.log ;;
    Frontend) logfile=/tmp/mosaic_frontend.log ;;
    Bridge)   logfile=/tmp/mosaic_bridge.log ;;
    *)        return 1 ;;
  esac
  if [ -f "$logfile" ]; then
    echo -e "  ${YELLOW}Last 15 lines of $logfile:${NC}"
    tail -15 "$logfile" | while IFS= read -r line; do
      echo "    $line"
    done
  fi
  echo ""
  return 1
}

all_up=true
wait_for_http 3001 "Backend" || all_up=false
wait_for_http 5173 "Frontend" || all_up=false
wait_for_http 8080 "Bridge" || all_up=false

# ── Done ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
if $all_up; then
  echo -e "${GREEN}  Mosaic is running.${NC}"
else
  echo -e "${YELLOW}  Some services failed to start (see above).${NC}"
fi
echo ""
echo "  Dashboard → http://localhost:5173/"
echo "  Backend   → http://localhost:3001/"
echo ""
echo "  Stop:  bash scripts/stop.sh"
echo "  Logs:  /tmp/mosaic_*.log"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Auto-open browser
if command -v open &>/dev/null; then
  open "http://localhost:5173/"
elif command -v xdg-open &>/dev/null; then
  xdg-open "http://localhost:5173/"
fi
