#!/usr/bin/env bash
# ─── TaskDog v2 · Robust First-Time-User Reset ────────────────────────────
# Kills ALL services, wipes all databases, clears config, clears caches.
# After running this: restart 3 services → fresh onboarding at http://localhost:5173/
#
# Usage:
#   bash scripts/reset_first_time.sh                # full wipe (key + pairing + all DBs)
#   bash scripts/reset_first_time.sh --keep-key     # preserve Gemini API key
#   bash scripts/reset_first_time.sh --keep-pairing # preserve WhatsApp session
#   bash scripts/reset_first_time.sh --keep-all     # wipe only task data (keep key + pairing)
#   bash scripts/reset_first_time.sh --dry-run      # show what WOULD be deleted
#
# Options can be combined: --keep-key --keep-pairing
#──────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_DIR/taskdog-backend"
BRIDGE_DIR="$PROJECT_DIR/whatsapp-mcp/whatsapp-bridge"
FRONTEND_DIR="$PROJECT_DIR/taskdog-frontend"

KEEP_KEY=false
KEEP_PAIRING=false
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --keep-key)     KEEP_KEY=true ;;
    --keep-pairing) KEEP_PAIRING=true ;;
    --keep-all)     KEEP_KEY=true; KEEP_PAIRING=true ;;
    --dry-run)      DRY_RUN=true ;;
    --help|-h)
      echo "Usage: bash scripts/reset_first_time.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --keep-key       Preserve GEMINI_API_KEY in .env"
      echo "  --keep-pairing   Preserve WhatsApp session (bridge store DBs)"
      echo "  --keep-all       Preserve key + pairing, wipe only task data"
      echo "  --dry-run        Show what would be deleted without doing it"
      echo "  --help, -h       Show this help"
      echo ""
      echo "Default (no flags): Full factory reset."
      exit 0
      ;;
    *)
      echo "Unknown option: $arg"
      echo "Use --help for usage."
      exit 1
      ;;
  esac
done

# ── Colors ───────────────────────────────────────────────────────────
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

DRY_TAG=""
if $DRY_RUN; then
  DRY_TAG=" ${YELLOW}(DRY RUN — no changes will be made)${NC}"
fi

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  TaskDog v2 — First-Time-User Reset${NC}${DRY_TAG}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "  ${CYAN}Flags:${NC} keep-key=$KEEP_KEY  keep-pairing=$KEEP_PAIRING  dry-run=$DRY_RUN"
echo ""

# ═══════════════════════════════════════════════════════════════════════
# STEP 1: Kill all services
# ═══════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[1/5]${NC} Killing all services…"
echo ""

declare -a KILLED_PIDS=()

kill_by_port() {
  local port=$1 name=$2
  local pids
  pids=$(lsof -ti:${port} 2>/dev/null || true)
  if [ -n "$pids" ]; then
    for pid in $pids; do
      if $DRY_RUN; then
        echo -e "  ${YELLOW}Would kill${NC} $name (port $port, pid $pid)"
      else
        kill -9 "$pid" 2>/dev/null || true
        KILLED_PIDS+=("$pid")
        echo -e "  ${GREEN}Killed${NC} $name (port $port, pid $pid)"
      fi
    done
  else
    echo -e "  - $name not running (port $port)"
  fi
}

