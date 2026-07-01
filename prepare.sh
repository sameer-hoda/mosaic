#!/usr/bin/env bash
# ─── TaskDog · Prepare github-dist for public release ─────────────────────
# Copies source files from the parent project into github-dist/,
# EXCLUDING all secrets, binaries, databases, and build artifacts.
#
# Usage:  bash github-dist/prepare.sh          # dry-run (show what would be copied)
#         bash github-dist/prepare.sh --copy   # actually copy files
#──────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$SCRIPT_DIR"                       # github-dist/
PARENT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"   # project root
DRY_RUN=true

for arg in "$@"; do
  case "$arg" in
    --copy) DRY_RUN=false ;;
    --help|-h)
      echo "Usage: bash github-dist/prepare.sh [--copy]"
      echo ""
      echo "  (no flag)  Dry run — shows what would be copied"
      echo "  --copy      Actually copy files into github-dist/"
      exit 0
      ;;
  esac
done

# ── Exclusion patterns for rsync (relative to transfer root) ──────────
EXCLUDE=(
  # Secrets
  ".env"
  "*.pem"
  "*_credentials*"
  "_secrets/"
  # Databases
  "*.db"
  "*.db-shm"
  "*.db-wal"
  # WhatsApp session store
  "store/"
  # Go/Python/Node build artifacts
  "venv/"
  "node_modules/"
  "dist/"
  "dist-electron/"
  "build/"
  "*.egg-info/"
  "__pycache__/"
  "*.pyc"
  # Go binaries
  "wa-bridge"
  "wa-bridge-*"
  "wa-bridge-arm64"
  "wa-bridge-x86_64"
  "whatsapp-bridge"
  "server"
  # OS files
  ".DS_Store"
  "Thumbs.db"
  # Log files
  "*.log"
  "*.log.*"
  # IDE
  ".idea/"
  ".vscode/"
  "*.swp"
  "*.swo"
  # Runtime
  ".taskdog_pids"
  # Backups
  "*.bak"
  ".env.bak*"
  "*.backup"
  # Stray files that don't belong in the dist
  "extract_wheels.py"
  # Nested git repos
  ".git/"
)

# ── Manually specify what directories/files to include ──────────────────
INCLUDE_DIRS=(
  "taskdog-backend"
  "taskdog-frontend"
  "whatsapp-mcp"
  "scripts"
  "v2_spec"
  "brand_book"
  "deployment"
  "okf"
  "sandbox"
  "taskdog-app"
)

# Optional files at root (explicitly list — NOT wildcard)
INCLUDE_FILES=(
  "AGENTS.md"
  "TODO.md"
  "PROJECT_IDENTITY.md"
  "NAMING_BRAINSTORM.md"
)

echo ""
echo "═══════════════════════════════════════════════"
if $DRY_RUN; then
  echo "  TaskDog · GitHub Release Prep (DRY RUN)"
else
  echo "  TaskDog · GitHub Release Prep"
fi
echo "═══════════════════════════════════════════════"
echo ""
echo "  Source:  $PARENT_DIR"
echo "  Dest:    $DIST_DIR"
echo ""

# Build rsync exclude args
RSYNC_EXCLUDE_ARGS=()
for pattern in "${EXCLUDE[@]}"; do
  RSYNC_EXCLUDE_ARGS+=(--exclude="$pattern")
done

# ── Clean destination first ────────────────────────────────────────────
if ! $DRY_RUN; then
  echo "→ Cleaning destination (keeping .gitignore, .env.example, prepare.sh, README.md)..."
  # Save these files
  KEEP_FILES=()
  for f in ".gitignore" ".env.example" "prepare.sh" "README.md"; do
    if [ -f "$DIST_DIR/$f" ]; then
      cp "$DIST_DIR/$f" /tmp/td_keep_$f
      KEEP_FILES+=("$f")
    fi
  done

  # Remove everything except the keep files
  find "$DIST_DIR" -mindepth 1 -maxdepth 1 -not -name '.gitignore' -not -name '.env.example' -not -name 'prepare.sh' -not -name 'README.md' -not -name '.git' | xargs rm -rf

  # Restore keep files
  for f in "${KEEP_FILES[@]}"; do
    cp "/tmp/td_keep_$f" "$DIST_DIR/$f"
    rm "/tmp/td_keep_$f"
  done
