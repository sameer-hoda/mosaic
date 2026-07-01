---
type: Concept
title: Task Messages Table
description: Messages tagged to specific tasks during discovery — contains the evidence for why a task was extracted.
tags: [database, tasks, messages]
---

# Task Messages Table

## Columns

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER (PK) | Auto-increment |
| `task_id` | TEXT (FK → tasks.id ON DELETE CASCADE) | Owning task |
| `message_content` | TEXT | The text content of the message |
| `sender_name` | TEXT | Name of the person who sent it (resolved from JID/LID) |
| `message_time` | TEXT | When the message was sent (ISO timestamp or WhatsApp format) |
| `relevance` | REAL | Relevance score 0.0-1.0 (default 1.0 for discovered tasks) |

## Purpose

When Gemini discovers a task, it also identifies which messages are relevant to that task via `relevant_message_indices`. These are stored in `task_messages` so the user can see the evidence trail — the conversations that led to the task being extracted.

## Difference from v1

v2's `task_messages` uses `message_time` and `relevance` instead of `message_id` and `timestamp`. There is no `message_id` column — messages are referenced by content only.

## Current State

As of June 20, 2026: 72 tagged messages across 13 tasks.

## Inspection

```bash
sqlite3 taskdog-backend/taskdog_v2.db "SELECT task_id, message_content, sender_name FROM task_messages LIMIT 10;"
```
