# TaskDog Backend

The TaskDog backend is a Flask REST API that powers the local-first WhatsApp task
intelligence app. It reads chats from the local WhatsApp bridge SQLite databases,
classifies them with Google Gemini, and exposes a Kanban API for the React frontend.

## Features

- Session reset (`POST /api/setup/reset`) — kills the bridge, purges the store DBs, rebuilds the local DB.
- Bridge status polling (`GET /api/bridge/status`) — reports `offline | pairing | connected`.
- Top-N chat classification (`POST /api/chats/classify`) — runs Gemini on the last 25 messages of each chat.
- Theme + task extraction (`POST /api/tasks/extract`) — runs Gemini on 30 days of messages for whitelisted groups.
- Kanban API (`GET /api/tasks`, `POST /api/tasks/update_status`).
- WhatsApp send via Go bridge (`POST /api/send`).
- Group list (`GET /api/groups`) and nudge history (`GET /api/history`).

## Architecture

```
Frontend (Vite · port 5173)
      ↓ (proxied /api)
TaskDog Backend (Flask · port 3001)
      ├── models/database.py    ← SQLite helpers (taskdog.db)
      ├── routes/tasks.py       ← all REST endpoints
      └── utils/gemini_client.py ← Gemini REST client
      ↓
Go WhatsApp Bridge (port 8080)
      ↓
SQLite (whatsapp.db, messages.db)
```

## Setup

```bash
# Create venv (one-time)
cd taskdog-backend
/opt/homebrew/bin/python3 -m venv venv

# Install deps (use cached wheels if no internet)
venv/bin/pip install --no-index --find-links=../.wheels -r requirements.txt

# Run
venv/bin/python app.py
# → http://localhost:3001
```

## Environment

`.env`:
```env
GEMINI_API_KEY="..."
DATABASE_PATH="taskdog.db"
```

## Tests

```bash
cd taskdog-backend
DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_api -v
```

25 tests covering schema, CRUD, API endpoints, and the Gemini client (with mocks).

## API

See `taskdog-handoff/04_api_contracts.md` for the full list of endpoints.
