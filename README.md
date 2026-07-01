<p align="center">
  <img src="brand_book/v2/mosaic_brand_assets/mosaic-logo-final.svg" alt="Mosaic" width="320" />
</p>

<p align="center">
  <strong>Your life, pieced together.</strong><br>
  <sub>Mosaic turns scattered WhatsApp conversations into a clear picture of commitments, decisions, blockers, and next steps.</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python" />
  <img src="https://img.shields.io/badge/go-1.21+-00ADD8" alt="Go" />
  <img src="https://img.shields.io/badge/node-18+-339933" alt="Node" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License" />
</p>

---

Mosaic is the invisible organizer for your WhatsApp life. It reads your chats with care, finds what matters — commitments, decisions, blockers, follow-ups — and assembles them into an organized picture. No manual task creation. No new apps to learn. Your chats already know. Mosaic helps you see.

## ✨ What It Does

- **Surfaces commitments** — "I'll send this by Friday" becomes a trackable item
- **Catches decisions** — captures what was agreed in group threads before they scroll away
- **Flags blockers** — surfaces things waiting on someone else before they fall through
- **Keeps context** — every item stays linked to the original conversation, people, and timeline
- **Refreshes incrementally** — new messages are folded into existing items, no duplicates
- **Deep-dives** any conversation thread into a rich knowledge page
- **QR pairing** — scan a QR code to link WhatsApp, no terminal fiddling

## 🏗 Architecture

```
  Your Phone                    Local Machine                     Your Browser
  ─────────                    ─────────────                     ────────────
  WhatsApp ──────► wa-bridge ──────► Flask API ──────► Vite + React
                   (Go, :8080)       (Python, :3001)     (:5173)
                                         │
                              ┌──────────┴──────────┐
                          mosaic.db (v1)      mosaic_v2.db (v2)
```

- **`wa-bridge`** — Go binary using `whatsmeow` to talk to WhatsApp. Exposes HTTP endpoints for reading chats, messages, and sending.
- **Flask backend** — Python REST API. v1 routes handle chat reads and bridge status; v2 routes handle the intelligence pipeline.
- **Vite frontend** — React shell with a 3-gate onboarding flow: API key → QR scan → group selection → dashboard.

## 🚀 Quick Start (one command)

```bash
curl -fsSL https://raw.githubusercontent.com/sameer-hoda/mosaic/main/install.sh | bash
```

That's it. The installer handles everything.

👉 **New to computers?** Read the [Beginner Setup Guide](SETUP.md) — it explains every step in plain language, from opening Terminal to connecting WhatsApp.

That's it. The installer will:
1. **Clone** the repo (if needed)
2. **Check** prerequisites and tell you how to install what's missing
3. **Install** all dependencies (Python venv, pip packages, npm, Go bridge)
4. **Setup** your `.env` file and prompt you for a Gemini key
5. **Start** all 3 services and open the dashboard

### Prerequisites (one-time)

