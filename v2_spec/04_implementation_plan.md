# TaskDog v2 — Implementation Plan

9 stages, ordered. Each stage produces a working artifact testable independently before the next stage begins. Everything builds on the v1 infrastructure already in place.

---

## Stage A — Database Schema & Helpers

**Goal:** Standalone database module with schema + CRUD. No routes, no Gemini. Pure SQLite.

**Files to create:**
- `taskdog-backend/models/database_v2.py` — full `init_db_v2()` + all CRUD functions listed in `01_database_schema.md`.

**Files to modify:**
- None. This is a new file that coexists with `database.py`.

**Reused from v1:**
- `database.py` for `fetch_top_chats`, `fetch_chat_messages`, `fetch_chat_messages_since`, `get_whatsapp_db_conn`, `get_user_identity`.

**Functions to implement (see 01_database_schema.md for signatures):**

```
init_db_v2(), get_db_connection_v2()
insert_groups(), get_groups(), get_group(), update_group_refreshed_at()
insert_tasks(), save_task(), get_tasks_by_group()
get_tasks_for_refresh(), update_task_status(), update_task_importance()
update_task_progress(), get_task(), update_task_deep_dive()
get_all_tasks(), get_dashboard_stats()
insert_task_messages(), get_task_messages()
record_followup(), get_followup_history()
```

**Test:** Run `init_db_v2()` → `taskdog_v2.db` created with all 4 tables + indexes. Insert a group + task, read it back.

**Verification command:**
```bash
cd taskdog-backend
rm -f taskdog_v2.db
venv/bin/python -c "from models.database_v2 import init_db_v2; init_db_v2()"
sqlite3 taskdog_v2.db ".schema"
```

---

## Stage B — Onboarding Endpoints

**Goal:** Backend endpoints for the 3-gate onboarding flow. Gemini key validation + group whitelisting.

**Files to create:**
- `taskdog-backend/routes/setup.py` — `/api/health`, `/api/setup/validate-key`
- `taskdog-backend/routes/groups.py` — `/api/groups/whitelist`, `GET /api/groups`

**Files to modify:**
- `taskdog-backend/app.py` — register `setup_bp` and `groups_bp`

**Implementation:**

### `routes/setup.py`
```python
from flask import Blueprint, request, jsonify
import os, requests, socket, subprocess

bp = Blueprint("setup_v2", __name__, url_prefix="/api")

@bp.route("/health")
def health():
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    # Bridge status check (reuse v1's is_port_open / is_bridge_process_running logic)
    # ... returns {ok, gemini_key_set, gemini_key_preview, bridge_status}

@bp.route("/setup/validate-key", methods=["POST"])
def validate_key():
    # Call Gemini models list endpoint with the candidate key
    # Return {ok, preview} or {ok: false, error}
```

### `routes/groups.py`
```python
from flask import Blueprint, request, jsonify
from models.database_v2 import insert_groups, get_groups

bp = Blueprint("groups_v2", __name__, url_prefix="/api")

@bp.route("/groups/whitelist", methods=["POST"])
def whitelist():
    # Receive {jids: [...]}, resolve names from messages.db, insert into groups table
    # Return {ok, count}

@bp.route("/groups", methods=["GET"])
def list_groups():
    # Return all whitelisted groups with task counts from v2 DB
```

### `app.py` additions
```python
from routes.setup import bp as setup_bp
from routes.groups import bp as groups_bp
app.register_blueprint(setup_bp)
app.register_blueprint(groups_bp)
```

**Test:**
```bash
curl -X POST http://localhost:3001/api/setup/validate-key -H 'Content-Type: application/json' -d '{"key":"AIzaSy..."}'
curl http://localhost:3001/api/health
curl -X POST http://localhost:3001/api/groups/whitelist -H 'Content-Type: application/json' -d '{"jids":["120363...@g.us"]}'
curl http://localhost:3001/api/groups
```

---

## Stage C — Task Discovery (Stage 1)

**Goal:** `/api/pipeline/discover` and `/api/pipeline/discover/stream` — extract all tasks from a group's 30-day transcript.

**Files to create:**
- `taskdog-backend/utils/gemini_v2.py` — `discover_tasks()` function
- `taskdog-backend/routes/pipeline.py` — `/discover` + `/discover/stream` routes

**Files to modify:**
- `taskdog-backend/app.py` — register `pipeline_bp`

### `utils/gemini_v2.py`
```python
import os, json, sys, time, requests
from typing import Dict, List
from dotenv import load_dotenv

# Reuse _call_gemini() from gemini_client.py OR copy/modify it here
# Implement: discover_tasks(group_name: str, messages: List[Dict]) -> Dict
# Uses Prompt 1 from 03_gemini_prompts.md
# Returns {"tasks": [...]} or {"tasks": [], "error": "..."}
```

