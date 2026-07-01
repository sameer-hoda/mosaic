---
type: Pipeline
title: Stage 4 — Dashboard View
description: Pure DB read — no Gemini calls. Tasks sorted by importance DESC with aggregate stats and enriched fields.
tags: [pipeline, dashboard]
---

# Dashboard View

## What It Does

Reads all data from the v2 DB and presents it:

1. **Task list**: All tasks, joined with groups for group name, sorted by importance DESC and updated_at DESC
2. **Stats**: Total count, by status (active/completed/archived), by importance level (1-5), high priority (>=4), followups sent, last refreshed timestamp
3. **Enriched fields**: `message_count`, `has_deep_dive` (based on last_deep_dived_at), `latest_progress` (last entry in progress_log), `days_since_refresh`, `context`
4. **Assignee resolution**: JID/LID identifiers resolved to human-readable names via `resolve_contact()`

## Key Properties

- **No Gemini calls**: Pure SQL queries, instant response
- **Cache-friendly**: Read-only endpoint, can be called frequently
- **Sort order**: Importance DESC, updated_at DESC
- **Group filtering**: Optional `group_jid` query parameter

## Endpoint

`GET /api/dashboard?group_jid=<optional-filter>`

## Dashboard Core Fields

```json
{
    "ok": true,
    "tasks": [
        {
            "id": "...",
            "title": "...",
            "status": "active",
            "importance": 5,
            "group_jid": "...",
            "group_name": "...",
            "assignee": "Rahul",
            "context": "...",
            "latest_progress": null,
            "has_deep_dive": false,
            "days_since_refresh": 2,
            "message_count": 8,
            "created_at": "...",
            "updated_at": "..."
        }
    ],
    "stats": {
        "total": 13, "active": 13, "completed": 0, "archived": 0,
        "high_priority": 10, "followups_sent": 0,
        "importance_5": 5, "importance_4": 5, "importance_3": 2,
        "importance_2": 1, "importance_1": 0,
        "last_refreshed": "2026-06-18 14:22:00"
    }
}
```

## Current Data State

As of June 20, 2026:
- 10 groups
- 13 tasks (all active)
- 72 tagged messages
- 0 deep-dives
- 0 followup history entries

## Task Detail

Individual task drill-down is available at:
- `GET /api/tasks/{id}` — full detail with deep-dive columns (resolves assignee JIDs)
- `GET /api/tasks/{id}/messages` — tagged messages with relevance scores
- `PATCH /api/tasks/{id}` — manual status/importance override
