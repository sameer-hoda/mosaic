#!/usr/bin/env bash
# ─── Mosaic · Single-Command Installer ─────────────────────────────────
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/sameer-hoda/mosaic/main/install.sh | bash
#
# Or from an already-cloned repo:
#   bash install.sh
#
# This script:
#   1. Clones the repo (if not already inside it)
#   2. Checks for required tools (python3, node, npm, go)
#   3. Installs all dependencies (venv, pip, npm, go build)
#   4. Sets up .env from template
#   5. Starts all 3 services
#──────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_URL="https://github.com/sameer-hoda/mosaic.git"
REPO_NAME="mosaic"

# ── Colors ───────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

step()  { echo -e "${BOLD}→${NC} $1"; }
ok()    { echo -e "  ${GREEN}✓${NC} $1"; }
warn()  { echo -e "  ${YELLOW}⚠${NC} $1"; }
fail()  { echo -e "  ${RED}✗${NC} $1"; }
info()  { echo -e "  ${CYAN}ℹ${NC} $1"; }

header() {
  echo ""
  echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
  echo -e "${BOLD}  Mosaic · Installer${NC}"
  echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
  echo ""
}

header

# ═════════════════════════════════════════════════════════════════════
# STEP 0: Determine if we're inside the repo or not
# ═════════════════════════════════════════════════════════════════════
if [ -f "install.sh" ] && [ -f "scripts/start.sh" ] && [ -d "taskdog-backend" ]; then
  PROJECT_DIR="$(pwd)"
  info "Already inside Mosaic repo at $PROJECT_DIR"
else
  step "Cloning Mosaic..."
  if [ -d "$REPO_NAME" ]; then
    warn "$REPO_NAME directory already exists. Using it."
    cd "$REPO_NAME"
  else
    git clone "$REPO_URL" "$REPO_NAME"
    cd "$REPO_NAME"
  fi
  PROJECT_DIR="$(pwd)"
  ok "Cloned to $PROJECT_DIR"
fi

echo ""

# ═════════════════════════════════════════════════════════════════════
# STEP 1: Check & guide tool installation
# ═════════════════════════════════════════════════════════════════════
missing_tools=()
check_tool() {
  if command -v "$1" &>/dev/null; then
    local ver
    ver=$("$1" --version 2>&1 | head -1 || echo "?")
    ok "$1 — $ver"
  else
    fail "$1 not found"
    missing_tools+=("$1")
  fi
}

echo -e "${BOLD}[1/4]${NC} Checking prerequisites..."
echo ""

check_tool python3

# ── Find the best Python (prefer versioned Homebrew installs) ────────
BEST_PYTHON=""
for candidate in python3.12 python3.13 python3.11 python3.10 python3; do
  if command -v "$candidate" &>/dev/null; then
    candidate_ver=$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    candidate_major=$(echo "$candidate_ver" | cut -d. -f1)
    candidate_minor=$(echo "$candidate_ver" | cut -d. -f2)
    if [ "$candidate_major" -gt 3 ] || ([ "$candidate_major" -eq 3 ] && [ "$candidate_minor" -ge 10 ]); then
      BEST_PYTHON="$candidate"
      info "Found Python $candidate_ver → using $candidate"
      break
    fi
  fi
done

if [ -z "$BEST_PYTHON" ]; then
  fail "No Python 3.10+ found. python3 reports Python $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  echo ""
  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  Install: brew install python@3.12"
    echo "  Then:    re-run this script"
  else
    echo "  Install Python 3.10+ and re-run this script."
  fi
  exit 1
fi

# Use the best Python for all later commands
PY3="$BEST_PYTHON"

check_tool node
check_tool npm
check_tool go

echo ""

if [ ${#missing_tools[@]} -gt 0 ]; then
  echo -e "${RED}Missing tools: ${missing_tools[*]}${NC}"
  echo ""
  echo -e "${BOLD}Install them before continuing:${NC}"
  echo ""

  for tool in "${missing_tools[@]}"; do
    case "$tool" in
      python3)
        if [[ "$OSTYPE" == "darwin"* ]]; then
          echo "  python3 — brew install python@3.12"
        else
          echo "  python3 — sudo apt install python3 python3-venv python3-pip  (Ubuntu/Debian)"
        fi
        ;;
      node|npm)
        if [[ "$OSTYPE" == "darwin"* ]]; then
          echo "  node+npm — brew install node"
        else
          echo "  node+npm — curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install nodejs"
        fi
        ;;
      go)
        if [[ "$OSTYPE" == "darwin"* ]]; then
          echo "  go — brew install go"
        else
          echo "  go — sudo apt install golang-go  (Ubuntu/Debian)"
        fi
        ;;
    esac
  done

  echo ""
  echo -e "${YELLOW}After installing missing tools, re-run this script:${NC}"
  echo -e "  ${BOLD}cd mosaic && bash install.sh${NC}"
  exit 1
fi

# ═════════════════════════════════════════════════════════════════════
# STEP 2: Install all dependencies
# ═════════════════════════════════════════════════════════════════════
step ""
echo -e "${BOLD}[2/4]${NC} Installing dependencies..."
echo ""

# ── Python venv ────────────────────────────────────────────────────
PYTHON_VENV="$PROJECT_DIR/taskdog-backend/venv/bin/python"
if [ -f "$PYTHON_VENV" ]; then
  ok "Python venv already exists"
else
  step "Creating Python virtual environment..."
  $PY3 -m venv "$PROJECT_DIR/taskdog-backend/venv"
  ok "venv created"

  step "Installing Python dependencies (Flask, Gemini SDK, etc.)..."
  "$PROJECT_DIR/taskdog-backend/venv/bin/pip" install -r "$PROJECT_DIR/taskdog-backend/requirements.txt" --quiet
  ok "Python dependencies installed"