fi

# ── Copy directories ───────────────────────────────────────────────────
echo "→ Copying directories..."
echo ""
for dir in "${INCLUDE_DIRS[@]}"; do
  src="$PARENT_DIR/$dir"
  if [ -d "$src" ]; then
    if $DRY_RUN; then
      echo "  [would copy]  $dir/"
    else
      rsync -a --delete "${RSYNC_EXCLUDE_ARGS[@]}" "$src/" "$DIST_DIR/$dir/"
      echo "  ✓ copied  $dir/"
    fi
  else
    echo "  ✗ missing $dir/ (skipped)"
  fi
done

# ── Copy root files ────────────────────────────────────────────────────
echo ""
echo "→ Copying root files..."
echo ""
for file in "${INCLUDE_FILES[@]}"; do
  src="$PARENT_DIR/$file"
  if [ -f "$src" ]; then
    if $DRY_RUN; then
      echo "  [would copy]  $file"
    else
      cp "$src" "$DIST_DIR/$file"
      echo "  ✓ copied  $file"
    fi
  else
    echo "  ✗ missing $file (skipped)"
  fi
done

# ── Summary ────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════"
if $DRY_RUN; then
  echo "  Dry run complete. Run with --copy to execute."
else
  echo "  Copy complete."
  echo ""
  echo "  → Running post-copy cleanup..."

  # ── Post-copy: Copy Go bridge source from deployment/ → whatsapp-mcp/ ──
  BRIDGE_SRC="$PARENT_DIR/deployment/taskdog-electron/bridge"
  BRIDGE_DST="$DIST_DIR/whatsapp-mcp/whatsapp-bridge"
  if [ -d "$BRIDGE_SRC" ]; then
    mkdir -p "$BRIDGE_DST"
    for f in go.mod go.sum main.go; do
      if [ -f "$BRIDGE_SRC/$f" ]; then
        cp "$BRIDGE_SRC/$f" "$BRIDGE_DST/$f"
        echo "  ✓ copied bridge $f → whatsapp-mcp/whatsapp-bridge/"
      fi
    done
  fi

  # ── Post-copy: Remove any stray binaries that slipped through ──────────
  find "$DIST_DIR" \( -name "wa-bridge" -o -name "wa-bridge-*" -o -name "whatsapp-bridge" -o -name "server" \) -not -name "*.go" -not -name "*.mod" -not -name "*.sum" -type f -delete 2>/dev/null || true

  # ── Post-copy: Remove stray root-level files that dont belong ──────────
  rm -f "$DIST_DIR/taskdog-backend/.env.bak"* 2>/dev/null || true
  rm -f "$DIST_DIR/taskdog-backend/test_api.py" 2>/dev/null || true
  rm -f "$DIST_DIR/taskdog-backend/test_db.py" 2>/dev/null || true
  rm -f "$DIST_DIR/taskdog-backend/test_detailed.py" 2>/dev/null || true
  rm -f "$DIST_DIR/taskdog-backend/start.sh" 2>/dev/null || true
  rm -f "$DIST_DIR/taskdog-backend/extract_wheels.py" 2>/dev/null || true

  # ── Post-copy: Remove nested .git directories (from copied sub-projects) ──
  find "$DIST_DIR" -name ".git" -type d -mindepth 2 -exec rm -rf {} + 2>/dev/null || true

  echo "  ✓ Post-copy cleanup done"
  echo ""
  echo "  WHAT WAS EXCLUDED (via .gitignore + rsync filters):"
  echo "    - .env, .pem files, _secrets/"
  echo "    - *.db (all databases)"
  echo "    - store/ (WhatsApp session)"
  echo "    - wa-bridge binaries"
  echo "    - node_modules/, venv/"
  echo "    - __pycache__/, .DS_Store, *.log, *.bak"
  echo "    - _archive*/, .opencode/"
  echo ""
  echo "  NEXT STEPS:"
  echo "    cd github-dist"
  echo "    git init"
  echo "    git add -A"
  echo "    git status          # ← review before committing"
  echo "    git commit -m 'Initial public release'"
  echo "    git remote add origin git@github.com:YOUR_USER/taskdog.git"
  echo "    git push -u origin main"
fi
echo "═══════════════════════════════════════════════════════════════"
echo ""
