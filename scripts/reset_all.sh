#!/usr/bin/env bash
# ─── TaskDog v2 · Full Reset (first-time-user experience) ────────────────
# Kills all services, deletes ALL databases, clears the Gemini key.
# After running this, restart the 3 services and open http://localhost:5173/
# to experience the full onboarding flow (API Key → QR Scan → Whitelist).
#
# Usage:  bash scripts/reset_all.sh
#──────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  TaskDog v2 — Full Reset"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── 1. Kill all services ──────────────────────────────────────────────
echo "→ Killing services…"

kill_service() {
  local port=$1 name=$2
  local pid
  pid=$(lsof -ti:${port} 2>/dev/null || true)
  if [ -n "$pid" ]; then
    kill -9 $pid 2>/dev/null || true
    echo "  ✓ Killed $name (port $port, pid $pid)"
  else
    echo "  - $name not running (port $port)"
  fi
}

pkill -f wa-bridge 2>/dev/null || true
echo "  ✓ Killed wa-bridge processes (if any)"

kill_service 3001 "Flask backend"
kill_service 5173 "Vite frontend"
kill_service 8080 "Go bridge HTTP server"

sleep 1

# ── 2. Wipe all databases ─────────────────────────────────────────────
echo ""
echo "→ Wiping databases…"

rm -f "$PROJECT_DIR/taskdog-backend/taskdog.db"
rm -f "$PROJECT_DIR/taskdog-backend/taskdog_v2.db"
rm -f "$PROJECT_DIR/taskdog-backend/taskdog_v2.db-wal"
rm -f "$PROJECT_DIR/taskdog-backend/taskdog_v2.db-shm"
echo "  ✓ Deleted taskdog.db + taskdog_v2.db"

rm -f "$PROJECT_DIR/whatsapp-mcp/whatsapp-bridge/store/whatsapp.db"
rm -f "$PROJECT_DIR/whatsapp-mcp/whatsapp-bridge/store/whatsapp.db-wal"
rm -f "$PROJECT_DIR/whatsapp-mcp/whatsapp-bridge/store/whatsapp.db-shm"
rm -f "$PROJECT_DIR/whatsapp-mcp/whatsapp-bridge/store/messages.db"
rm -f "$PROJECT_DIR/whatsapp-mcp/whatsapp-bridge/store/messages.db-wal"
rm -f "$PROJECT_DIR/whatsapp-mcp/whatsapp-bridge/store/messages.db-shm"
echo "  ✓ Deleted bridge whatsapp.db + messages.db"

# ── 3. Clear Gemini API key ───────────────────────────────────────────
ENV_FILE="$PROJECT_DIR/taskdog-backend/.env"

if [ -f "$ENV_FILE" ]; then
  if grep -q "^GEMINI_API_KEY=." "$ENV_FILE" 2>/dev/null; then
    cp "$ENV_FILE" "$ENV_FILE.bak"
    sed -i '' 's/^GEMINI_API_KEY=.*/GEMINI_API_KEY=/' "$ENV_FILE"
    echo "  ✓ Cleared GEMINI_API_KEY from .env (backup: .env.bak)"
  else
    echo "  - GEMINI_API_KEY already empty or unset"
  fi
else
  echo "  - No .env file found"
fi

# ── 4. Done ───────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Reset complete. You are now a first-time user."
echo ""
echo "  To restart the full experience:"
echo ""
echo "    Terminal 1 (bridge):"
echo "      cd whatsapp-mcp/whatsapp-bridge && ./wa-bridge"
echo ""
echo "    Terminal 2 (backend):"
echo "      cd taskdog-backend && venv/bin/python app.py"
echo ""
echo "    Terminal 3 (frontend):"
echo "      cd taskdog-frontend && npm run dev"
echo ""
echo "  Then open:  http://localhost:5173/"
echo "═══════════════════════════════════════════════════════════"
echo ""