kill_by_name() {
  local pattern=$1 label=$2
  local pids
  pids=$(pgrep -f "$pattern" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    for pid in $pids; do
      # Skip if already killed via port
      if [[ " ${KILLED_PIDS[*]:-} " =~ " ${pid} " ]]; then
        continue
      fi
      if $DRY_RUN; then
        echo -e "  ${YELLOW}Would kill${NC} $label (pid $pid)"
      else
        kill -9 "$pid" 2>/dev/null || true
        echo -e "  ${GREEN}Killed${NC} $label (pid $pid)"
      fi
    done
  else
    echo -e "  - No $label processes found"
  fi
}

kill_by_port 8080 "Go bridge"
kill_by_port 3001 "Flask backend"
kill_by_port 5173 "Vite frontend"

kill_by_name "wa-bridge" "wa-bridge"
kill_by_name "whatsapp-bridge" "whatsapp-bridge"
kill_by_name "app.py" "Flask app.py"
kill_by_name "vite" "Vite dev server"

if ! $DRY_RUN; then
  sleep 1
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════
# STEP 2: Wipe databases
# ═══════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[2/5]${NC} Wiping databases…"
echo ""

wipe_files() {
  local dir=$1 label=$2
  local pattern=$3
  local count=0
  for f in "$dir"/$pattern; do
    if [ -f "$f" ]; then
      count=$((count + 1))
      if $DRY_RUN; then
        echo -e "  ${YELLOW}Would delete${NC} $f"
      else
        rm -f "$f"
        echo -e "  ${GREEN}Deleted${NC} $f"
      fi
    fi
  done
  if [ "$count" -eq 0 ]; then
    echo -e "  - No $label files found"
  fi
}

# v1 + v2 backend DBs
wipe_files "$BACKEND_DIR" "taskdog v1+v2" "taskdog.db taskdog_v2.db taskdog.db-shm taskdog_v2.db-shm taskdog.db-wal taskdog_v2.db-wal"
# Also catch any stray temp test DBs
wipe_files "$BACKEND_DIR" "stray temp DBs" "tmp.*.db tmp.*.db-*"

# Bridge WhatsApp session + messages DBs
if $KEEP_PAIRING; then
  echo -e "  ${CYAN}Skipped${NC} bridge store DBs (--keep-pairing)"
else
  BRIDGE_STORE="$BRIDGE_DIR/store"
  wipe_files "$BRIDGE_STORE" "bridge whatsapp" "whatsapp.db whatsapp.db-shm whatsapp.db-wal"
  wipe_files "$BRIDGE_STORE" "bridge messages" "messages.db messages.db-shm messages.db-wal"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════
# STEP 3: Clear Gemini API key
# ═══════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[3/5]${NC} Managing Gemini API key…"
echo ""

ENV_FILE="$BACKEND_DIR/.env"
if [ -f "$ENV_FILE" ]; then
  CURRENT_KEY=$(grep "^GEMINI_API_KEY=" "$ENV_FILE" 2>/dev/null | sed 's/^GEMINI_API_KEY=//' || echo "")
  if [ -n "$CURRENT_KEY" ]; then
    if $KEEP_KEY; then
      echo -e "  ${CYAN}Preserved${NC} GEMINI_API_KEY (--keep-key)"
    elif $DRY_RUN; then
      echo -e "  ${YELLOW}Would clear${NC} GEMINI_API_KEY"
    else
      cp "$ENV_FILE" "$BACKEND_DIR/.env.bak.$(date +%Y%m%d_%H%M%S)"
      # macOS sed requires '' for in-place
      sed -i '' 's/^GEMINI_API_KEY=.*/GEMINI_API_KEY=/' "$ENV_FILE"
      echo -e "  ${GREEN}Cleared${NC} GEMINI_API_KEY (backup: .env.bak.*)"
    fi
  else
    echo -e "  - GEMINI_API_KEY already empty or unset"
  fi
else
  echo -e "  - No .env file found"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════
# STEP 4: Clear Python bytecode caches
# ═══════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[4/5]${NC} Clearing Python bytecode caches…"
echo ""

PYCACHE_COUNT=0
while IFS= read -r -d '' dir; do
  PYCACHE_COUNT=$((PYCACHE_COUNT + 1))
  if $DRY_RUN; then
    echo -e "  ${YELLOW}Would remove${NC} $dir"
  else
    rm -rf "$dir"
    echo -e "  ${GREEN}Removed${NC} $dir"
  fi
done < <(find "$BACKEND_DIR" -type d -name "__pycache__" -print0 2>/dev/null || true)

if [ "$PYCACHE_COUNT" -eq 0 ]; then
  echo -e "  - No __pycache__ directories found"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════
# STEP 5: Verification
# ═══════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[5/5]${NC} Verifying reset…"
echo ""

VERIFY_OK=true

# Check that DBs are gone
check_missing() {
  local file=$1 label=$2
  if [ -f "$file" ]; then
    echo -e "  ${RED}WARNING:${NC} $label still exists at $file"
    VERIFY_OK=false
  else
    echo -e "  ${GREEN}OK${NC} $label removed"
  fi
}

# Check key is cleared
check_key_cleared() {
  if [ -f "$ENV_FILE" ]; then
    local key
    key=$(grep "^GEMINI_API_KEY=" "$ENV_FILE" 2>/dev/null | sed 's/^GEMINI_API_KEY=//' || echo "")
    if [ -n "$key" ]; then
      if $KEEP_KEY; then
        echo -e "  ${GREEN}OK${NC} GEMINI_API_KEY preserved (--keep-key)"
      else
        echo -e "  ${RED}WARNING:${NC} GEMINI_API_KEY is still set in .env"
        VERIFY_OK=false
      fi
    else
      echo -e "  ${GREEN}OK${NC} GEMINI_API_KEY cleared"
    fi
  fi
}

# Check ports are free
check_port_free() {
  local port=$1 name=$2
  local pids
  pids=$(lsof -ti:${port} 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo -e "  ${YELLOW}NOTE:${NC} $name still on port $port (pid $pids)"
  else
    echo -e "  ${GREEN}OK${NC} $name port $port free"
  fi
}

if $DRY_RUN; then
  echo -e "  ${CYAN}Skipped${NC} (dry run)"
else
  check_missing "$BACKEND_DIR/taskdog.db" "v1 taskdog.db"
  check_missing "$BACKEND_DIR/taskdog.db-wal" "v1 WAL"
  check_missing "$BACKEND_DIR/taskdog.db-shm" "v1 SHM"
  check_missing "$BACKEND_DIR/taskdog_v2.db" "v2 taskdog_v2.db"
  check_missing "$BACKEND_DIR/taskdog_v2.db-wal" "v2 WAL"
  check_missing "$BACKEND_DIR/taskdog_v2.db-shm" "v2 SHM"

  if ! $KEEP_PAIRING; then
    check_missing "$BRIDGE_DIR/store/whatsapp.db" "bridge whatsapp.db"
    check_missing "$BRIDGE_DIR/store/messages.db" "bridge messages.db"
  fi

  check_key_cleared
  check_port_free 8080 "Bridge"
  check_port_free 3001 "Flask"
  check_port_free 5173 "Vite"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════
# DONE
# ═══════════════════════════════════════════════════════════════════════
if $DRY_RUN; then
  echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
  echo -e "  ${YELLOW}Dry run complete. No changes were made.${NC}"
  echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
  echo ""
  exit 0
fi

echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}Reset complete. You are now a first-time user.${NC}"
echo ""
echo -e "  To restart the full experience:"
echo ""
echo -e "    ${BOLD}Terminal 1${NC} (bridge):"
echo -e "      cd whatsapp-mcp/whatsapp-bridge && ./wa-bridge"
echo ""
echo -e "    ${BOLD}Terminal 2${NC} (backend):"
echo -e "      cd taskdog-backend && venv/bin/python app.py"
echo ""
echo -e "    ${BOLD}Terminal 3${NC} (frontend):"
echo -e "      cd taskdog-frontend && npm run dev"
echo ""
echo -e "  Then open:  ${CYAN}http://localhost:5173/${NC}"
echo ""
echo -e "  Onboarding flow: ${BOLD}API Key → QR Scan → Group Whitelist → Dashboard${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""

if ! $VERIFY_OK; then
  echo -e "${YELLOW}Some verifications failed (see WARNINGs above).${NC}"
  echo -e "${YELLOW}Manually check the state before restarting services.${NC}"
  echo ""
fi