#!/usr/bin/env bash
# ─── TaskDog · Stop all services ──────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$PROJECT_DIR/.taskdog_pids"

echo "⏹  Stopping TaskDog services…"

if [ -f "$PID_FILE" ]; then
  while IFS=' ' read -r pid name; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null && echo "  ✅ Stopped $name (pid $pid)"
    else
      echo "  - $name (pid $pid) already stopped"
    fi
  done < "$PID_FILE"
  rm -f "$PID_FILE"
fi

# Also kill anything lingering on the ports
for port in 3001 5173 8080; do
  pids=$(lsof -ti:$port 2>/dev/null || true)
  if [ -n "$pids" ]; then
    for pid in $pids; do
      kill -9 "$pid" 2>/dev/null && echo "  ✅ Killed leftover on port $port (pid $pid)"
    done
  fi
done

echo "  Done."