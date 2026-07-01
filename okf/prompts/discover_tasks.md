---
type: Prompt
title: Discover Tasks Prompt
description: Gemini prompt used during Stage 1 (discover) — extracts tasks from a group's last 30 days of WhatsApp messages.
tags: [prompt, gemini, discovery]
---

# Discover Tasks Prompt

## Input

- List of messages (sender, timestamp, content) from a WhatsApp group
- Group name
- User identity (push_name + jid)

## Prompt Structure

The prompt instructs Gemini to:
1. Analyze the conversation transcript
2. Identify ALL outstanding tasks, action items, commitments, open questions, or deliverables
3. For each task extract: title, status (active/completed), importance (1-5), assignee, context (narrative), people (with roles), suggested_responses (3 variants), relevant_message_indices
4. CRITICAL: suggested_responses must be addressed TO other members, not to the account owner
5. Return a JSON array of tasks with their supporting message indices

## Response Schema

```json
{
    "tasks": [
        {
            "title": "Finalize June budget plan",
            "status": "active",
            "importance": 5,
            "assignee": "Rahul",
            "context": "Priya asked Rahul during the June 5 meeting to finalize the budget...",
            "people": [
                {"name": "Rahul", "role": "assignee"},
                {"name": "Priya", "role": "requestor"}
            ],
            "suggested_responses": {
                "concise": "Rahul, any update on the budget?",
                "moderate": "Hey team, just checking in on the June budget plan...",
                "with_context": "Rahul, you mentioned on June 5 that you'd finalize the budget..."
            },
            "relevant_message_indices": [3, 7, 12]
        }
    ]
}
```

## Implementation

In `utils/gemini_v2.py`, function `discover_tasks()`:

- Uses `GEMINI_API_KEY` from `.env`
- Calls Gemini REST API directly (not SDK)
- Response format: JSON with `responseMimeType: application/json`
- Uses `response_schema=DISCOVERY_SCHEMA` for structured output
- Model: `gemini-3.1-flash-lite-preview`
- Temperature: 0.3
- Timeout: 120s
- Retries up to 3 times with exponential backoff on failure
