---
type: Architecture
title: Data Flow
description: How data flows through the pipeline stages — from WhatsApp messages to the dashboard.
tags: [data-flow, pipeline]
---

# Data Flow

## Onboarding Flow

```
WhatsApp Bridge ──► GET /api/bridge/status ──► Frontend Gate B (pairing)
                         │
                         ▼
            POST /api/chats/classify ──► Frontend Gate C (whitelist)
                         │
                         ▼
            POST /api/groups/whitelist ──► v2 groups table
```

## Nudge Generation Flow

```
Dashboard nudge button
         │
         ▼
POST /api/nudge/generate (with task_id)
         │
         ▼
Gemini generates 3 variants (gentle, passive-aggressive, aggressive)
         │
         ▼
POST /api/send (v1) ──► wa-bridge ──► WhatsApp

Persona: saved as persona.txt, used to style nudge messages.
Auto-generated from user's message history via POST /api/persona/generate.
```

## Discovery Flow

```
For each whitelisted group:
  1. Fetch last 30 days of messages from bridge (GET /api/messages)
  2. Send transcript + prompt to Gemini REST API
  3. Parse response into tasks (title, status, importance, assignee, context, people, suggested_responses)
  4. For each task:
     a. Insert into v2 tasks table (with dedup via token-overlap similarity)
     b. Tag relevant messages into task_messages table
  5. Stream SSE events back to frontend

Parallelism: ThreadPoolExecutor(max_workers=3)
Concurrency guard: threading.Lock wraps all DB writes
```

## Refresh Flow

```
For each whitelisted group:
  1. Read last_refreshed_at timestamp
  2. Fetch messages since that timestamp (with 1-day buffer)
  3. Send to Gemini with existing tasks in context
  4. Gemini returns updates (status changes, progress notes, new tasks)
  5. Apply updates to DB (mark completed/archived, add progress notes)

Refresh is incremental — no duplicate tasks are created.
```

## Deep-Dive Flow

```
For a single task:
  1. Fetch 365 days of messages for the task's group (full history)
  2. Send to Gemini with task context (title, status, importance, assignee, context)
  3. Gemini returns: wiki (Markdown), people (JSON), progress_log (JSON), blockers (JSON), decisions (JSON), importance
  4. Contact resolver normalizes JID/LID names in people/blockers/decisions
  5. All saved as TEXT columns in the tasks table
  6. Single Gemini call, 5-20 seconds
```

## Dashboard Flow

```
GET /api/dashboard
  1. Read all tasks from v2 DB
  2. Join with groups for group name
  3. Compute stats (total, by status, by importance, followups sent, last refreshed)
  4. Resolve assignee JIDs to human names via contact_resolver
  5. Enrich with message_count, has_deep_dive, days_since_refresh
  6. Sort by importance DESC
  7. No Gemini calls — pure DB read
```
