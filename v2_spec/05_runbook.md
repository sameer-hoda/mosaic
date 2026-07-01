# TaskDog v2 — Runbook

How to run and test the v2 system locally. This builds on v1 infrastructure — the Go bridge and Flask backend are the same processes, just with new routes.

---

## Prerequisites

- Python 3.13+ (via Homebrew at `/opt/homebrew/bin/python3`)
- Go 1.24+ (pre-built bridge binary available, no compilation needed)
- Node.js 24+ (for Vite frontend)
- Working Gemini API key
- WhatsApp account linked (QR scan via Go bridge)

---

## Quick Start (all services)

### Terminal 1 — Go WhatsApp Bridge (port 8080)

```bash
cd $PROJECT_DIR/whatsapp-mcp/whatsapp-bridge
./wa-bridge
```

Scan the QR code from WhatsApp → Settings → Linked Devices → Link a Device.
Skip this if already paired (bridge will connect automatically).

### Terminal 2 — Flask Backend (port 3001)

```bash
cd $PROJECT_DIR/taskdog-backend
venv/bin/python app.py
```

Backend is ready when you see `Running on http://0.0.0.0:3001`.
Both v1 and v2 databases are auto-initialized on startup.

### Terminal 3 — Vite Frontend (port 5173)

```bash
cd $PROJECT_DIR/taskdog-frontend
npm run dev
```

Open **http://localhost:5173/** in your browser.

---

## Onboarding Flow (3 gates)

The frontend automatically routes through three onboarding gates. You can also test each step manually via curl.

### Gate A: Gemini API Key

The app starts on the API Key screen. Your key is already set in `.env`, so click "Continue" to proceed.

**Manual check:**
```bash
curl http://localhost:3001/api/health
```
- `gemini_key_set: true` → key is configured, proceed to Gate B
- `gemini_key_set: false` → set `GEMINI_API_KEY` in `taskdog-backend/.env` and restart

**Validate a new key (optional):**
```bash
curl -X POST http://localhost:3001/api/setup/validate-key \
  -H 'Content-Type: application/json' \
  -d '{"key":"AIzaSy..."}'
```

### Gate B: WhatsApp Bridge

The app polls `/api/bridge/status` every 2s until the bridge is connected.

**Manual check:**
```bash
curl http://localhost:3001/api/bridge/status
```
- `connected` → proceed to Gate C
- `pairing` → bridge is running, waiting for QR scan
- `offline` → start `./wa-bridge` in Terminal 1

### Gate C: Group Whitelisting

The app loads all chats via the classify stream (v1 endpoint, reused), lets you select groups, and saves them to the v2 `groups` table.

**Manual:**
```bash
# 1. Classify chats (shows top 100 with category + TLDR)
curl -X POST http://localhost:3001/api/chats/classify | jq '.chats[:5]'

# 2. Pick group JIDs and whitelist them
curl -X POST http://localhost:3001/api/groups/whitelist \
  -H 'Content-Type: application/json' \
  -d '{"jids":["120363123456@g.us","919967151186@s.whatsapp.net"]}'

# 3. Verify groups saved
curl http://localhost:3001/api/groups | jq .
```

After whitelisting, the app moves to the Dashboard.

---

## Pipeline (4 stages)

### Stage 1 — Discover Tasks

Scans 30 days of messages per group and extracts all tasks via Gemini.

**From the UI:** Click "Discover Tasks" on the dashboard. Streaming progress shows per-group results.

**Manual:**
```bash
curl -X POST http://localhost:3001/api/pipeline/discover \
  -H 'Content-Type: application/json' \
  -d '{"group_jids":["120363123456@g.us"]}'
```

Takes 10-30 seconds per group. The streaming variant (`/discover/stream`) shows real-time progress.

### Stage 2 — Refresh Tasks

Incrementally updates known tasks with new messages since last refresh.

**From the UI:** Click "Refresh" on the dashboard.

**Manual:**
```bash
curl -X POST http://localhost:3001/api/pipeline/refresh \
  -H 'Content-Type: application/json' \
  -d '{"group_jids":["120363123456@g.us"]}'
```

### Stage 3 — Deep-Dive

Comprehensive analysis of a single task — produces wiki, people, timeline, blockers, decisions.

**From the UI:** Click the analytics icon on any task card, or click the card itself.

**Manual:**
```bash
TASK_ID=$(curl -s http://localhost:3001/api/dashboard | jq -r '.tasks[0].id')

curl -X POST http://localhost:3001/api/pipeline/deep-dive \
  -H 'Content-Type: application/json' \
  -d "{\"task_id\":\"$TASK_ID\"}"
```

Takes 5-20 seconds (single Gemini call with full transcript).

### Stage 4 — Dashboard

Pure DB read — no Gemini calls. Tasks sorted by importance (high → low).

```bash
curl http://localhost:3001/api/dashboard | jq .
```

---

## Task Management

### View task detail
```bash
curl http://localhost:3001/api/tasks/$TASK_ID | jq .
```