### `routes/pipeline.py`
```python
from flask import Blueprint, request, jsonify, Response, stream_with_context
from models.database import fetch_chat_messages_since, get_user_identity
from models.database_v2 import insert_tasks, insert_task_messages, update_group_refreshed_at, get_tasks_by_group
from utils.gemini_v2 import discover_tasks

bp = Blueprint("pipeline", __name__, url_prefix="/api/pipeline")

@bp.route("/discover", methods=["POST"])
def discover():
    # {group_jids: [...]}
    # For each group: fetch 30-day messages → discover_tasks() → save to DB
    # ThreadPoolExecutor(max_workers=3)
    # Return per-group results

@bp.route("/discover/stream", methods=["POST"])
def discover_stream():
    # Same logic, SSE streaming: meta → group (per group) → done
```

**Test:**
```bash
# First whitelist a group
curl -X POST http://localhost:3001/api/groups/whitelist -H 'Content-Type: application/json' -d '{"jids":["120363...@g.us"]}'

# Run discovery
curl -X POST http://localhost:3001/api/pipeline/discover -H 'Content-Type: application/json' -d '{"group_jids":["120363...@g.us"]}'

# Check tasks in DB
sqlite3 taskdog_v2.db "SELECT id, title, status, importance FROM tasks;"
```

---

## Stage D — Task Refresh (Stage 2)

**Goal:** `/api/pipeline/refresh` and `/api/pipeline/refresh/stream` — delta update of known tasks.

**Files to modify:**
- `taskdog-backend/utils/gemini_v2.py` — add `refresh_tasks()` function
- `taskdog-backend/routes/pipeline.py` — add `/refresh` + `/refresh/stream` routes

### `utils/gemini_v2.py` additions
```python
def refresh_tasks(group_name: str, current_tasks: List[Dict], new_messages: List[Dict]) -> Dict:
    # Uses Prompt 2 from 03_gemini_prompts.md
    # current_tasks: serialized list of {id, title, status, assignee, importance}
    # Returns {"task_updates": [...], "new_tasks": [...]}
```

### `routes/pipeline.py` additions
```python
@bp.route("/refresh", methods=["POST"])
def refresh():
    # {group_jids: [...]}
    # For each group:
    #   1. Get current tasks from DB → get_tasks_for_refresh()
    #   2. Get new messages since last_refreshed_at → fetch_chat_messages_since()
    #   3. refresh_tasks(group_name, current_tasks, new_messages)
    #   4. Apply updates: status, importance, progress notes
    #   5. Create new tasks (replace "new-001" IDs with UUIDs)
    #   6. Update groups.last_refreshed_at

@bp.route("/refresh/stream", methods=["POST"])
def refresh_stream():
    # SSE: meta → task event per update → new_task events → done
```

**Test:**
```bash
# Run refresh
curl -X POST http://localhost:3001/api/pipeline/refresh -H 'Content-Type: application/json' -d '{"group_jids":["120363...@g.us"]}'

# Verify tasks updated
sqlite3 taskdog_v2.db "SELECT id, title, status, updated_at FROM tasks;"
```

---

## Stage E — Task Deep-Dive (Stage 3)

**Goal:** `/api/pipeline/deep-dive` — comprehensive analysis of a single task.

**Files to modify:**
- `taskdog-backend/utils/gemini_v2.py` — add `deep_dive_task()` function
- `taskdog-backend/routes/pipeline.py` — add `/deep-dive` route

### `utils/gemini_v2.py` additions
```python
def deep_dive_task(task: Dict, full_messages: List[Dict]) -> Dict:
    # Uses Prompt 3 from 03_gemini_prompts.md
    # task dict: {id, title, status, importance, assignee, context}
    # full_messages: ALL messages from the group (not just recent)
    # Returns {wiki, people, progress_log, blockers, decisions, importance}
```

### `routes/pipeline.py` additions
```python
@bp.route("/deep-dive", methods=["POST"])
def deep_dive():
    # {task_id}
    # 1. Get task from DB → get_task()
    # 2. Get group_jid from task → fetch ALL messages (no date filter)
    #    Use fetch_chat_messages_since() with days=365 (effectively all)
    # 3. deep_dive_task(task, full_messages)
    # 4. update_task_deep_dive() → save wiki, people, progress_log, blockers, decisions
    # 5. Return full task object
```

**Test:**
```bash
curl -X POST http://localhost:3001/api/pipeline/deep-dive -H 'Content-Type: application/json' -d '{"task_id":"<uuid>"}'

# Verify deep-dive fields
sqlite3 taskdog_v2.db "SELECT id, wiki, people, progress_log FROM tasks WHERE id='<uuid>';"
```

---

## Stage F — Dashboard API

