---
type: Prompt
title: Refresh Tasks Prompt
description: Gemini prompt used during Stage 2 (refresh) — incrementally updates existing tasks with new messages since last refresh.
tags: [prompt, gemini, refresh]
---

# Refresh Tasks Prompt

## Input

- New messages since last refresh timestamp
- Existing tasks (id, title, status, importance, assignee, context) for the group — JSON formatted
- Group name
- User name

## Prompt Structure

The prompt instructs Gemini to:
1. Review the new messages
2. For EACH known task, determine status update: `still_active`, `completed`, or `archived`
3. For each task, provide a 1-line progress_note (or "No change" if nothing new)
4. Re-assess importance if changed; return current value if unchanged
5. Use EXACT `id` field from current tasks — do not create new IDs for existing tasks
6. Scan for NEW tasks: format as "new-001", "new-002", etc.
7. Rules: don't mark completed unless explicit evidence; archived if mentioned once without followup; silence doesn't mean completion

## Response Schema

```json
{
    "task_updates": [
        {
            "id": "existing-uuid",
            "status_update": "completed",
            "progress_note": "Budget approved by finance on June 15",
            "importance": 5
        }
    ],
    "new_tasks": [
        {
            "title": "Review Q3 budget proposal",
            "status": "active",
            "importance": 3,
            "assignee": "Priya",
            "context": "New task discovered...",
            "people": [],
            "suggested_responses": {
                "concise": "...",
                "moderate": "...",
                "with_context": "..."
            }
        }
    ]
}
```

## Key Property

Refresh is incremental — it only processes new messages, not the full history. This makes it faster than discovery and ensures no duplicate tasks are created (token-overlap dedup on the DB side catches any that slip through).