### View tagged messages for a task
```bash
curl http://localhost:3001/api/tasks/$TASK_ID/messages | jq .
```

### Manual status / importance override
```bash
curl -X PATCH http://localhost:3001/api/tasks/$TASK_ID \
  -H 'Content-Type: application/json' \
  -d '{"status":"completed","importance":5}'
```

Valid statuses: `active`, `completed`, `archived`. Importance: 1-5.

---

## Running Tests

```bash
cd $PROJECT_DIR/taskdog-backend

# v2 integration tests (30 tests — DB CRUD, routes, pipeline with mocked Gemini)
DATABASE_PATH_V2=$(mktemp) DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_v2 -v

# v1 tests (existing, unchanged)
DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_api -v
```

### End-to-End Smoke Test

Requires all 3 services running + WhatsApp paired + Gemini key set:

```bash
cd $PROJECT_DIR/taskdog-backend
bash tests/e2e_v2.sh
```

This script walks through: health → classify → whitelist → discover → dashboard → refresh → deep-dive → manual update.

---

## Database Inspection

```bash
cd $PROJECT_DIR/taskdog-backend

# v2 DB (new)
sqlite3 taskdog_v2.db ".tables"
sqlite3 taskdog_v2.db "SELECT jid, name, category FROM groups;"
sqlite3 taskdog_v2.db "SELECT id, title, status, importance, assignee FROM tasks ORDER BY importance DESC;"
sqlite3 taskdog_v2.db "SELECT task_id, message_content, sender_name FROM task_messages LIMIT 10;"
sqlite3 taskdog_v2.db "SELECT COUNT(*) FROM followup_history;"

# v1 DB (unchanged, coexists)
sqlite3 taskdog.db ".tables"
sqlite3 taskdog.db "SELECT COUNT(*) FROM tasks;"
```

---

## Full Reset

To wipe v2 data and start fresh (keeps v1 and WhatsApp pairing intact):

```bash
# Kill backend
lsof -ti:3001 | xargs kill -9

# Delete v2 DB only
rm -f $PROJECT_DIR/taskdog-backend/taskdog_v2.db
rm -f $PROJECT_DIR/taskdog-backend/taskdog_v2.db-wal
rm -f $PROJECT_DIR/taskdog-backend/taskdog_v2.db-shm

# Restart backend (Terminal 2)
cd $PROJECT_DIR/taskdog-backend
venv/bin/python app.py
```

To wipe everything including WhatsApp pairing:

```bash
# Kill all services
pkill -f wa-bridge
lsof -ti:3001 | xargs kill -9
pkill -f "vite"

# Delete all databases
rm -f $PROJECT_DIR/taskdog-backend/taskdog_v2.db*
rm -f $PROJECT_DIR/taskdog-backend/taskdog.db
rm -f $PROJECT_DIR/whatsapp-mcp/whatsapp-bridge/store/whatsapp.db
rm -f $PROJECT_DIR/whatsapp-mcp/whatsapp-bridge/store/messages.db

# Restart from Terminal 1, 2, 3 above
```

---

## Frontend Build

```bash
cd $PROJECT_DIR/taskdog-frontend

# Dev server (hot reload)
npm run dev

# Production build (verify no import errors)
npx vite build
```

---

## File Structure (v2)

```
taskdog-backend/
├── app.py                        ← Flask app, registers all blueprints
├── .env                          ← GEMINI_API_KEY, DATABASE_PATH, DATABASE_PATH_V2
├── taskdog.db                    ← v1 database (coexists)
├── taskdog_v2.db                 ← v2 database (new)
├── models/
│   ├── database.py               ← v1 DB helpers (reused for WhatsApp reads)
│   └── database_v2.py            ← v2 schema + CRUD (thread-safe with write lock)
├── routes/
│   ├── tasks.py                  ← v1 routes (bridge status, classify, send, etc.)
│   ├── setup.py                  ← v2: GET /api/health, POST /api/setup/validate-key
│   ├── groups.py                 ← v2: POST /api/groups/whitelist, GET /api/groups
│   ├── pipeline.py               ← v2: /discover, /refresh, /deep-dive (+ streams)
│   └── dashboard.py              ← v2: GET /api/dashboard, /api/tasks/{id}, PATCH
├── utils/
│   ├── gemini_client.py          ← v1 Gemini client (classify, extract)
│   └── gemini_v2.py              ← v2 Gemini client (discover, refresh, deep-dive)
└── tests/
    ├── test_api.py               ← v1 tests
    ├── test_v2.py                ← v2 integration tests (30 tests)
    └── e2e_v2.sh                 ← End-to-end smoke test

taskdog-frontend/src/
├── app.js                        ← Phase router (apikey → pairing → whitelist → dashboard)
├── api.js                        ← API client (v1 + v2 endpoints, SSE stream parser)
└── components/
    ├── ApiKey.js                 ← Gate A: Gemini key entry
    ├── Pairing.js                ← Gate B: WhatsApp bridge pairing
    ├── Whitelist.js              ← Gate C: group selection
    ├── Dashboard.js              ← v2 task list with stats, discover/refresh, deep-dive
    ├── DeepDive.js               ← Task knowledge page (wiki, people, timeline)
    ├── Header.js                 ← Top bar with nav + settings
    ├── Classifier.js             ← v1 classifier (reused in Gate C)
    ├── Kanban.js                 ← v1 Kanban (legacy)
    └── ...
```