**Goal:** Task listing + detail + CRUD endpoints. No Gemini calls. Pure DB reads.

**Files to create:**
- `taskdog-backend/routes/dashboard.py` — `GET /api/dashboard`, `GET /api/tasks/{id}`, `GET /api/tasks/{id}/messages`, `PATCH /api/tasks/{id}`

**Files to modify:**
- `taskdog-backend/app.py` — register `dashboard_bp`

### `routes/dashboard.py`
```python
from flask import Blueprint, request, jsonify
from models.database_v2 import get_all_tasks, get_dashboard_stats, get_task, get_task_messages, update_task_status, update_task_importance

bp = Blueprint("dashboard_v2", __name__, url_prefix="/api")

@bp.route("/dashboard")
def dashboard():
    group_jid = request.args.get("group_jid")
    tasks = get_all_tasks(group_jid)
    stats = get_dashboard_stats()
    # Enrich tasks: latest_progress from progress_log JSON, has_deep_dive, etc.

@bp.route("/tasks/<task_id>")
def task_detail(task_id):
    return jsonify({"ok": True, "task": get_task(task_id)})

@bp.route("/tasks/<task_id>/messages")
def task_messages(task_id):
    return jsonify({"ok": True, "messages": get_task_messages(task_id)})

@bp.route("/tasks/<task_id>", methods=["PATCH"])
def update_task(task_id):
    data = request.get_json() or {}
    if "status" in data:
        update_task_status(task_id, data["status"])
    if "importance" in data:
        update_task_importance(task_id, data["importance"])
    return jsonify({"ok": True})
```

**Test:**
```bash
curl http://localhost:3001/api/dashboard
curl http://localhost:3001/api/tasks/<uuid>
curl -X PATCH http://localhost:3001/api/tasks/<uuid> -H 'Content-Type: application/json' -d '{"status":"completed"}'
```

---

## Stage G — Integration Tests

**Goal:** Automated tests covering the full pipeline.

**Files to create:**
- `taskdog-backend/tests/test_v2.py`

**Test cases:**
```python
class TestDatabaseV2(unittest.TestCase):
    def test_init_db_creates_tables(self): ...
    def test_insert_and_get_groups(self): ...
    def test_insert_and_get_tasks(self): ...
    def test_update_task_status(self): ...
    def test_get_dashboard_stats(self): ...
    def test_progress_log_json(self): ...

class TestSetupRoutes(unittest.TestCase):
    def test_health_endpoint(self): ...
    def test_validate_key_invalid(self): ...
    def test_whitelist_groups(self): ...

class TestDiscovery(unittest.TestCase):
    @patch('utils.gemini_v2.discover_tasks')
    def test_discover_saves_tasks(self, mock_discover): ...
    def test_discover_empty_messages(self): ...

class TestRefresh(unittest.TestCase):
    @patch('utils.gemini_v2.refresh_tasks')
    def test_refresh_updates_status(self, mock_refresh): ...
    def test_refresh_creates_new_tasks(self): ...

class TestDeepDive(unittest.TestCase):
    @patch('utils.gemini_v2.deep_dive_task')
    def test_deep_dive_saves_wiki(self, mock_deep_dive): ...

class TestDashboard(unittest.TestCase):
    def test_dashboard_returns_tasks_sorted_by_importance(self): ...
    def test_dashboard_stats(self): ...
    def test_update_task_manual_override(self): ...
```

**Run:**
```bash
cd taskdog-backend
DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_v2 -v
```

---

## Stage H — Frontend Adaptation

**Goal:** Update the React frontend to use v2 data model and new pipeline endpoints.

**Files to create:**
- `taskdog-frontend/src/components/Dashboard.js` — replaces `Kanban.js`
- `taskdog-frontend/src/components/DeepDive.js` — new component
- `taskdog-frontend/src/components/ApiKey.js` — from DISTRIBUTION_PLAN.md
- `taskdog-frontend/src/components/Whitelist.js` — group selection UI

**Files to modify:**
- `taskdog-frontend/src/app.js` — add PHASE.APIKEY, PHASE.WHITELIST, route to new components
- `taskdog-frontend/src/api.js` — add v2 endpoints
- `taskdog-frontend/src/components/Header.js` — add Refresh, Switch API Key buttons

**Dashboard.js states:**
1. Empty state ("No groups whitelisted — go to settings to add groups")
2. No tasks yet ("Click 'Discover Tasks' to scan {group_name}")
3. Task list (cards sorted by importance, with status badges, assignee chips, latest progress)
4. After refresh (tasks animate as they update)

**DeepDive.js states:**
1. Loading ("Analysing task...")
2. Wiki view (rendered Markdown, people list as chips, progress timeline, blockers/decisions as cards)
3. Error state

