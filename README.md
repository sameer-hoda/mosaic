<h1 align="center">🐶 TaskDog</h1>
<p align="center"><strong>Your WhatsApp → AI Task Intelligence Pipeline</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python" />
  <img src="https://img.shields.io/badge/go-1.21+-00ADD8" alt="Go" />
  <img src="https://img.shields.io/badge/node-18+-339933" alt="Node" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License" />
</p>

<p align="center">
  TaskDog watches your WhatsApp groups and DMs, uses <strong>Gemini</strong> to discover tasks, keeps them updated as conversations evolve, and builds rich knowledge pages — all in a sleek web dashboard. No more "who said what?" rabbit holes.
</p>

---

## ✨ What It Does

- **Discovers tasks** from 30 days of WhatsApp messages using Gemini  
- **Refreshes incrementally** — new messages are folded into existing tasks, no duplicates  
- **Deep-dives** any task into a full wiki page with people, timeline, blockers, and decisions  
- **Dashboard** with importance-ranked cards, one-click status toggling, and filter-by-priority  
- **QR pairing** — scan a QR code to link your WhatsApp, no terminal fiddling  
- **Incremental updates** — refresh only picks up new messages since your last scan  
- **Zero-cron architecture** — every pipeline stage is triggered manually from the UI  

## 🏗 Architecture

```
  Your Phone                    Local Machine                        Your Browser
  ─────────                    ─────────────                        ────────────
  WhatsApp ──────► wa-bridge ──────► Flask API ──────► Vite + React
                   (Go, :8080)       (Python, :3001)     (:5173)
                                         │
                              ┌──────────┴──────────┐
                          taskdog.db (v1)    taskdog_v2.db (v2)
```

- **`wa-bridge`** — Go binary using `whatsmeow` to talk to WhatsApp. Exposes HTTP endpoints for reading chats, messages, and sending.  
- **Flask backend** — Python REST API. v1 routes handle chat reads and bridge status; v2 routes handle the task pipeline.  
- **Vite frontend** — React shell with a 3-gate onboarding flow (API key → QR scan → group whitelist → dashboard).  

## 🚀 Quick Start

### Prerequisites

| Tool | Why |
|---|---|
| **Go 1.21+** | Build the WhatsApp bridge from source |
| **Python 3.10+** | Run the Flask backend |
| **Node.js 18+** | Run the Vite frontend |
| **Gemini API key** | [Get one free](https://aistudio.google.com/apikey) |
| **WhatsApp account** | Scan a QR code to pair |

### 1. Clone & install

```bash
git clone https://github.com/sameer-hoda/taskdog.git
cd taskdog
```

### 2. Set your Gemini key

```bash
cp .env.example taskdog-backend/.env
```

Open `taskdog-backend/.env` and replace the placeholder:

```env
GEMINI_API_KEY=your-actual-gemini-key-here
DATABASE_PATH=taskdog.db
DATABASE_PATH_V2=taskdog_v2.db
```

### 3. Install dependencies

```bash
# Python backend
cd taskdog-backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# Frontend
cd ../taskdog-frontend
npm install

# Go bridge
cd ../whatsapp-mcp/whatsapp-bridge
go build -o wa-bridge .
```

### 4. Start everything

```bash
cd ../..
bash scripts/start.sh
```

Open **http://localhost:5173** — the onboarding flow will guide you through:
1. Paste your Gemini key
2. Scan the QR code with WhatsApp
3. Pick which groups/DMs to track

### Manual start (3 terminals)

| Terminal | Service | Port | Command |
|---|---|---|---|
| 1 | Go bridge | `8080` | `cd whatsapp-mcp/whatsapp-bridge && ./wa-bridge` |
| 2 | Flask API | `3001` | `cd taskdog-backend && venv/bin/python app.py` |
| 3 | Vite dev | `5173` | `cd taskdog-frontend && npm run dev` |

## ⚙️ Pipeline

Every stage is triggered manually from the dashboard. No scheduled jobs, no cron.

| Stage | Trigger | What happens |
|---|---|---|
| **Discover** | Click "Discover" | Scans last 30 days of messages per group. Gemini extracts all tasks. |
| **Refresh** | Click "Refresh" | Incremental update — only new messages since last scan. Tasks updated in-place. |
| **Deep-dive** | Click a task card | Full transcript → Gemini → wiki page + people + timeline + blockers + decisions. |
| **Dashboard** | Always live | Pure DB read, sorted by importance. No Gemini calls — fast. |

## 📡 API Reference

### v2 Task Pipeline

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
| `GET` | `/api/bridge/status` | Onboarding → checks if WhatsApp is connected |
| `GET` | `/api/bridge/qr` | Onboarding → renders QR code for pairing |
| `POST` | `/api/chats/classify` | Onboarding → lists chats with AI category + TLDR |
| `POST` | `/api/chats/classify/stream` | Onboarding → streaming variant |
| `POST` | `/api/send` | Dashboard → send a nudge to a WhatsApp contact |

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

# v2 integration tests (30 tests — DB CRUD, routes, pipeline with mocked Gemini)
DATABASE_PATH_V2=$(mktemp) DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_v2 -v

# Onboarding tests (67 tests — full first-time-user journey)
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
│   │   └── components/       # ApiKey.js, Pairing.js, Whitelist.js, Dashboard.js, DeepDive.js, Header.js
│   └── package.json
│
├── whatsapp-mcp/             # WhatsApp bridge (Go) + MCP server (Python)
│   └── whatsapp-bridge/      # Go source: main.go, go.mod, go.sum
│
├── scripts/                  # start.sh, stop.sh, reset_first_time.sh
├── v2_spec/                  # Architecture docs, API contracts, runbook
├── deployment/               # Electron wrapper for desktop distribution
└── okf/                      # Organized Knowledge Folder (internal docs)
```

## 🔒 Security

- Your Gemini API key stays in a local `.env` file (gitignored)  
- WhatsApp session data (`.db` files) is gitignored — never leaves your machine  
- The bridge runs on `localhost` only — nothing is exposed to the internet  
- All pipeline stages are manually triggered — no automated API spend  

## 📄 License

MIT
