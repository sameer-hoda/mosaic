---
type: Pipeline
title: Stage 3 — Deep-Dive
description: Comprehensive analysis of a single task. Full 365-day transcript → Gemini → wiki (Markdown), people, progress_log, blockers, decisions.
tags: [pipeline, deep-dive, gemini, wiki]
---

# Deep-Dive

## What It Does

For a single task:
1. Fetches the full chat transcript (365 days = effectively all) for the task's group
2. Sends the full transcript + task context (title, status, importance, assignee, context, group_name) to Gemini with a structured prompt
3. Gemini returns:
   - **wiki** (Markdown) — A formatted knowledge page about the task (4-6 paragraphs: overview, chronology, status, key quotes)
   - **people** (JSON) — All mentioned people with their names, roles, and JIDs
   - **progress_log** (JSON) — Timeline of progress updates (date + summary)
   - **blockers** (JSON) — Identified blockers (description, raised_by, date)
   - **decisions** (JSON) — Key decisions made (description, made_by, date)
   - **importance** (int) — Re-assessed importance 1-5 based on full context
4. Contact resolver normalizes JID/LID references in people names, blocker authors, and decision authors
5. All saved as TEXT columns in the `tasks` table, `last_deep_dived_at` is updated

## Key Properties

- **Single-task**: One deep-dive per call, not batched
- **Full transcript**: No pre-filtering — the entire chat history (up to 365 days) is sent
- **Single Gemini call**: 5-20 seconds depending on transcript size
- **Model**: Uses `gemini-3.1-flash-lite-preview` (same as discover/refresh)
- **5-10K token response**: Structured JSON parsed from Gemini's response

## Endpoint

- `POST /api/pipeline/deep-dive` with `{"task_id": "<uuid>"}` — returns the full updated task object

## Output Schema (per Gemini response)

```json
{
    "wiki": "# Task: Finalize June budget\n\n## Overview\n...",
    "people": [
        {"name": "Rahul", "role": "owner", "jid": null}
    ],
    "progress_log": [
        {"date": "2026-06-01", "summary": "Budget discussion started"}
    ],
    "blockers": [
        {"description": "Awaiting approval from finance", "raised_by": "Priya", "date": "2026-06-10"}
    ],
    "decisions": [
        {"description": "Budget will be 50L for June", "made_by": "Rahul", "date": "2026-06-10"}
    ],
    "importance": 5
}
```

## Current State

As of June 20, 2026: **No deep-dives performed** (0 wikis in DB). Deep-dive is the primary remaining verification task.