**Frontend — API client additions to `api.js`:**
```js
health: () => request('/health'),
validateKey: (key) => request('/setup/validate-key', { method:'POST', body:JSON.stringify({key}) }),
whitelistGroups: (jids) => request('/groups/whitelist', { method:'POST', body:JSON.stringify({jids}) }),
discoverTasks: (jids) => request('/pipeline/discover', { method:'POST', body:JSON.stringify({group_jids:jids}) }),
refreshTasks: (jids) => request('/pipeline/refresh', { method:'POST', body:JSON.stringify({group_jids:jids}) }),
deepDive: (taskId) => request('/pipeline/deep-dive', { method:'POST', body:JSON.stringify({task_id:taskId}) }),
getDashboard: (groupJid) => request(`/dashboard${groupJid ? '?group_jid=' + groupJid : ''}`),
getTask: (id) => request(`/tasks/${id}`),
getTaskMessages: (id) => request(`/tasks/${id}/messages`),
updateTask: (id, data) => request(`/tasks/${id}`, { method:'PATCH', body:JSON.stringify(data) }),
```

---

## Stage I — End-to-End Validation

**Goal:** Full smoke test of the complete v2 system end-to-end.

**Prerequisites:**
- Go bridge running on port 8080 (WhatsApp paired)
- Flask backend running on port 3001
- Vite dev server on port 5173

**Test script:**
```bash
#!/bin/bash
BASE="http://localhost:3001"

echo "=== 1. Health check ==="
curl -s $BASE/api/health | jq .

echo "=== 2. Classify chats ==="
curl -s -X POST $BASE/api/chats/classify | jq '.chats[:3]'

echo "=== 3. Whitelist a group ==="
JID=$(curl -s -X POST $BASE/api/chats/classify | jq -r '.chats[0].jid')
curl -s -X POST $BASE/api/groups/whitelist \
  -H 'Content-Type: application/json' \
  -d "{\"jids\":[\"$JID\"]}" | jq .

echo "=== 4. Discover tasks ==="
curl -s -X POST $BASE/api/pipeline/discover \
  -H 'Content-Type: application/json' \
  -d "{\"group_jids\":[\"$JID\"]}" | jq .

echo "=== 5. Dashboard ==="
curl -s $BASE/api/dashboard | jq '.stats'

echo "=== 6. Refresh tasks ==="
curl -s -X POST $BASE/api/pipeline/refresh \
  -H 'Content-Type: application/json' \
  -d "{\"group_jids\":[\"$JID\"]}" | jq .

echo "=== 7. Deep-dive on first task ==="
TASK_ID=$(curl -s $BASE/api/dashboard | jq -r '.tasks[0].id')
curl -s -X POST $BASE/api/pipeline/deep-dive \
  -H 'Content-Type: application/json' \
  -d "{\"task_id\":\"$TASK_ID\"}" | jq '.task.wiki[:200]'

echo "=== ALL CHECKS PASSED ==="
```

---

## Dependency Graph

```
Stage A (database)
  │
  ├──► Stage B (onboarding endpoints)
  │      │
  │      └──► Stage C (discovery) ── requires DB + groups whitelisted
  │             │
  │             ├──► Stage D (refresh) ── requires discovery output in DB
  │             │
  │             ├──► Stage E (deep-dive) ── requires discovery output in DB
  │             │
  │             └──► Stage F (dashboard) ── requires tasks in DB from C/D/E
  │                    │
  │                    ├──► Stage G (tests) ── requires all routes
  │                    │
  │                    └──► Stage H (frontend) ── requires all API endpoints
  │                           │
  │                           └──► Stage I (E2E validation)
```

Stages C, D, E are independent of each other (all need tasks in DB, none depend on each other's output). Stage F depends on at least C being complete. Stage H depends on F. Stage I is the final integration.

---

## File-by-File Summary

| File | Stage | Type | Lines (est.) |
|---|---|---|---|
| `models/database_v2.py` | A | New | ~300 |
| `routes/setup.py` | B | New | ~80 |
| `routes/groups.py` | B | New | ~60 |
| `utils/gemini_v2.py` | C, D, E | New | ~350 |
| `routes/pipeline.py` | C, D, E | New | ~300 |
| `routes/dashboard.py` | F | New | ~80 |
| `tests/test_v2.py` | G | New | ~300 |
| `src/components/Dashboard.js` | H | New | ~300 |
| `src/components/DeepDive.js` | H | New | ~250 |
| `src/components/ApiKey.js` | H | New | ~100 |
| `src/components/Whitelist.js` | H | New | ~150 |
| `src/app.js` | H | Modify | +30 |
| `src/api.js` | H | Modify | +20 |
| `src/components/Header.js` | H | Modify | +15 |
| `app.py` (backend) | B, C, F | Modify | +10 |
| **Total** | | | **~2,350 lines** |