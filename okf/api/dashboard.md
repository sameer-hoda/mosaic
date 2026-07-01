---
type: API Endpoint
title: Dashboard Endpoints
description: Read dashboard, task detail, task messages, and update tasks.
tags: [api, dashboard, tasks]
---

# Dashboard Endpoints

## GET /api/dashboard

Read-only dashboard — no Gemini calls. Tasks sorted by importance DESC, enriched with computed fields. Supports optional `group_jid` query param for filtering.

**Response**:
```json
{
    "ok": true,
    "tasks": [
        {
            "id": "10fcd89b-...",
            "title": "Define cohort for low propensity education model",
            "status": "active",
            "importance": 5,
            "group_jid": "120363409785935773@g.us",
            "group_name": "Bio auth <> edu",
            "assignee": "Ayesha",
            "context": "Detailed narrative of the task...",
            "latest_progress": null,
            "has_deep_dive": false,
            "days_since_refresh": 2,
            "message_count": 8,
            "created_at": "2026-06-15T10:30:00",
            "updated_at": "2026-06-18T14:22:00"
        }
    ],
    "stats": {
        "total": 13,
        "active": 13,
        "completed": 0,
        "archived": 0,
        "high_priority": 10,
        "followups_sent": 0,
        "importance_5": 5,
        "importance_4": 5,
        "importance_3": 2,
        "importance_2": 1,
        "importance_1": 0,
        "last_refreshed": "2026-06-18 14:22:00"
    }
}
```

## GET /api/tasks/{id}

Full task detail, including all deep-dive columns. Resolves assignee JIDs to human names via `resolve_task_assignees()`.

**Response**: `{"ok": true, "task": {...}}`

## GET /api/tasks/{id}/messages

Messages tagged for a specific task, ordered by message_time ASC.

**Response**:
```json
{
    "ok": true,
    "messages": [
        {
            "id": 1,
            "message_content": "We need to finalize the budget for June",
            "sender_name": "Rahul",
            "message_time": "2026-06-15T10:30:00",
            "relevance": 1.0
        }
    ]
}
```

## PATCH /api/tasks/{id}

Manual override for status and importance.

**Request**:
```json
{
    "status": "completed",
    "importance": 5
}
```

Valid statuses: `active`, `completed`, `archived`. Importance: 1-5. Either field is optional.

**Response**: `{"ok": true}`
