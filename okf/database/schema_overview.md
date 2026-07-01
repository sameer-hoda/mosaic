---
type: Concept
title: Database Schema Overview
description: The v2 database has 4 tables — groups, tasks, task_messages, followup_history. No themes table; tasks are flat and keyed to a group via group_jid.
tags: [database, schema, design]
---

# Schema Overview

## Entity Relationship

```
groups (1) ────── (N) tasks
                  tasks (1) ────── (N) task_messages
                  tasks (1) ────── (N) followup_history
```

All foreign keys use `ON DELETE CASCADE`.

## Key Design Decisions

- **No themes table** — tasks are flat, directly keyed to a group via `group_jid`.
- **Deep-dive columns** are TEXT fields in the `tasks` table: `wiki` (Markdown), `people` (JSON), `progress_log` (JSON), `blockers` (JSON), `decisions` (JSON). All default to `[]`.
- **Task dedup**: Token-overlap >70% prevents duplicate task creation within the same group.
- **Task statuses**: `active`, `completed`, `archived` (CHECK constraint).
- **Importance score**: 1-5, AI-assessed, user-overridable via PATCH.
- **No migration from v1** — v2 starts fresh; users re-whitelist groups.

## DDL

```sql
CREATE TABLE IF NOT EXISTS groups (
    jid               TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    category          TEXT NOT NULL CHECK (category IN ('Work', 'Personal')),
    tldr              TEXT,
    whitelisted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_refreshed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id                 TEXT PRIMARY KEY,
    group_jid          TEXT NOT NULL REFERENCES groups(jid) ON DELETE CASCADE,
    title              TEXT NOT NULL,
    status             TEXT NOT NULL CHECK (status IN ('active', 'completed', 'archived')),
    importance         INTEGER NOT NULL DEFAULT 3 CHECK (importance BETWEEN 1 AND 5),
    assignee           TEXT,
    context            TEXT,
    wiki               TEXT,
    people             TEXT DEFAULT '[]',
    progress_log       TEXT DEFAULT '[]',
    blockers           TEXT DEFAULT '[]',
    decisions          TEXT DEFAULT '[]',
    last_deep_dived_at TIMESTAMP,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tasks_group_jid    ON tasks(group_jid);
CREATE INDEX IF NOT EXISTS idx_tasks_status       ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_importance   ON tasks(importance DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_group_title ON tasks(group_jid, title);

CREATE TABLE IF NOT EXISTS task_messages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id          TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    message_content  TEXT,
    sender_name      TEXT,
    message_time     TEXT,
    relevance        REAL DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS idx_task_messages_task ON task_messages(task_id);

CREATE TABLE IF NOT EXISTS followup_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id        TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    message_text   TEXT NOT NULL,
    recipient_jid  TEXT NOT NULL,
    sent_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_followup_task ON followup_history(task_id);
```