fi

# ── Frontend node_modules ──────────────────────────────────────────
if [ -d "$PROJECT_DIR/taskdog-frontend/node_modules" ]; then
  ok "node_modules already exists"
else
  step "Installing frontend dependencies (Vite, React, QR code)..."
  (cd "$PROJECT_DIR/taskdog-frontend" && npm install --silent)
  ok "Frontend dependencies installed"
fi

# ── Go bridge ──────────────────────────────────────────────────────
BRIDGE_BIN="$PROJECT_DIR/whatsapp-mcp/whatsapp-bridge/wa-bridge"
if [ -f "$BRIDGE_BIN" ]; then
  ok "Go bridge binary already built"
else
  step "Building WhatsApp bridge (Go)..."
  (cd "$PROJECT_DIR/whatsapp-mcp/whatsapp-bridge" && go build -o wa-bridge .)
  ok "Go bridge built"
fi

echo ""

# ═════════════════════════════════════════════════════════════════════
# STEP 3: Setup .env
# ═════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[3/4]${NC} Setting up configuration..."
echo ""

ENV_FILE="$PROJECT_DIR/taskdog-backend/.env"
if [ -f "$ENV_FILE" ] && grep -q "GEMINI_API_KEY=." "$ENV_FILE" 2>/dev/null; then
  ok ".env already configured with a key"
else
  if [ ! -f "$ENV_FILE" ]; then
    cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
  fi
  echo ""
  echo -e "  ${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "  ${BOLD}ACTION REQUIRED: Add your Gemini API key${NC}"
  echo ""
  echo -e "  Get a free key: ${CYAN}https://aistudio.google.com/apikey${NC}"
  echo ""
  echo -e "  Then edit ${CYAN}taskdog-backend/.env${NC} and replace:"
  echo -e "    GEMINI_API_KEY=${RED}your-gemini-api-key-here${NC}"
  echo -e "    → GEMINI_API_KEY=${GREEN}AIzaSy...your-actual-key${NC}"
  echo ""
  echo -e "  Or set it now:"
  echo -e "    ${BOLD}export GEMINI_API_KEY=your-key-here${NC}"
  echo -e "  ${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
fi

# ═════════════════════════════════════════════════════════════════════
# STEP 4: Start services
# ═════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[4/4]${NC} Starting services..."
echo ""

# Kill anything lingering on our ports
for port in 3001 5173 8080; do
  pids=$(lsof -ti:$port 2>/dev/null || true)
  if [ -n "$pids" ]; then
    for pid in $pids; do
      kill -9 "$pid" 2>/dev/null || true
    done
  fi
done
sleep 0.5

PID_FILE="$PROJECT_DIR/.mosaic_pids"
rm -f "$PID_FILE"

# ── Start Go bridge ──────────────────────────────────────────────────
echo "  Starting WhatsApp bridge (port 8080)..."
(cd "$PROJECT_DIR/whatsapp-mcp/whatsapp-bridge" && nohup ./wa-bridge > /tmp/mosaic_bridge.log 2>&1) &
BRIDGE_PID=$!
echo "$BRIDGE_PID bridge" >> "$PID_FILE"
echo "    PID $BRIDGE_PID"

# ── Start Flask backend ──────────────────────────────────────────────
echo "  Starting Flask backend (port 3001)..."
nohup "$PYTHON_VENV" "$PROJECT_DIR/taskdog-backend/app.py" > /tmp/mosaic_backend.log 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID backend" >> "$PID_FILE"
echo "    PID $BACKEND_PID"

# ── Start Vite frontend ──────────────────────────────────────────────
echo "  Starting frontend (port 5173)..."
(cd "$PROJECT_DIR/taskdog-frontend" && nohup npm run dev > /tmp/mosaic_frontend.log 2>&1) &
FRONTEND_PID=$!
echo "$FRONTEND_PID frontend" >> "$PID_FILE"
echo "    PID $FRONTEND_PID"

echo ""

# ── Wait for services ────────────────────────────────────────────────
step "Waiting for services to come online..."

wait_for_port() {
  local port=$1 name=$2 timeout=${3:-30}
  local elapsed=0
  while [ $elapsed -lt $timeout ]; do
    if curl -s "http://localhost:$port" >/dev/null 2>&1; then
      ok "$name ready (port $port)"
      return 0
    fi
    sleep 0.5
    elapsed=$((elapsed + 1))
  done

  # Check logs for clues
  echo ""
  warn "$name on port $port didn't respond in ${timeout}s."
  case "$name" in
    Backend)
      if [ -f /tmp/mosaic_backend.log ]; then
        echo -e "  ${YELLOW}Backend log tail:${NC}"
        tail -20 /tmp/mosaic_backend.log | sed 's/^/    /'
      fi
      ;;
  esac
  return 1
}

all_up=true
wait_for_port 3001 "Backend" || all_up=false
wait_for_port 5173 "Frontend" || all_up=false

# ── Done ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
if $all_up; then
  echo -e "${GREEN}  Mosaic is running.${NC}"
else
  echo -e "${YELLOW}  Mosaic started with warnings (see above).${NC}"
fi
echo ""
echo "  Dashboard → http://localhost:5173/"
echo "  Backend   → http://localhost:3001/"
echo ""
echo "  Stop:  bash scripts/stop.sh"
echo "  Logs:  /tmp/mosaic_backend.log"
echo "         /tmp/mosaic_frontend.log"
echo "         /tmp/mosaic_bridge.log"
echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Auto-open browser
if command -v open &>/dev/null; then
  open "http://localhost:5173/"
elif command -v xdg-open &>/dev/null; then
  xdg-open "http://localhost:5173/"
fi
