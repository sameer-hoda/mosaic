---
type: Concept
title: Groups Table
description: Whitelisted WhatsApp groups and DMs. Auto-populated via /api/groups/whitelist or _ensure_group_exists() in the pipeline.
tags: [database, groups]
---

# Groups Table

## Columns

| Column | Type | Description |
|---|---|---|
| `jid` | TEXT (PK) | WhatsApp JID — group ID ending in `@g.us` or DM ending in `@s.whatsapp.net` |
| `name` | TEXT | Human-readable group name (e.g., "Product Team Invoice Payouts") |
| `category` | TEXT | CHECK constrained — must be "Work" or "Personal". Defaults to "Personal" when auto-inserted. |
| `tldr` | TEXT | One-line summary from v1 cached classification |
| `whitelisted_at` | TIMESTAMP | When the group was whitelisted (auto-set) |
| `last_refreshed_at` | TIMESTAMP | When refresh was last run for this group. Used for incremental refresh. |

## Insertion Paths

1. **Whitelist flow**: `POST /api/groups/whitelist` — groups get correct categories + TLDRs from v1 cached classifications. Also handles deselection via `delete_groups_not_in()`.
2. **`_ensure_group_exists()`**: Auto-inserts when pipeline runs and group isn't in v2 table. Gets category "Personal" by default — a known limitation.

## Current State

As of June 20, 2026: 10 groups whitelisted — 8 Work, 2 Personal.

## Inspection

```bash
sqlite3 taskdog-backend/taskdog_v2.db "SELECT jid, name, category, tldr FROM groups;"
```
