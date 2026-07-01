---
type: Reference
title: Bugs Fixed During v2 Implementation
description: Three bugs encountered and fixed during the v2 build — FK constraint failures, database locking, and route shadowing.
tags: [bugs, fixes]
---

# Bugs Fixed

## 1. Route Conflict — FK Constraint Failures

**Symptom**: "FOREIGN KEY constraint failed" during task discovery when inserting tasks for groups that existed in v1 but not v2.

**Root Cause**: v1's `GET /api/groups` route in `routes/tasks.py` was still registered and shadowing v2's version in `routes/groups.py`. It read from the v1 `groups` table, so groups whitelisted via v2 flow appeared in v1 but not in v2's `groups` table, causing FK failures when inserting tasks.

**Fix**: Removed v1's `GET /api/groups` route from `routes/tasks.py`. v2's `routes/groups.py` now owns this endpoint and reads from the correct v2 `groups` table.

## 2. Database Locking — Write Contention

**Symptom**: "database is locked" errors during discovery with parallel `ThreadPoolExecutor(max_workers=3)`.

**Root Cause**: SQLite doesn't support concurrent writes. Three parallel Gemini calls succeeded, but three parallel DB write operations failed.

**Fix** (three-pronged):
- WAL journal mode: `PRAGMA journal_mode = WAL` — allows concurrent reads during writes
- 30s busy timeout: `PRAGMA busy_timeout = 30000` — waits up to 30s for the lock
- `threading.Lock` (`_write_lock`) wraps all write functions via `with _write_lock:` context manager

## 3. Missing Groups — FK Errors from Auto-Insert Gap

**Symptom**: FK constraint failures when pipeline ran for groups that weren't in the v2 `groups` table.

**Root Cause**: Groups whitelisted via v1 flow or existing in v1 DB weren't auto-migrated to v2. When discovery tried to insert tasks referencing those groups, FK constraints failed.

**Fix**: Added `_ensure_group_exists()` in `routes/pipeline.py` — auto-inserts a group into v2 `groups` table if it's missing, before discovery or refresh runs.
