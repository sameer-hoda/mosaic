---
type: Component
title: Flask Backend
description: Python Flask application on port 3001 that registers 6 blueprints (v1 + v2 routes), auto-initializes both databases on startup.
resource: file://taskdog-backend/app.py
tags: [python, flask, backend]
---

# Flask Backend

The Flask backend at `taskdog-backend/app.py` is the central orchestrator. It serves both v1 and v2 routes, manages both databases, and calls the Go bridge.

## Blueprints

| Blueprint | File | Routes |
|---|---|---|
| `tasks` (v1) | `routes/tasks.py` | Bridge status, classify, send, history |
| `setup_v2` | `routes/setup.py` | `GET /api/health`, `POST /api/setup/validate-key` |
| `groups_v2` | `routes/groups.py` | `POST /api/groups/whitelist`, `GET /api/groups` |
| `pipeline` | `routes/pipeline.py` | `/discover`, `/refresh`, `/deep-dive` (+ SSE streams) |
| `dashboard_v2` | `routes/dashboard.py` | Dashboard, task detail, messages, PATCH |
| `nudge_v2` | `routes/nudge.py` | Nudge generation + Persona management |

## Database Initialization

On startup, the app auto-initializes both databases:

```python
from models.database import init_db
from models.database_v2 import init_db_v2

init_db()    # v1: taskdog.db
init_db_v2() # v2: taskdog_v2.db
```

## Environment Configuration

Read from `taskdog-backend/.env`:

```env
GEMINI_API_KEY="AIzaSy..."
DATABASE_PATH="taskdog.db"
DATABASE_PATH_V2="taskdog_v2.db"
```

## Key Files

| File | Purpose |
|---|---|
| `app.py` | Flask app entry point, blueprint registration |
| `routes/tasks.py` | v1 routes (bridge, classify, send) |
| `routes/setup.py` | v2 health + key validation |
| `routes/groups.py` | v2 group whitelisting |
| `routes/pipeline.py` | v2 pipeline stages with SSE |
| `routes/dashboard.py` | v2 dashboard and task management |
| `routes/nudge.py` | v2 nudge generation + persona CRUD |
| `utils/gemini_v2.py` | All 3 Gemini prompts (discover, refresh, deep-dive) |
| `utils/gemini_client.py` | v1 Gemini client (classify, extract) |
| `utils/contact_resolver.py` | JID/LID → human name resolution |
| `utils/markdown_parser.py` | Markdown rendering utilities |
| `models/database_v2.py` | v2 schema + CRUD |
| `models/database.py` | v1 DB helpers |

## Virtual Environment

Always use `venv/bin/python`:

```bash
cd taskdog-backend
venv/bin/python app.py
```

System Python (mambaforge) is broken with `no module named 'encodings'`.