---

## API Reference

### v2 Endpoints (new)

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Combined health: gemini key + bridge status |
| POST | `/api/setup/validate-key` | Validate a Gemini API key |
| POST | `/api/groups/whitelist` | Save selected groups to v2 DB |
| GET | `/api/groups` | List all whitelisted groups with task counts |
| POST | `/api/pipeline/discover` | Stage 1: discover tasks (non-streaming) |
| POST | `/api/pipeline/discover/stream` | Stage 1: discover tasks (SSE streaming) |
| POST | `/api/pipeline/refresh` | Stage 2: refresh tasks (non-streaming) |
| POST | `/api/pipeline/refresh/stream` | Stage 2: refresh tasks (SSE streaming) |
| POST | `/api/pipeline/deep-dive` | Stage 3: deep-dive a single task |
| GET | `/api/dashboard` | All tasks with stats, sorted by importance |
| GET | `/api/tasks/{id}` | Full task detail |
| GET | `/api/tasks/{id}/messages` | Messages tagged for a task |
| PATCH | `/api/tasks/{id}` | Manual override (status, importance) |

### v1 Endpoints (reused, unchanged)

| Method | Path | Used In |
|---|---|---|
| GET | `/api/bridge/status` | Gate B: bridge status polling |
| POST | `/api/chats/classify` | Gate C: chat classification |
| POST | `/api/chats/classify/stream` | Gate C: streaming classification |
| POST | `/api/send` | Dashboard: send nudge |
| GET | `/api/history` | Dashboard: sent nudge history |

---

## SSE Streaming Test (manual)

Test the discover stream from a browser console:

```js
const response = await fetch('http://localhost:3001/api/pipeline/discover/stream', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({group_jids: ['120363...@g.us']})
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;
  console.log(decoder.decode(value)); // Raw SSE events
}
```

---

## Environment Variables

Set in `taskdog-backend/.env`:

```env
GEMINI_API_KEY="AIzaSy..."
DATABASE_PATH="taskdog.db"          # v1 DB (unchanged)
DATABASE_PATH_V2="taskdog_v2.db"    # v2 DB (new)
```

`DATABASE_PATH_V2` is read by `database_v2.py`. Defaults to `taskdog_v2.db` if not set.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Bridge is offline` | Start `wa-bridge` in Terminal 1. If already running, check `curl http://localhost:8080/api/status` |
| `gemini_key_set: false` | Set `GEMINI_API_KEY` in `.env` or pass via `export GEMINI_API_KEY=...` |
| `No chats found` | Bridge was just paired, hasn't loaded chats yet. Wait 30s and retry `/api/chats/classify`. |
| `FOREIGN KEY constraint failed` | Group not in v2 `groups` table. The pipeline auto-inserts missing groups — restart backend if persisting. |
| `database is locked` | Concurrent write contention. The v2 DB uses WAL mode + a write lock. If persisting, reduce `MAX_WORKERS` in `routes/pipeline.py`. |
| `Gateway timeout` on discover/refresh | Gemini call took >120s. Reduce the transcript window (try `days=7` in `fetch_chat_messages_since`). |
| `Address already in use — Port 3001` | Another Flask instance is running. `lsof -ti:3001 \| xargs kill -9`. |
| `Address already in use — Port 8080` | Another bridge instance. `pkill -f wa-bridge` then restart. |
| `no module named 'encodings'` | You're using mambaforge Python (broken). Use `venv/bin/python`. |
| Deep-dive returns empty wiki | The transcript may have no messages relevant to this task. Check the task was correctly identified in discovery. |
| Gemini returns `{"error": "..."}` | 3 retries exhausted. Check the Gemini API key is valid. Try reducing transcript size. |
| Dashboard shows 0 tasks | Run "Discover Tasks" first. Discovery must complete before tasks appear. |
| Dashboard shows old groups | The `/api/groups` endpoint reads from v2 `groups` table. Re-whitelist via the Groups tab. |

---

## Log Locations

| Service | Log |
|---|---|
| Go bridge | Terminal stdout (or `~/Library/Logs/TaskDog/bridge.log` in packaged app) |
| Flask backend | Terminal stdout (or `~/Library/Logs/TaskDog/backend.log` in packaged app) |
| Backend errors | Printed to Flask stdout with `print()` statements |
| Gemini API errors | Printed to Flask stdout — look for `Gemini API request error:` or `discover_tasks: Gemini failed` |
| Vite dev server | Terminal stdout |
