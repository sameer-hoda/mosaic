# TaskDog Electron Deployment

Self-contained desktop app — no terminals, no manual setup. The user only needs to
provide their Gemini API key on first launch.

## What's Included

- **Go WhatsApp bridge** (arm64 + x86_64 binaries) — connects to WhatsApp
- **Python Flask backend** — API server (Gemini AI, task discovery, deep-dive)
- **Built Vite frontend** — static SPA served directly by Flask
- **Electron shell** — manages subprocesses, config, and app lifecycle

## Architecture (Deployed)

```
┌─────────────────────────────────────────┐
│  Electron App                            │
│  ┌───────┐  ┌──────────┐  ┌──────────┐  │
│  │ Bridge │  │  Flask   │  │ Browser  │  │
│  │ :8080  │  │  :3001   │  │  Window  │  │
│  │  (Go)  │  │ (Python) │  │  (React) │  │
│  └───────┘  └──────────┘  └──────────┘  │
│       │           │             │         │
│       └───────────┴──────┬──────┘         │
│                          │                │
│              ~/Library/Application       │
│              Support/TaskDog/             │
│              (all user data here)         │
└─────────────────────────────────────────┘
```

Flask serves both the API (`/api/*`) and the static frontend (SPA fallback on `/*`).
No Vite dev server needed — the frontend is pre-built into `backend/static/`.

## Prerequisites for Building

- Node.js 20+ and npm
- macOS (for DMG target; build Windows/Linux by adding targets in package.json)

## Quick Start (Development)

```bash
cd deployment/taskdog-electron

# Install Electron + builder deps
npm install

# Start the app in dev mode
npm start
```

On first launch, the app automatically:
1. Creates a Python virtual environment in `~/Library/Application Support/TaskDog/venv/`
2. Installs Python dependencies from `backend/requirements.txt`
3. Starts the Flask backend on port 3001
4. Starts the Go bridge on port 8080
5. Opens the TaskDog onboarding flow (API key → QR code → whitelist → dashboard)

## Building the DMG

```bash
cd deployment/taskdog-electron

# Install deps if not already done
npm install

# Build for macOS (creates universal DMG with arm64 + x86_64)
npm run build:dmg

# Output: dist-electron/TaskDog-2.0.0-arm64.dmg and TaskDog-2.0.0-x64.dmg
```

**Before building, generate a proper icon:**
```bash
# Convert SVG to ICNS (requires imagemagick and iconutil)
cd assets
mkdir -p icon.iconset
# Generate PNGs at various sizes
sips -z 16 16   icon.svg --out icon.iconset/icon_16x16.png
sips -z 32 32   icon.svg --out icon.iconset/icon_16x16@2x.png
sips -z 32 32   icon.svg --out icon.iconset/icon_32x32.png
sips -z 64 64   icon.svg --out icon.iconset/icon_32x32@2x.png
sips -z 128 128 icon.svg --out icon.iconset/icon_128x128.png
sips -z 256 256 icon.svg --out icon.iconset/icon_128x128@2x.png
sips -z 256 256 icon.svg --out icon.iconset/icon_256x256.png
sips -z 512 512 icon.svg --out icon.iconset/icon_256x256@2x.png
sips -z 512 512 icon.svg --out icon.iconset/icon_512x512.png
iconutil -c icns icon.iconset
mv icon.icns ../
rm -rf icon.iconset
```

## What the User Experiences

1. **Double-click DMG, drag TaskDog to /Applications**
2. **Launch TaskDog** — app auto-bootstraps Python environment (30-60s first run)
3. **Gate A: Gemini API Key** — paste key, app validates it against Gemini API
4. **Gate B: WhatsApp Pairing** — QR code appears in-app, scan with WhatsApp phone
5. **Gate C: Group Whitelisting** — pick which WhatsApp groups to track
6. **Dashboard** — run Discover, Refresh, Deep Dive, manage tasks

The user never touches a terminal.

## What's NOT Included in the DMG

- No API keys (user provides their own)
- No WhatsApp session data (fresh pairing required)
- No database files (created fresh on first run)
- No personal messages or chat data

All user data lives in `~/Library/Application Support/TaskDog/`:
```
TaskDog/
├── config.json        # Gemini API key, preferences
├── taskdog.db         # v1 database
├── taskdog_v2.db      # v2 database (tasks, groups, deep-dives)
├── store/             # WhatsApp session + message cache
│   ├── whatsapp.db
│   └── messages.db
└── venv/              # Python virtualenv + installed packages
```

## System Requirements (end user)

- macOS 12 (Monterey) or later
- Python 3 installed (`python3` on PATH)
  - If not installed, the app shows a dialog with a download link
  - Install from: https://www.python.org/downloads/
  - Or run: `xcode-select --install` for Xcode CLT Python
- ~200 MB disk space (app + first-run venv)
- Internet connection (for Gemini API + WhatsApp)

## Updating the Frontend

```bash
# Rebuild frontend
cd ../../taskdog-frontend
npm run build

# Copy to deployment backend static folder
cp -r dist/* ../deployment/taskdog-electron/backend/static/
```

## Troubleshooting

| Problem | Solution |
|---|---|
| "python3 not found" | Install Python 3 from python.org or `xcode-select --install` |
| Bridge not connecting | The bridge QR pairing flow is shown in the frontend; ensure WhatsApp is open on your phone |
| Flask fails to start | Check `~/Library/Application Support/TaskDog/` for logs; delete `venv/` to force re-bootstrap |
| Database locked | Restart the app — WAL mode handles concurrent access normally |
| Port 3001 or 8080 in use | The app expects these ports; stop other processes using them |