#!/usr/bin/env bash
# ===========================================================================
# OKF Sync — Daily documentation audit & update script
#
# Designed to run from cron or manually. Three modes:
#   ./scripts/sync-okf.sh           → audit only, report staleness
#   ./scripts/sync-okf.sh --check   → exit 0 if OKF is fresh, 1 if stale
#   ./scripts/sync-okf.sh --apply   → launch opencode agent to sync OKF
#
# Cron example (daily at 9am):
#   0 9 * * * /path/to/project/scripts/sync-okf.sh --check || \
#     opencode /path/to/project --task "sync okf" &
# ===========================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OKF_DIR="$ROOT/okf"
AGENTS_MD="$ROOT/AGENTS.md"
BACKEND="$ROOT/taskdog-backend"
FRONTEND="$ROOT/taskdog-frontend"
LAST_SYNC_MARKER="$OKF_DIR/.last_sync"
MODE="${1:-audit}"

# -- Helpers ----------------------------------------------------------------
ok()    { echo "  ✓ $1"; }
warn()  { echo "  ⚠ $1"; }
fail()  { echo "  ✗ $1"; }
header(){ echo; echo "── $1 ──"; }

# -- 1. Ensure OKF folder exists -------------------------------------------
if [ ! -d "$OKF_DIR" ]; then
  echo "❌ OKF folder missing at $OKF_DIR"
  echo "   Run 'opencode --task \"create okf\"' to bootstrap it."
  exit 2
fi

if [ ! -f "$LAST_SYNC_MARKER" ]; then
  echo "⚠ No last-sync marker found. Assuming stale."
  touch -t 200001010000 "$LAST_SYNC_MARKER"
fi

# -- 2. Collect modification times -----------------------------------------
CODE_TIMESTAMP=$(find "$BACKEND" "$FRONTEND" "$ROOT/store" \
  -path '*/__pycache__' -prune -o \
  -path '*/node_modules' -prune -o \
  -path '*/venv' -prune -o \
  -path '*.db' -prune -o \
  -path '*.db-wal' -prune -o \
  -path '*.db-shm' -prune -o \
  -type f -print0 | xargs -0 stat -f '%m' 2>/dev/null | sort -rn | head -1)

OKF_TIMESTAMP=$(find "$OKF_DIR" -type f -name '*.md' -print0 | xargs -0 stat -f '%m' 2>/dev/null | sort -rn | head -1)
LAST_SYNC=$(stat -f '%m' "$LAST_SYNC_MARKER" 2>/dev/null || echo 0)

STALE=0
header "Staleness check"

if [ -n "$CODE_TIMESTAMP" ] && [ -n "$OKF_TIMESTAMP" ]; then
  if [ "$CODE_TIMESTAMP" -gt "$OKF_TIMESTAMP" ]; then
    warn "Code changed after last OKF update"
    STALE=1
  else
    ok "No code changes since last OKF update"
  fi
fi

# -- 3. Structural checks --------------------------------------------------
header "Structure check"

# Expected okf file count (53 as of June 2026)
OKF_COUNT=$(find "$OKF_DIR" -type f -name '*.md' | wc -l | tr -d ' ')
if [ "$OKF_COUNT" -lt 50 ]; then
  warn "OKF has $OKF_COUNT files (expected ~53)"
  STALE=1
else
  ok "OKF has $OKF_COUNT files"
fi

# Blueprint count check (app.py should register 6)
if grep -q "app.register_blueprint.*nudge_bp" "$BACKEND/app.py" 2>/dev/null; then
  ok "Backend has nudge blueprint (6 total)"
else
  warn "Nudge blueprint not registered — check app.py"
  STALE=1
fi

# Frontend component count
FE_COUNT=$(ls "$FRONTEND/src/components/"*.js 2>/dev/null | wc -l | tr -d ' ')
if [ "$FE_COUNT" -ne 11 ]; then
  warn "Frontend has $FE_COUNT components (expected 11)"
  STALE=1
else
  ok "Frontend has $FE_COUNT components"
fi

# Store path check
if [ -f "$ROOT/store/messages.db" ]; then
  ok "Store is at project root (/store/)"
else
  warn "Store not at project root — check bridge storage path"
fi

# -- 4. Latest known-gotcha checks (fail-fast) -----------------------------
header "Schema sanity"

# Check for stale 'timeline' field references in OKF (should be 'progress_log')
if grep -r '"timeline"' "$OKF_DIR" --include='*.md' > /dev/null 2>&1; then
  warn "OKF still references 'timeline' instead of 'progress_log'"
  STALE=1
else
  ok "OKF uses 'progress_log' (not 'timeline')"
fi

# Check for stale 'description' in tasks schema docs
if grep -i 'description.*task' "$OKF_DIR/database/tasks.md" | grep -v 'columns\|purpose' > /dev/null 2>&1; then
  if grep -q '\bdescription\b' "$OKF_DIR/database/tasks.md"; then
    warn "tasks.md may mention 'description' column (should be 'context')"
  fi
fi

# -- 5. Action -------------------------------------------------------------
header "Result"
echo

if [ "$STALE" -eq 1 ]; then
  case "$MODE" in
    --check)
      echo "❌ OKF is STALE (exit 1)"
      exit 1
      ;;
    --apply)
      echo "🔄 Launching opencode agent to sync OKF..."
      # Touch marker so repeated runs don't re-launch immediately
      echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LAST_SYNC_MARKER"

      if command -v opencode &> /dev/null; then
        opencode "$ROOT" --task "The OKF folder at okf/ is stale. Read the skill at .opencode/skills/okf-sync/SKILL.md and follow its instructions to sync OKF with the current codebase. Do not modify any code — only update files under okf/."
      else
        echo "   opencode CLI not found. Audit results above — update OKF manually."
        exit 2
      fi
      ;;
    *)
      echo "ℹ  OKF is stale. Run with --apply to auto-sync, or --check for CI."
      echo "   Changes since last sync: $(find "$BACKEND" "$FRONTEND" -newer "$LAST_SYNC_MARKER" -not -path '*/__pycache__/*' -not -path '*/venv/*' -not -path '*/node_modules/*' -not -name '*.db*' | head -20)"
      exit 0
      ;;
  esac
else
  echo "✅ OKF is FRESH — nothing to do."
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LAST_SYNC_MARKER"
  exit 0
fi
