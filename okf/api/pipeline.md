---
type: API Endpoint
title: Pipeline Endpoints
description: The 4-stage pipeline — discover, refresh, deep-dive — with SSE streaming for stages 1 and 2.
tags: [api, pipeline, sse]
---

# Pipeline Endpoints

## POST /api/pipeline/discover

Stage 1: Discover tasks from last 30 days of messages.

**Request**:
```json
{
    "group_jids": ["120363123456@g.us"]
}
```

**Response**:
```json
{
    "ok": true,
    "results": [
        {
            "jid": "120363123456@g.us",
            "name": "Product Team",
            "status": "ok",
            "task_count": 3,
            "error": null
        }
    ],
    "summary": {
        "total_groups": 5,
        "groups_with_tasks": 3,
        "total_tasks_found": 7
    }
}
```

Individual group statuses: `ok`, `no_messages`, `gemini_failed`, `save_failed`.

## POST /api/pipeline/discover/stream

Same as discover but with SSE streaming for real-time progress.

**SSE Events**:
```
event: meta
data: {"total": 5}

event: group
data: {"jid":"...","name":"...","status":"ok","task_count":3}

event: group
data: {"jid":"...","name":"...","status":"no_messages","task_count":0,"error":"No messages in last 30 days"}

event: done
data: {"ok":true,"total_groups":5,"groups_with_tasks":3,"total_tasks_found":7}
```

## POST /api/pipeline/refresh

Stage 2: Incrementally update tasks with new messages since last refresh.

**Request**:
```json
{
    "group_jids": ["120363123456@g.us"]
}
```

**Response**:
```json
{
    "ok": true,
    "results": [
        {
            "jid": "120363123456@g.us",
            "name": "Product Team",
            "status": "ok",
            "tasks_updated": 2,
            "tasks_completed": 1,
            "tasks_archived": 0,
            "new_tasks_found": 1,
            "error": null
        }
    ]
}
```

## POST /api/pipeline/refresh/stream

Same as refresh with SSE streaming.

**SSE Events**:
```
event: meta
data: {"total_groups":5,"total_known_tasks":13}

event: task
data: {"task_id":"...","status_update":"completed","progress_note":"Budget approved by finance"}

event: new_task
data: {"title":"Review Q3 budget","importance":3,"assignee":"Rahul"}

event: done
data: {"ok":true,"updated":2,"completed":1,"archived":0,"new":1}
```

## POST /api/pipeline/deep-dive

Stage 3: Deep-dive analysis of a single task. Synchronous (5-20s). Fetches 365 days of full transcript.

**Request**:
```json
{
    "task_id": "10fcd89b-5ef7-48c3-bbb9-1f5f16cc4128"
}
```

**Response**:
```json
{
    "ok": true,
    "task": {
        "id": "10fcd89b-...",
        "title": "Define cohort for low propensity education model",
        "wiki": "# Task: Define cohort...\n\n## Overview\n...",
        "people": [{"name": "Ayesha", "role": "owner"}],
        "progress_log": [{"date": "2026-06-01", "summary": "Discussion started"}],
        "blockers": [{"description": "Awaiting data", "raised_by": "Ayesha", "date": "2026-06-05"}],
        "decisions": [{"description": "Use RFM model", "made_by": "Rahul", "date": "2026-06-10"}],
        ...
    }
}
```

Contact resolver normalizes JID/LID references in people names, blocker authors (`raised_by`), and decision authors (`made_by`) before saving.