| Tool | Why | Install |
|---|---|---|
| **python3** (3.10+) | Flask backend | `brew install python@3.12` or `apt install python3 python3-venv` |
| **node + npm** (18+) | Vite frontend | `brew install node` or [nodejs.org](https://nodejs.org) |
| **go** (1.21+) | WhatsApp bridge | `brew install go` or `apt install golang-go` |
| **Gemini API key** | AI intelligence | [Get one free](https://aistudio.google.com/apikey) |

After the installer finishes, open **http://localhost:5173** and follow the 3-step onboarding:
1. **API Key** — paste your Gemini key
2. **QR Scan** — scan the QR code with WhatsApp to pair
3. **Group Selection** — pick which groups and DMs to include

Then click **Discover** on the dashboard to scan your chats.

### Manual start (3 terminals)

| Terminal | Service | Port | Command |
|---|---|---|---|
| 1 | Go bridge | `8080` | `cd whatsapp-mcp/whatsapp-bridge && ./wa-bridge` |
| 2 | Flask API | `3001` | `cd taskdog-backend && venv/bin/python app.py` |
| 3 | Vite dev | `5173` | `cd taskdog-frontend && npm run dev` |

## ⚙️ Intelligence Pipeline

Every stage is triggered manually from the dashboard. No scheduled jobs, no automatic API spend.

| Stage | Trigger | What happens |
|---|---|---|
| **Discover** | Click "Discover" | Scans last 30 days of messages per group. Gemini finds all commitments, decisions, blockers. |
| **Refresh** | Click "Refresh" | Incremental update — only new messages since last scan. Items updated in-place. |
| **Deep-dive** | Click a card | Full transcript → Gemini → rich knowledge page with people, timeline, blockers, decisions. |
| **Dashboard** | Always live | Pure DB read, sorted by importance. No Gemini calls — fast. |

## 📡 API Reference

### v2 Intelligence Endpoints

| Method | Endpoint |
|---|---|
| `GET` | `/api/health` |
| `POST` | `/api/setup/validate-key` |
| `POST` | `/api/groups/whitelist` |
| `GET` | `/api/groups` |
| `POST` | `/api/pipeline/discover` |
| `POST` | `/api/pipeline/discover/stream` (SSE) |
| `POST` | `/api/pipeline/refresh` |
| `POST` | `/api/pipeline/refresh/stream` (SSE) |
| `POST` | `/api/pipeline/deep-dive` |
| `GET` | `/api/dashboard` |
| `GET` | `/api/tasks/{id}` |
| `GET` | `/api/tasks/{id}/messages` |
| `PATCH` | `/api/tasks/{id}` |

### v1 Bridge / Chat

| Method | Endpoint | Used by |
|---|---|---|
| `GET` | `/api/bridge/status` | Onboarding — checks if WhatsApp is connected |
| `GET` | `/api/bridge/qr` | Onboarding — renders QR code for pairing |
| `POST` | `/api/chats/classify` | Onboarding — lists chats with AI category + TLDR |
| `POST` | `/api/chats/classify/stream` | Onboarding — streaming variant |

## 🔧 Management

```bash
bash scripts/start.sh                           # Start all 3 services
bash scripts/stop.sh                            # Kill everything

bash scripts/reset_first_time.sh                 # Full factory reset
bash scripts/reset_first_time.sh --keep-key      # Preserve Gemini key
bash scripts/reset_first_time.sh --keep-pairing  # Preserve WhatsApp session
bash scripts/reset_first_time.sh --keep-all      # Wipe only task data, keep config
```

## 🧪 Testing

```bash
cd taskdog-backend

# v2 integration tests (30 tests)
DATABASE_PATH_V2=$(mktemp) DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_v2 -v

# Onboarding tests (67 tests)
DATABASE_PATH_V2=$(mktemp) DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_onboarding -v

# All backend tests (97 total)
DATABASE_PATH_V2=$(mktemp) DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_onboarding tests.test_v2 -v

# Frontend build (verify no import errors)
cd ../taskdog-frontend && npx vite build
```

## 🗂 Project Structure

```
├── taskdog-backend/          # Flask API server (Python)
│   ├── app.py                # Entry point — registers blueprints, inits DBs
│   ├── .env.example          # Template for your Gemini key
│   ├── models/               # database.py (v1) + database_v2.py (v2)
│   ├── routes/               # tasks.py, setup.py, groups.py, pipeline.py, dashboard.py, nudge.py
│   ├── utils/                # gemini_client.py (v1) + gemini_v2.py (v2)
│   ├── tests/                # test_v2.py, test_onboarding.py, e2e_v2.sh
│   └── requirements.txt
│
├── taskdog-frontend/         # Vite + React dashboard
│   ├── src/
│   │   ├── app.js            # Phase router (apikey → pairing → whitelist → dashboard)
│   │   ├── api.js            # API client with SSE streaming
│   │   └── components/       # UI components for each step
│   └── package.json
│
├── whatsapp-mcp/             # WhatsApp bridge (Go) + MCP server (Python)
│   └── whatsapp-bridge/      # Go source: main.go, go.mod, go.sum
│
├── brand_book/               # Mosaic brand assets, logos, brand guide
├── scripts/                  # start.sh, stop.sh, reset_first_time.sh
├── v2_spec/                  # Architecture docs, API contracts, runbook
├── deployment/               # Electron wrapper for desktop distribution
└── okf/                      # Organized Knowledge Folder (internal docs)
```

## 🔒 Security

- Your Gemini API key stays in a local `.env` file (gitignored)
- WhatsApp session data (`.db` files) is gitignored — never leaves your machine
- The bridge runs on `localhost` only — nothing is exposed to the internet
- All intelligence stages are manually triggered — no automated API spend

## Brand

Mosaic's visual identity is built around the **tile** — each message, commitment, and decision is a piece that Mosaic assembles into a clear picture. Colors are calm and composed: violet (`#5B21FF`) for focus, ink (`#15163A`) for clarity, and neutral whitespace for breathing room. See the full [Brand Book](brand_book/v2/mosaic_brand_assets/MOSAIC_BRAND_BOOK.md).

> **Mosaic is the invisible organizer for your WhatsApp life.** From conversation to clarity. Your life, pieced together.

## 📄 License

MIT
