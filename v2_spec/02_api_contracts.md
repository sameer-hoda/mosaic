# TaskDog v2 — API Contracts

**Backend base URL:** `http://localhost:3001`
**Go bridge base URL:** `http://localhost:8080`

All new v2 endpoints are under `/api/`. Existing v1 endpoints (`/api/bridge/status`, `/api/chats/classify`, `/api/chats/classify/stream`, `/api/send`, `/api/history`, `/api/groups`) remain unchanged.

---

## Section 1: Onboarding Endpoints

### `GET /api/health`
Combined health check. Returns Gemini key status and bridge status in one call so the frontend can decide which onboarding gate to show.

**Response:**
```json
{
  "ok": true,
  "gemini_key_set": true,
  "gemini_key_preview": "AIza…xyz",
  "bridge_status": "connected"
}
```
- `gemini_key_set`: `true` if `GEMINI_API_KEY` env var is non-empty.
- `gemini_key_preview`: First 4 + last 3 chars if set, else empty string.
- `bridge_status`: `"connected"` | `"pairing"` | `"offline"` — same logic as v1's `/api/bridge/status`.

---

### `POST /api/setup/validate-key`
Validates a candidate Gemini API key by calling the Gemini models list endpoint.

**Request:**
```json
{
  "key": "AIzaSy..."
}
```

**Response (valid):**
```json
{
  "ok": true,
  "preview": "AIza…xyz"
}
```

**Response (invalid):**
```json
{
  "ok": false,
  "error": "Invalid key (rejected by Gemini)"
}
```

**Implementation:** `GET https://generativelanguage.googleapis.com/v1beta/models?key=...` → 200 = valid, 400/403 = invalid. Timeout 10s. Does NOT persist the key — persistence is the shell's job (Keychain).

---

### `POST /api/groups/whitelist`
Saves the user's selected groups for task monitoring.

**Request:**
```json
{
  "jids": ["120363123456@g.us", "120363789012@g.us"]
}
```

**Response:**
```json
{
  "ok": true,
  "count": 2
}
```

**Side effects:**
- For each JID: resolves the chat name from `messages.db`, inserts into `groups` table.
- If a group already exists, updates its `category` and `tldr` from the `chat_classifications` cache.
- Returns count of groups saved.

---

### `GET /api/groups`
Returns all whitelisted groups (same endpoint as v1, now reads from v2 `groups` table).

**Response:**
```json
{
  "ok": true,
  "groups": [
    {
      "jid": "120363123456@g.us",
      "name": "Product Team",
      "category": "Work",
      "tldr": "Q3 roadmap discussions",
      "whitelisted_at": "2026-06-20T10:00:00",
      "task_count": 12,
      "active_count": 8,
      "last_refreshed_at": "2026-06-20T10:30:00"
    }
  ]
}
```

---

## Section 2: Pipeline Endpoints

### `POST /api/pipeline/discover`
Runs Stage 1 (Task Discovery) on one or more groups. Non-streaming variant.

**Request:**
```json
{
  "group_jids": ["120363123456@g.us", "120363789012@g.us"]
}
```

**Response:**
```json
{
  "ok": true,
  "results": [
    {
      "jid": "120363123456@g.us",
      "name": "Product Team",
      "status": "ok",
      "task_count": 8,
      "error": null
    },
    {
      "jid": "120363789012@g.us",
      "name": "Engineering",
      "status": "no_messages",
      "task_count": 0,
      "error": "No messages in last 30 days"
    }
  ],
  "summary": {
    "total_groups": 2,
    "groups_with_tasks": 1,
    "total_tasks_found": 8
  }
}
```

Per-group `status` values: `"ok"` | `"no_messages"` | `"gemini_failed"` | `"save_failed"`.

**Implementation notes:**
- Uses `ThreadPoolExecutor(max_workers=3)` — same concurrency as v1 extract.
- Calls `discover_tasks()` from `utils/gemini_v2.py`.
- Saves tasks + task_messages via `database_v2.py`.
- Updates `groups.last_refreshed_at`.

---

### `POST /api/pipeline/discover/stream`
Streaming variant of Stage 1. Returns Server-Sent Events.

**Events:**
```
event: meta
data: {"total": 2}

event: group
data: {"jid": "120363...", "name": "Product Team", "status": "ok", "task_count": 8}

event: group
data: {"jid": "120363...", "name": "Engineering", "status": "no_messages", "task_count": 0, "error": "..."}

event: done
data: {"ok": true, "total_groups": 2, "groups_with_tasks": 1, "total_tasks_found": 8}
```

**Frontend usage:** Show a progress bar with group chips — each lights up green/yellow/red as events arrive.

---

### `POST /api/pipeline/refresh`
Runs Stage 2 (Task Refresh) on one or more groups. Non-streaming variant.

**Request:**
```json
{
  "group_jids": ["120363123456@g.us"]
}
```

**Response:**
```json
{
  "ok": true,
  "results": [
    {
      "jid": "120363123456@g.us",
      "name": "Product Team",
      "status": "ok",
      "tasks_updated": 5,
      "tasks_completed": 2,
      "tasks_archived": 1,
      "new_tasks_found": 3,
      "error": null
    }
  ]
}
```

**Implementation notes:**
- Fetches new messages since `groups.last_refreshed_at` using `fetch_chat_messages_since()`.
- Fetches current tasks for the group via `get_tasks_for_refresh()` → serializes as JSON.
- Sends both to Gemini via `refresh_tasks()`.
- Applies status updates, archives, creates new tasks.
- Updates `groups.last_refreshed_at`.

---

### `POST /api/pipeline/refresh/stream`
Streaming variant of Stage 2.

