---
type: Concept
title: Tasks Table
description: Discovered tasks with status lifecycle, importance scoring, dedup logic, and deep-dive output columns.
tags: [database, tasks]
---

# Tasks Table

## Columns

| Column | Type | Description |
|---|---|---|
| `id` | TEXT (PK) | UUID v4 |
| `group_jid` | TEXT (FK → groups.jid ON DELETE CASCADE) | Owning group |
| `title` | TEXT | Task title (e.g., "Finalize June communications budget plan") |
| `status` | TEXT | CHECK constrained: `active`, `completed`, or `archived` |
| `importance` | INTEGER | 1-5, AI-assessed. User-overridable via PATCH. |
| `assignee` | TEXT | Responsible person (resolved from JID/LID to human name) |
| `context` | TEXT | Detailed narrative (replaces `description` from v1 — 2-4 sentence summary with asker, history, next step) |
| `wiki` | TEXT | Markdown — deep-dive output (knowledge page) |
| `people` | TEXT | JSON array — defaults to `[]`. People involved with `name` and `role`. |
| `progress_log` | TEXT | JSON array — defaults to `[]`. Timeline with `date` and `summary`. |
| `blockers` | TEXT | JSON array — defaults to `[]`. Blockers with `description`, `raised_by`, `date`. |
| `decisions` | TEXT | JSON array — defaults to `[]`. Decisions with `description`, `made_by`, `date`. |
| `last_deep_dived_at` | TIMESTAMP | When deep-dive was last run (null before first deep-dive) |
| `created_at` | TIMESTAMP | Auto-set on insert |
| `updated_at` | TIMESTAMP | Auto-updated on modification |

## Status Lifecycle

```
active ──► completed
active ──► archived
```

No other transitions are enforced at the DB level. Status changes are made via `PATCH /api/tasks/{id}`.

## Dedup Logic

Task insertion uses token-overlap dedup: >70% token overlap with any existing title for the same group = duplicate, task skipped. A unique index on `(group_jid, title)` is attempted but may fall back silently on existing duplicates.

## Deep-Dive Columns

All 5 deep-dive columns (`wiki`, `people`, `progress_log`, `blockers`, `decisions`) default to `[]` (empty JSON array). Before deep-dive, `last_deep_dived_at` is `NULL`. As of June 20, 2026, all 13 tasks have `NULL` deep-dive columns (no deep-dives performed yet).

## Current State

As of June 20, 2026: 13 tasks, all `active`. Importance distribution: 5 tasks at importance 5, 5 at importance 4, 2 at importance 3, 1 at importance 2.

## Inspection

```bash
sqlite3 taskdog-backend/taskdog_v2.db "SELECT id, title, status, importance, assignee FROM tasks ORDER BY importance DESC;"
```
