---
type: Component
title: Database v2 Module
description: SQLite schema + CRUD for v2, with thread-safe write lock, WAL mode, and 30s busy timeout.
resource: file://taskdog-backend/models/database_v2.py
tags: [python, sqlite, database]
---

# Database v2 Module

The v2 database module at `models/database_v2.py` defines the schema, CRUD operations, and concurrency safety for the v2 SQLite database (`taskdog_v2.db`).

## Concurrency Safety

Three mechanisms prevent "database is locked" errors from concurrent writes:

1. **WAL Journal Mode**: `PRAGMA journal_mode = WAL` — allows concurrent reads during writes.
2. **Busy Timeout**: `PRAGMA busy_timeout = 30000` — waits up to 30 seconds for the lock.
3. **Write Lock**: `threading.Lock` (`_write_lock`) wraps all writes via `with _write_lock:` blocks.

## Schema

Four tables:

| Table | Purpose | Key Columns |
|---|---|---|
| `groups` | Whitelisted WhatsApp groups | `jid` (PK), `name`, `category` (CHECK 'Work'/'Personal'), `tldr`, `whitelisted_at`, `last_refreshed_at` |
| `tasks` | Discovered tasks | `id` (UUID PK), `group_jid` (FK CASCADE), `title`, `status` (CHECK active/completed/archived), `importance` (1-5), `assignee`, `context`, `people`, `progress_log`, `blockers`, `decisions`, `wiki`, `last_deep_dived_at` |
| `task_messages` | Messages tagged to tasks | `id` (PK AUTOINCREMENT), `task_id` (FK CASCADE), `message_content`, `sender_name`, `message_time`, `relevance` (0.0-1.0) |
| `followup_history` | Sent followup nudges | `id` (PK AUTOINCREMENT), `task_id` (FK CASCADE), `message_text`, `recipient_jid`, `sent_at` |

## CRUD Operations

All write operations use `with _write_lock:` context manager directly:

- `insert_groups()`, `get_groups()`, `get_group()`, `delete_groups_not_in()`, `update_group_refreshed_at()`
- `insert_tasks()` (with dedup via token-overlap >70%), `save_task()`, `get_tasks_by_group()`, `get_tasks_for_refresh()`
- `update_task_status()`, `update_task_importance()`, `update_task_progress()`, `update_task_deep_dive()`
- `insert_task_messages()`, `get_task_messages()`
- `record_followup()`, `get_followup_history()`, `get_dashboard_stats()`
- `get_all_tasks()`, `get_task()`, `get_task_group_jid()`, `get_group_last_refreshed()`
- `backfill_resolve_names()` — one-shot utility to normalize JID/LID references

## Dedup Strategy

Task insertion uses token-overlap dedup: if >70% of tokens in the new title overlap with any existing title for the same group, the task is skipped. This prevents duplicate creation during refresh/discovery.

## Environment Variable

Path controlled by `DATABASE_PATH_V2` env var, defaults to `taskdog_v2.db`:

```python
DB_PATH = os.environ.get("DATABASE_PATH_V2", "taskdog_v2.db")
```
