# TaskDog v2 — Database Schema

## Database file

**Path:** `taskdog-backend/taskdog_v2.db`
**Engine:** SQLite 3
**Creation:** Auto-created by `models/database_v2.py` on first Flask startup if the file doesn't exist.
**Coexistence:** Lives alongside v1's `taskdog.db`. No conflict. v2 routes use `database_v2.py`, v1 routes use `database.py`.

---

## Full DDL

```sql
-- Groups whitelisted by the user for task monitoring.
-- Populated by POST /api/groups/whitelist during onboarding.
-- Updated by pipeline stages (last_refreshed_at).
CREATE TABLE groups (
    jid               TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    category          TEXT NOT NULL CHECK (category IN ('Work', 'Personal')),
    tldr              TEXT,
    whitelisted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_refreshed_at TIMESTAMP
);

-- Tasks extracted from group chats.
-- Flat model — no themes table. Each task belongs directly to a group.
-- Populated by Stage 1 (discovery), updated by Stage 2 (refresh).
-- Enriched by Stage 3 (deep-dive) with wiki, people, progress_log,
-- blockers, and decisions.
CREATE TABLE tasks (
    id                 TEXT PRIMARY KEY,          -- UUID v4
    group_jid          TEXT NOT NULL REFERENCES groups(jid) ON DELETE CASCADE,
    title              TEXT NOT NULL,
    status             TEXT NOT NULL CHECK (status IN ('active', 'completed', 'archived')),
    importance         INTEGER NOT NULL DEFAULT 3 CHECK (importance BETWEEN 1 AND 5),
    assignee           TEXT,
    context            TEXT,                      -- initial context from discovery
    wiki               TEXT,                      -- populated by Stage 3 deep-dive
    people             TEXT DEFAULT '[]',          -- JSON array of {name, role, jid}
    progress_log       TEXT DEFAULT '[]',          -- JSON array of {date, summary}
    blockers           TEXT DEFAULT '[]',          -- JSON array of {description, raised_by, date}
    decisions          TEXT DEFAULT '[]',          -- JSON array of {description, made_by, date}
    last_deep_dived_at TIMESTAMP,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages from the group transcript that Gemini tagged as relevant to
-- a specific task during discovery (Stage 1).
-- Used to provide context snippets in the dashboard without re-sending
-- the full transcript to Gemini.
CREATE TABLE task_messages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id          TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    message_content  TEXT,
    sender_name      TEXT,
    message_time     TEXT,         -- WhatsApp timestamp string
    relevance        REAL DEFAULT 0.0  -- 0.0–1.0 relevance score from Gemini
);

-- Log of every nudge/follow-up message sent via the app.
-- Identical to v1's nudge_history table.
CREATE TABLE followup_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id        TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    message_text   TEXT NOT NULL,
    recipient_jid  TEXT NOT NULL,
    sent_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## JSON Column Schemas

These are stored as TEXT in SQLite. Python serializes/deserializes with `json.dumps`/`json.loads`.

### `tasks.people`
```json
[
  {"name": "Priya", "role": "assignee", "jid": "919967151186@s.whatsapp.net"},
  {"name": "Rahul", "role": "reviewer", "jid": "919876543210@s.whatsapp.net"}
]
```

### `tasks.progress_log`
```json
[
  {"date": "2026-06-10", "summary": "Priya shared initial wireframes in the group."},
  {"date": "2026-06-12", "summary": "Team reviewed. Rahul requested changes to the nav."},
  {"date": "2026-06-15", "summary": "Revised wireframes posted. Awaiting sign-off."}
]
```

### `tasks.blockers`
```json
[
  {"description": "Waiting on legal approval for data sharing clause", "raised_by": "Priya", "date": "2026-06-12"},
  {"description": "Design team bandwidth — no capacity until June 18", "raised_by": "Rahul", "date": "2026-06-14"}
]
```

### `tasks.decisions`
```json
[
  {"description": "Q3 budget capped at ₹2.4L for the design sprint", "made_by": "Sameer", "date": "2026-06-11"},
  {"description": "P0 launch moved from June 30 to July 15", "made_by": "Priya", "date": "2026-06-13"}
]
```

---

## Indexes

```sql
CREATE INDEX idx_tasks_group_jid    ON tasks(group_jid);
CREATE INDEX idx_tasks_status       ON tasks(status);
CREATE INDEX idx_tasks_importance   ON tasks(importance DESC);
CREATE INDEX idx_task_messages_task ON task_messages(task_id);
CREATE INDEX idx_followup_task      ON followup_history(task_id);
```

The importance index supports the dashboard sort (high → low importance). The group_jid index supports filtering by group. Status index supports the active/completed/archived counts in stats.

---

## v1 vs v2 Schema Comparison

| v1 Table | v2 Equivalent | Changes |
|---|---|---|
| `whitelisted_groups` | `groups` | Renamed. Added `last_refreshed_at`. |
| `themes` | — | **Removed.** Tasks are flat, keyed by group directly. |
| `tasks` | `tasks` | Complete rewrite. New fields: `wiki`, `people`, `progress_log`, `blockers`, `decisions`, `last_deep_dived_at`, `importance`. Removed: `theme_id`, `response_concise`, `response_moderate`, `response_with_context`. Status values changed from `not started`/`pending`/`done` to `active`/`completed`/`archived`. |
| `nudge_history` | `followup_history` | Renamed. Identical schema. |
| `chat_classifications` | — | Stays in v1 database.py. v2 reuses v1's classify endpoint. |
| — | `task_messages` | **New.** Message-to-task relevance mapping. |

---

## Database helpers to implement (`models/database_v2.py`)

```python
# Required functions — all SQLite CRUD for v2 schema:

init_db_v2()                          # CREATE TABLE IF NOT EXISTS for all 4 tables + indexes
get_db_connection_v2()                # sqlite3.connect(taskdog_v2.db) with row_factory

# Groups
insert_groups(jids, names, categories, tldrs)  # INSERT OR REPLACE into groups
get_groups()                                   # SELECT all from groups
get_group(jid)                                 # SELECT one
update_group_refreshed_at(jid)                 # SET last_refreshed_at = now

# Tasks — Discovery (Stage 1)
insert_tasks(task_list)                         # Bulk insert from Gemini discovery output
save_task(task_dict)                            # Single INSERT OR REPLACE
get_tasks_by_group(jid, status_filter=None)     # Tasks for one group, optional status filter

# Tasks — Refresh (Stage 2)
get_tasks_for_refresh(group_jid)                # Returns current tasks as JSON-ready list
update_task_status(task_id, new_status)         # active → completed / archived
update_task_importance(task_id, importance)     # Manual or AI override
update_task_progress(task_id, progress_note)    # Append to progress_log JSON

# Tasks — Deep-Dive (Stage 3)
get_task(task_id)                               # Full single task
update_task_deep_dive(task_id, wiki, people,    # Save Stage 3 output
                      progress_log, blockers,
                      decisions, importance)

# Tasks — Dashboard (Stage 4)
get_all_tasks(group_jid=None)                   # All tasks, grouped by importance DESC
get_dashboard_stats()                           # {active: N, completed: N, archived: N, total: N}

# Task Messages
insert_task_messages(task_id, messages)         # Bulk insert from Gemini relevance tagging
get_task_messages(task_id)                      # All messages tagged for a task

# Followup History (identical to v1)
record_followup(task_id, text, recipient_jid)
get_followup_history(limit=50)

# Utility
get_user_identity()                             # Same as v1 — reads whatsmeow_device
```

---

## Reused from v1 `database.py` (unchanged)

These functions are called by v2 routes but live in v1's `database.py`:

| Function | Used By |
|---|---|
| `fetch_top_chats(limit)` | Onboarding — chat list for whitelisting |
| `fetch_chat_messages(jid, limit)` | Classifier — last 25 messages |
| `fetch_chat_messages_since(jid, days)` | Pipeline stages — full transcript |
| `get_whatsapp_db_conn()` | All of the above — WhatsApp DB access |