**Events:**
```
event: meta
data: {"total_groups": 1, "total_known_tasks": 8}

event: task
data: {"task_id": "uuid-1", "title": "Q3 budget approval", "status_update": "still_active", "progress_note": "Priya shared updated numbers"}

event: task
data: {"task_id": "uuid-2", "title": "Design sprint planning", "status_update": "completed"}

event: new_task
data: {"task_id": "uuid-9", "title": "Vendor evaluation for analytics tool", "importance": 4}

event: done
data: {"ok": true, "updated": 7, "completed": 1, "archived": 0, "new": 1}
```

**Frontend usage:** Show individual task status changes as they stream in. Completed/archived tasks get a strike-through animation.

---

### `POST /api/pipeline/deep-dive`
Runs Stage 3 (Task Deep-Dive) on a single task. Synchronous — no streaming (this is a single 5-20s Gemini call).

**Request:**
```json
{
  "task_id": "uuid-1"
}
```

**Response:**
```json
{
  "ok": true,
  "task": {
    "id": "uuid-1",
    "title": "Q3 budget approval",
    "status": "active",
    "importance": 4,
    "assignee": "Priya",
    "context": "Priya asked for budget sign-off on April 12th...",
    "wiki": "## Q3 Budget Approval\n\nThe Q3 budget approval process began on April 12th when Priya...\n\n### Current Status\n...\n\n### Next Steps\n...",
    "people": [
      {"name": "Priya", "role": "assignee", "jid": "919967151186@s.whatsapp.net"},
      {"name": "Rahul", "role": "approver", "jid": "919876543210@s.whatsapp.net"}
    ],
    "progress_log": [
      {"date": "2026-06-10", "summary": "Priya shared initial wireframes."},
      {"date": "2026-06-15", "summary": "Revised wireframes posted."}
    ],
    "blockers": [
      {"description": "Waiting on legal approval", "raised_by": "Priya", "date": "2026-06-12"}
    ],
    "decisions": [
      {"description": "Budget capped at ₹2.4L", "made_by": "Sameer", "date": "2026-06-11"}
    ],
    "last_deep_dived_at": "2026-06-20T11:00:00",
    "created_at": "2026-06-20T10:00:00",
    "updated_at": "2026-06-20T11:00:00"
  }
}
```

**Error response:**
```json
{
  "ok": false,
  "error": "Gemini deep-dive failed after 3 attempts: timeout"
}
```

---

## Section 3: Dashboard Endpoints

### `GET /api/dashboard`
Returns all tasks with stats, sorted by importance (high → low).

**Query params:**
- `group_jid` (optional) — filter to one group.

**Response:**
```json
{
  "ok": true,
  "tasks": [
    {
      "id": "uuid-1",
      "group_jid": "120363123456@g.us",
      "group_name": "Product Team",
      "title": "Q3 budget approval",
      "status": "active",
      "importance": 4,
      "assignee": "Priya",
      "latest_progress": "Priya shared updated numbers",
      "has_deep_dive": false,
      "days_since_refresh": 1,
      "created_at": "2026-06-20T10:00:00"
    }
  ],
  "stats": {
    "active": 8,
    "completed": 3,
    "archived": 2,
    "total": 13,
    "high_priority": 4,
    "followups_sent": 12
  }
}
```

- `latest_progress`: Last entry from `progress_log` JSON array, or `null`.
- `has_deep_dive`: `true` if `last_deep_dived_at` is not null.
- `high_priority`: Count of tasks with importance >= 4.

---

### `GET /api/tasks/{task_id}`
Full detail for a single task (same shape as Stage 3 response). Returns all fields including wiki, people, progress_log, blockers, decisions.

**Response:** Same as the `task` object in `POST /api/pipeline/deep-dive` response.

---

### `GET /api/tasks/{task_id}/messages`
Returns messages tagged as relevant to a task.

**Response:**
```json
{
  "ok": true,
  "messages": [
    {
      "id": 1,
      "message_content": "Hey Priya, what's the status on the Q3 budget?",
      "sender_name": "Sameer",
      "message_time": "2026-06-15T14:30:00+05:30",
      "relevance": 0.85
    }
  ]
}
```

---

### `PATCH /api/tasks/{task_id}`
Manual override for task fields. Currently only `status` and `importance` are user-editable.

**Request:**
```json
{
  "status": "completed",
  "importance": 3
}
```

**Response:**
```json
{"ok": true}
```

**Validation:**
- `status` must be one of `active`, `completed`, `archived`.
- `importance` must be 1-5.
- All fields are optional — only provided fields are updated.

---

## Section 4: Unchanged v1 Endpoints

These endpoints are reused as-is from v1's `routes/tasks.py`:

| Endpoint | Used In |
|---|---|
| `GET /api/bridge/status` | Onboarding Gate B |
| `POST /api/chats/classify` | Onboarding Gate C (classifier) |
| `POST /api/chats/classify/stream` | Onboarding Gate C (streaming variant) |
| `POST /api/send` | Dashboard — send nudge |
| `GET /api/history` | Dashboard — view sent nudges (reads v2 followup_history) |

---

## Section 5: SSE Streaming Pattern

Both `discover/stream` and `refresh/stream` use the same SSE pattern from v1 (`/api/chats/classify/stream`):

```python
def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"

response = Response(stream_with_context(generate()), mimetype='text/event-stream')
response.headers['Cache-Control'] = 'no-cache'
response.headers['X-Accel-Buffering'] = 'no'
```

**Frontend consumption:**
```js
const source = new EventSource('/api/pipeline/discover/stream', {
  method: 'POST',
  body: JSON.stringify({group_jids: [...]})
});
source.addEventListener('meta', (e) => { /* show total */ });
source.addEventListener('group', (e) => { /* update progress bar */ });
source.addEventListener('done', (e) => { /* finish */ });
source.addEventListener('error', (e) => { /* handle */ });
```