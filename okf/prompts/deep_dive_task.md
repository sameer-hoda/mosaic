---
type: Prompt
title: Deep-Dive Task Prompt
description: Gemini prompt used during Stage 3 (deep-dive) — generates a comprehensive knowledge page for a single task from the full chat transcript.
tags: [prompt, gemini, deep-dive, wiki]
---

# Deep-Dive Task Prompt

## Input

- Full chat transcript (365 days) for the task's group
- Task title, status, importance, assignee, context
- Group name
- User name

## Prompt Structure

The prompt instructs Gemini to:
1. Read the entire transcript, focusing on conversations relevant to this task
2. Produce a comprehensive knowledge page with:
   - **wiki** (Markdown): 4-6 paragraphs covering what the task is, chronology, current status, key quotes
   - **people**: Everyone involved with name, role (assignee/requestor/reviewer/stakeholder), and JID if identifiable
   - **progress_log**: Day-by-day log of developments (date + summary), sorted chronologically
   - **blockers**: Blockers with description, raised_by, date
   - **decisions**: Key decisions with description, made_by, date
   - **importance**: Re-assessed 1-5 score based on full context
3. Only extract information PRESENT in the transcript — no fabrication
4. Markdown headings and bullet points for readability

## Response Schema

```json
{
    "wiki": "# Task: Finalize June budget\n\n## Overview\nThe team needs to finalize the communications budget for June...\n\n## Chronology\n- **June 1**: Discussion started in Comms way of working group\n- **June 5**: Draft budget shared by Rahul\n- **June 10**: Priya requested revisions\n\n## Current Status\nAwaiting finance approval before finalizing...\n\n## Key Quotes\n> \"We need to get this done by June 15\" — Priya, June 10",
    "people": [
        {"name": "Rahul", "role": "assignee", "jid": null},
        {"name": "Priya", "role": "stakeholder", "jid": null}
    ],
    "progress_log": [
        {"date": "2026-06-01", "summary": "Budget discussion initiated"},
        {"date": "2026-06-05", "summary": "Draft budget shared by Rahul"},
        {"date": "2026-06-10", "summary": "Revisions requested by Priya"}
    ],
    "blockers": [
        {"description": "Finance approval pending", "raised_by": "Rahul", "date": "2026-06-10"}
    ],
    "decisions": [
        {"description": "Budget cap set at ₹50L for June", "made_by": "Priya", "date": "2026-06-05"}
    ],
    "importance": 5
}
```

## Implementation

- Single Gemini call with the full transcript
- Model: `gemini-3.1-flash-lite-preview`
- Temperature: 0.4
- Timeout: 120s
- 5-20 seconds response time depending on transcript size
- Wiki is Markdown text; people/progress_log/blockers/decisions are JSON
- All 6 fields saved as TEXT columns in the `tasks` table
- Response passes through contact_resolver to normalize JID/LID names
