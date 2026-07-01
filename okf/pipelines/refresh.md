---
type: Pipeline
title: Stage 2 — Refresh Tasks
description: Incrementally updates existing tasks with new messages since the last refresh timestamp. Processes status changes, progress notes, and new tasks.
tags: [pipeline, refresh, gemini]
---

# Refresh Tasks

## What It Does

For each group:
1. Reads `last_refreshed_at` from the `groups` table
2. Calculates days since last refresh (with 1-day buffer, min 1, max 30)
3. Fetches messages since that timestamp via the bridge
4. Gets current task list formatted for Gemini context (id, title, status, importance, assignee, context)
5. Sends new messages + existing task context to Gemini
6. Gemini returns updates:
   - `task_updates`: per-task `id`, `status_update` (still_active/completed/archived), `progress_note`, `importance`
   - `new_tasks`: new tasks with full schema (title, status, importance, assignee, context, people, suggested_responses)
7. Applies updates to the DB:
   - Updates status (completed/archived)
   - Updates importance if changed
   - Appends progress notes
   - Creates new tasks with UUIDs (skipped if duplicate detected via token-overlap dedup)
8. Updates `last_refreshed_at` to current time

## Key Properties

- **Incremental**: Only fetches new messages since last refresh
- **No duplicates**: Token-overlap dedup prevents creating tasks similar to existing ones
- **Per-group**: Each group has its own `last_refreshed_at` timestamp
- **Status accounting**: Tracks update/completed/archived/new counts in response

## SSE Events

Refresh stream emits per-task and per-new-task events:
- `meta`: total groups and known tasks count
- `task`: individual task status update (id, status_update, progress_note)
- `new_task`: new task found (title, importance, assignee)
- `done`: aggregate results

## Endpoints

- `POST /api/pipeline/refresh` — synchronous response
- `POST /api/pipeline/refresh/stream` — SSE streaming

## Current State

As of June 20, 2026: Refresh has **not been run yet**. First refresh should be done after discovery to verify no duplicates are created.
