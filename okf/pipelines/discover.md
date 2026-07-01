---
type: Pipeline
title: Stage 1 — Discover Tasks
description: Scans 30 days of messages per whitelisted group and extracts all tasks via Gemini. Runs groups in parallel via ThreadPoolExecutor(max_workers=3).
tags: [pipeline, discovery, gemini]
---

# Discover Tasks

## What It Does

For each whitelisted group, the discover stage:
1. Fetches the last 30 days of messages via the Go bridge
2. Sends the transcript as context to Gemini with a structured prompt
3. Parses the response into tasks (title, status, importance, assignee, context, people, suggested_responses, relevant_message_indices)
4. For each task:
   a. Inserts into the `tasks` table (with dedup via token-overlap >70%)
   b. Tags relevant messages into `task_messages` (with relevance 1.0)
5. Streams SSE events back to the frontend (per-group progress)

## Parallelism

Groups are processed via `ThreadPoolExecutor(max_workers=3)`:
- **Gemini calls**: Parallel (up to 3 simultaneous)
- **DB writes**: Serialized by `_write_lock` context manager to prevent "database is locked" errors
- **WAL mode**: Allows concurrent reads during writes

## Error Handling

- If Gemini returns an error for a group, that group is skipped with an error message (3 retries before failure)
- `_ensure_group_exists()` auto-inserts the group into v2 `groups` table if missing
- SSE stream sends per-group `success`, `no_messages`, `gemini_failed`, or `save_failed` events

## Timing

10-30 seconds per group depending on message volume and Gemini response time.

## Endpoints

- `POST /api/pipeline/discover` — synchronous response with summary block
- `POST /api/pipeline/discover/stream` — SSE streaming (events: `meta`, `group`, `done`)

## Current State

As of June 20, 2026: Discovery has been run successfully. 10 groups processed, 13 tasks discovered, 72 messages tagged.
