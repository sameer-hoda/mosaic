---
type: Playbook
title: Runbook
description: Complete instructions for running all three services and executing the pipeline stages.
tags: [runbook, operations]
---

# Runbook

## Quick Start (single command)

```bash
bash scripts/start.sh     # starts bridge + backend + frontend, opens browser
bash scripts/stop.sh      # kills all services
bash scripts/reset_first_time.sh  # full factory reset
```

## Quick Start (3 Terminals)

### Terminal 1 — Go WhatsApp Bridge (port 8080)

```bash
cd whatsapp-mcp/whatsapp-bridge
./wa-bridge
```

### Terminal 2 — Flask Backend (port 3001)

```bash
cd taskdog-backend
venv/bin/python app.py
```

### Terminal 3 — Vite Frontend (port 5173)

```bash
cd taskdog-frontend
npm run dev
```

Open http://localhost:5173/.

## Onboarding

The frontend routes through 3 gates automatically. For manual testing:

```bash
# Gate A — Check health
curl http://localhost:3001/api/health

# Gate B — Bridge status
curl http://localhost:3001/api/bridge/status

# Gate C — Classify and whitelist
curl -X POST http://localhost:3001/api/chats/classify | jq '.chats[:5]'
curl -X POST http://localhost:3001/api/groups/whitelist \
  -H 'Content-Type: application/json' \
  -d '{"jids":["120363123456@g.us"]}'
```

## Pipeline Stages

```bash
# Stage 1 — Discover tasks
curl -X POST http://localhost:3001/api/pipeline/discover \
  -H 'Content-Type: application/json' \
  -d '{"group_jids":["120363123456@g.us"]}'

# Stage 2 — Refresh tasks
curl -X POST http://localhost:3001/api/pipeline/refresh \
  -H 'Content-Type: application/json' \
  -d '{"group_jids":["120363123456@g.us"]}'

# Stage 3 — Deep-dive a task
TASK_ID=$(curl -s http://localhost:3001/api/dashboard | jq -r '.tasks[0].id')
curl -X POST http://localhost:3001/api/pipeline/deep-dive \
  -H 'Content-Type: application/json' \
  -d "{\"task_id\":\"$TASK_ID\"}"

# Stage 4 — Dashboard
curl http://localhost:3001/api/dashboard | jq .
```

## Nudge Generation

```bash
# Generate nudges for a task
curl -X POST http://localhost:3001/api/nudge/generate \
  -H 'Content-Type: application/json' \
  -d "{\"task_id\":\"$TASK_ID\"}"

# Persona management
curl -X GET http://localhost:3001/api/persona
curl -X POST http://localhost:3001/api/persona \
  -H 'Content-Type: application/json' \
  -d '{"persona":"Write concisely, use bullet points."}'
curl -X POST http://localhost:3001/api/persona/generate
```

## Testing

```bash
# v2 tests (30 tests, all pass)
DATABASE_PATH_V2=$(mktemp) DATABASE_PATH=$(mktemp) cd taskdog-backend && venv/bin/python -m unittest tests.test_v2 -v

# v1 tests
DATABASE_PATH=$(mktemp) cd taskdog-backend && venv/bin/python -m unittest tests.test_api -v

# E2E smoke test (all services must be running)
cd taskdog-backend && bash tests/e2e_v2.sh

# Frontend build check
cd taskdog-frontend && npx vite build
```

## DB Inspection

```bash
sqlite3 taskdog-backend/taskdog_v2.db "SELECT jid, name, category, tldr FROM groups;"
sqlite3 taskdog-backend/taskdog_v2.db "SELECT id, title, status, importance, assignee FROM tasks ORDER BY importance DESC;"
sqlite3 taskdog-backend/taskdog_v2.db "SELECT COUNT(*) FROM task_messages;"
```
