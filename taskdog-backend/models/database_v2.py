"""
TaskDog v2 Database — schema + CRUD.

Fresh database file (taskdog_v2.db) that coexists with v1's taskdog.db.
No migration from v1; v2 routes use this module exclusively for v2 tables.

Tables:
    groups             — whitelisted WhatsApp groups for task monitoring
    tasks              — flat task model (no themes), keyed by group_jid
    task_messages      — messages tagged as relevant to a specific task
    followup_history   — log of sent follow-up / nudge messages
"""
import sqlite3
import os
import json
import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional


DATABASE_PATH_V2 = os.environ.get('DATABASE_PATH_V2', 'taskdog_v2.db')

# Global write lock — SQLite doesn't handle concurrent writes from multiple
# threads well (raises "database is locked"). This serializes all writes.
_write_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Connection & initialization
# ---------------------------------------------------------------------------

def get_db_connection_v2():
    """Open a connection to taskdog_v2.db with Row factory.
    Sets a 30s busy_timeout so concurrent access waits instead of erroring.
    """
    conn = sqlite3.connect(DATABASE_PATH_V2, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db_v2():
    """Create all v2 tables and indexes if they don't exist."""
    conn = sqlite3.connect(DATABASE_PATH_V2)
    conn.execute("PRAGMA journal_mode = WAL")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            jid               TEXT PRIMARY KEY,
            name              TEXT NOT NULL,
            category          TEXT NOT NULL CHECK (category IN ('Work', 'Personal')),
            tldr              TEXT,
            whitelisted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_refreshed_at TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id                 TEXT PRIMARY KEY,
            group_jid          TEXT NOT NULL REFERENCES groups(jid) ON DELETE CASCADE,
            title              TEXT NOT NULL,
            status             TEXT NOT NULL CHECK (status IN ('active', 'completed', 'archived')),
            importance         INTEGER NOT NULL DEFAULT 3 CHECK (importance BETWEEN 1 AND 5),
            assignee           TEXT,
            context            TEXT,
            wiki               TEXT,
            people             TEXT DEFAULT '[]',
            progress_log       TEXT DEFAULT '[]',
            blockers           TEXT DEFAULT '[]',
            decisions          TEXT DEFAULT '[]',
            last_deep_dived_at TIMESTAMP,
            created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_messages (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id          TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            message_content  TEXT,
            sender_name      TEXT,
            message_time     TEXT,
            relevance        REAL DEFAULT 0.0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS followup_history (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id        TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
            message_text   TEXT NOT NULL,
            recipient_jid  TEXT NOT NULL,
            sent_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_group_jid    ON tasks(group_jid)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status       ON tasks(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_importance   ON tasks(importance DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_messages_task ON task_messages(task_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_followup_task      ON followup_history(task_id)')

    try:
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_group_title ON tasks(group_jid, title)')
    except Exception as e:
        print(f"  (unique index on (group_jid, title) skipped — existing duplicates: {e})")

    conn.commit()
    conn.close()
    print(f"✓ TaskDog v2 Database initialized at {DATABASE_PATH_V2}")


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------

def insert_groups(jids: List[str], names: List[str], categories: List[str], tldrs: List[str]):
    """Bulk insert or replace groups. Lists must be parallel."""
    with _write_lock:
        conn = get_db_connection_v2()
        cursor = conn.cursor()
        for jid, name, category, tldr in zip(jids, names, categories, tldrs):
            if category not in ('Work', 'Personal'):
                category = 'Personal'
            cursor.execute('''
                INSERT INTO groups (jid, name, category, tldr)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(jid) DO UPDATE SET
                    name = excluded.name,
                    category = excluded.category,
                    tldr = excluded.tldr
            ''', (jid, name, category, tldr or ''))
        conn.commit()
        conn.close()


def get_groups() -> List[Dict]:
    """Return all whitelisted groups with task counts."""
    conn = get_db_connection_v2()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT g.*,
               (SELECT COUNT(*) FROM tasks t WHERE t.group_jid = g.jid) AS task_count,
               (SELECT COUNT(*) FROM tasks t WHERE t.group_jid = g.jid AND t.status = 'active') AS active_count
        FROM groups g
        ORDER BY g.name
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_whitelisted_jids_v2() -> set:
    """Return the set of all JIDs currently in the v2 groups table (whitelisted)."""
    conn = get_db_connection_v2()
    cursor = conn.cursor()
    cursor.execute('SELECT jid FROM groups')
    rows = cursor.fetchall()
    conn.close()
    return {r[0] for r in rows}


def delete_groups_not_in(jids: List[str]):
    """Remove groups whose JID is NOT in the given list.
    Used to sync the whitelist: groups the user deselected get removed
    (along with their tasks and task_messages via FK cascade).
    """
    with _write_lock:
        conn = get_db_connection_v2()
        if not jids:
            conn.execute('DELETE FROM groups')
        else:
            placeholders = ','.join('?' for _ in jids)
            conn.execute(f'DELETE FROM groups WHERE jid NOT IN ({placeholders})', jids)
        conn.commit()
        conn.close()


def get_group(jid: str) -> Optional[Dict]:
    """Return a single group by JID."""
    conn = get_db_connection_v2()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM groups WHERE jid = ?', (jid,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_group_refreshed_at(jid: str):
    """Set last_refreshed_at to now for a group."""
    with _write_lock:
        conn = get_db_connection_v2()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE groups SET last_refreshed_at = CURRENT_TIMESTAMP WHERE jid = ?
        ''', (jid,))
        conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# Tasks — Discovery (Stage 1)
# ---------------------------------------------------------------------------

def _normalize_title(title: str) -> str:
    """Normalize a task title for dedup comparison: lowercase, strip, collapse whitespace."""
    return " ".join(title.lower().split())


def _title_exists(group_jid: str, title: str, cursor) -> bool:
    """Check if a normalized title already exists for this group in the DB.
    Uses token-overlap scoring: >60% token overlap with any existing title = duplicate.
    """
    normalized = _normalize_title(title)
    cursor.execute('SELECT title FROM tasks WHERE group_jid = ?', (group_jid,))
    existing_titles = [r[0] for r in cursor.fetchall()]

    new_tokens = set(normalized.split())
    if not new_tokens:
        return False

    for existing in existing_titles:
        existing_normalized = _normalize_title(existing)
        existing_tokens = set(existing_normalized.split())
        if not existing_tokens:
            continue
        overlap = len(new_tokens & existing_tokens)
        min_len = min(len(new_tokens), len(existing_tokens))
        if min_len > 0 and overlap / min_len > 0.70:
            return True

    return False


def insert_tasks(task_list: List[Dict], group_jid: str):
    """Bulk insert tasks from Gemini discovery output.
    Each task dict should have: title, status, importance, assignee, context, people, suggested_responses.
    Generates UUIDs for each task.
    Returns list of inserted task dicts (with ids).
    """
    with _write_lock:
        conn = get_db_connection_v2()
        cursor = conn.cursor()
        inserted = []
        skipped = 0
        for t in task_list:
            title = t.get('title', '')
            if _title_exists(group_jid, title, cursor):
                skipped += 1
                continue

            task_id = str(uuid.uuid4())
            people = t.get('people', [])
            try:
                cursor.execute('''
                    INSERT INTO tasks (id, group_jid, title, status, importance, assignee, context, people)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_id,
                    group_jid,
                    title,
                    t.get('status', 'active'),
                    t.get('importance', 3),
                    t.get('assignee', ''),
                    t.get('context', ''),
                    json.dumps(people),
                ))
            except sqlite3.IntegrityError:
                skipped += 1
                continue

            result = dict(t)
            result['id'] = task_id
            result['group_jid'] = group_jid
            result['people'] = people
            inserted.append(result)
        conn.commit()
        conn.close()
        if skipped:
            print(f"  [dedup] insert_tasks: skipped {skipped} duplicate(s) for group {group_jid}")
    return inserted


def save_task(task_dict: Dict):
    """Single INSERT OR REPLACE for a task. Used by refresh for new tasks.
    Skips if a task with a similar title already exists in the same group."""
    with _write_lock:
        conn = get_db_connection_v2()
        cursor = conn.cursor()
        task_id = task_dict.get('id') or str(uuid.uuid4())
        group_jid = task_dict.get('group_jid', '')
        title = task_dict.get('title', '')

        if _title_exists(group_jid, title, cursor):
            conn.close()
            print(f"  [dedup] save_task: skipping duplicate '{title}' for group {group_jid}")
            return None

        try:
            cursor.execute('''
                INSERT INTO tasks (id, group_jid, title, status, importance, assignee, context, people)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    status = excluded.status,
                    importance = excluded.importance,
                    assignee = excluded.assignee,
                    context = excluded.context,
                    people = excluded.people,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                task_id,
                group_jid,
                title,
                task_dict.get('status', 'active'),
                task_dict.get('importance', 3),
                task_dict.get('assignee', ''),
                task_dict.get('context', ''),
                json.dumps(task_dict.get('people', [])),
            ))
        except sqlite3.IntegrityError:
            conn.close()
            return None

        conn.commit()
        conn.close()
    return task_id


def get_tasks_by_group(jid: str, status_filter: Optional[str] = None) -> List[Dict]:
    """Tasks for one group, optionally filtered by status."""
    conn = get_db_connection_v2()
    cursor = conn.cursor()
    if status_filter:
        cursor.execute('''
            SELECT * FROM tasks WHERE group_jid = ? AND status = ?
            ORDER BY importance DESC, created_at DESC
        ''', (jid, status_filter))
    else:
        cursor.execute('''
            SELECT * FROM tasks WHERE group_jid = ?
            ORDER BY importance DESC, created_at DESC
        ''', (jid,))
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_task_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Tasks — Refresh (Stage 2)
# ---------------------------------------------------------------------------

def get_tasks_for_refresh(group_jid: str) -> List[Dict]:
    """Return current tasks for a group as JSON-ready list for the refresh prompt."""
    conn = get_db_connection_v2()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, status, importance, assignee, context
        FROM tasks WHERE group_jid = ?
        ORDER BY created_at ASC
    ''', (group_jid,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_task_status(task_id: str, new_status: str):
    """Update a task's status (active / completed / archived)."""
    with _write_lock:
        conn = get_db_connection_v2()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (new_status, task_id))
        conn.commit()
        conn.close()


def update_task_importance(task_id: str, importance: int):
    """Update a task's importance score (1-5)."""
    with _write_lock:
        conn = get_db_connection_v2()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks SET importance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (importance, task_id))
        conn.commit()
        conn.close()


def update_task_progress(task_id: str, progress_note: str):
    """Append a progress note to the task's progress_log JSON array."""
    with _write_lock:
        conn = get_db_connection_v2()
        cursor = conn.cursor()
        cursor.execute('SELECT progress_log FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return
        try:
            log = json.loads(row[0] or '[]')
        except (json.JSONDecodeError, TypeError):
            log = []
        log.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'summary': progress_note,
        })
        cursor.execute('''
            UPDATE tasks SET progress_log = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (json.dumps(log), task_id))
        conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# Tasks — Deep-Dive (Stage 3)
# ---------------------------------------------------------------------------

def get_task(task_id: str) -> Optional[Dict]:
    """Full single task with all fields, JSON columns parsed. Includes group_name."""
    conn = get_db_connection_v2()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.*, g.name as group_name
        FROM tasks t
        LEFT JOIN groups g ON t.group_jid = g.jid
        WHERE t.id = ?
    ''', (task_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    task = _row_to_task_dict(row)
    task['group_name'] = row['group_name'] or ''
    return task


def update_task_deep_dive(task_id: str, wiki: str, people: List[Dict],
                          progress_log: List[Dict], blockers: List[Dict],
                          decisions: List[Dict], importance: int):
    """Save Stage 3 deep-dive output to the task."""
    with _write_lock:
        conn = get_db_connection_v2()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks SET
                wiki = ?,
                people = ?,
                progress_log = ?,
                blockers = ?,
                decisions = ?,
                importance = ?,
                last_deep_dived_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            wiki,
            json.dumps(people),
            json.dumps(progress_log),
            json.dumps(blockers),
            json.dumps(decisions),
            importance,
            task_id,
        ))
        conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# Tasks — Dashboard (Stage 4)
# ---------------------------------------------------------------------------

def get_all_tasks(group_jid: Optional[str] = None) -> List[Dict]:
    """All tasks sorted by importance DESC. Optionally filtered by group.
    Joins group name for the dashboard. Enriches with latest_progress, has_deep_dive, and message_count.
    """
    conn = get_db_connection_v2()
    cursor = conn.cursor()
    if group_jid:
        cursor.execute('''
            SELECT t.*, g.name as group_name,
                   (SELECT COUNT(*) FROM task_messages tm WHERE tm.task_id = t.id) AS message_count
            FROM tasks t
            JOIN groups g ON t.group_jid = g.jid
            WHERE t.group_jid = ?
            ORDER BY t.importance DESC, t.updated_at DESC
        ''', (group_jid,))
    else:
        cursor.execute('''
            SELECT t.*, g.name as group_name,
                   (SELECT COUNT(*) FROM task_messages tm WHERE tm.task_id = t.id) AS message_count
            FROM tasks t
            JOIN groups g ON t.group_jid = g.jid
            ORDER BY t.importance DESC, t.updated_at DESC
        ''')
    rows = cursor.fetchall()
    conn.close()
    tasks = []
    for r in rows:
        task = _row_to_task_dict(r)
        task['group_name'] = r['group_name']
        task['message_count'] = r['message_count'] or 0
        progress_log = task.get('progress_log') or []
        task['latest_progress'] = progress_log[-1]['summary'] if progress_log else None
        task['has_deep_dive'] = task.get('last_deep_dived_at') is not None
        tasks.append(task)
    return tasks


def get_dashboard_stats() -> Dict:
    """Aggregate stats for the dashboard, including importance breakdown and last refresh time."""
    conn = get_db_connection_v2()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'active'")
    active = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'archived'")
    archived = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE importance >= 4")
    high_priority = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM followup_history")
    followups = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE importance = 5")
    importance_5 = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE importance = 4")
    importance_4 = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE importance = 3")
    importance_3 = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE importance = 2")
    importance_2 = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE importance = 1")
    importance_1 = cursor.fetchone()[0]

    cursor.execute("SELECT MAX(last_refreshed_at) FROM groups WHERE last_refreshed_at IS NOT NULL")
    last_refreshed = cursor.fetchone()[0]

    conn.close()
    return {
        'active': active,
        'completed': completed,
        'archived': archived,
        'total': total,
        'high_priority': high_priority,
        'followups_sent': followups,
        'importance_5': importance_5,
        'importance_4': importance_4,
        'importance_3': importance_3,
        'importance_2': importance_2,
        'importance_1': importance_1,
        'last_refreshed': last_refreshed,
    }


# ---------------------------------------------------------------------------
# Task Messages
# ---------------------------------------------------------------------------

def insert_task_messages(task_id: str, messages: List[Dict]):
    """Bulk insert messages tagged for a task.
    Each message dict: {message_content, sender_name, message_time, relevance}
    """
    with _write_lock:
        conn = get_db_connection_v2()
        cursor = conn.cursor()
        for m in messages:
            cursor.execute('''
                INSERT INTO task_messages (task_id, message_content, sender_name, message_time, relevance)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                task_id,
                m.get('message_content', ''),
                m.get('sender_name', ''),
                m.get('message_time', ''),
                m.get('relevance', 0.0),
            ))
        conn.commit()
        conn.close()


def get_task_messages(task_id: str) -> List[Dict]:
    """All messages tagged for a task, ordered by time."""
    conn = get_db_connection_v2()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM task_messages WHERE task_id = ? ORDER BY message_time ASC
    ''', (task_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Followup History
# ---------------------------------------------------------------------------

def record_followup(task_id: str, text: str, recipient_jid: str):
    """Log a sent follow-up message."""
    with _write_lock:
        conn = get_db_connection_v2()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO followup_history (task_id, message_text, recipient_jid)
            VALUES (?, ?, ?)
        ''', (task_id, text, recipient_jid))
        conn.commit()
        conn.close()


def get_followup_history(limit: int = 50) -> List[Dict]:
    """Retrieve follow-up dispatch history, most recent first."""
    conn = get_db_connection_v2()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.*, t.title as task_title, g.name as group_name
        FROM followup_history f
        JOIN tasks t ON f.task_id = t.id
        JOIN groups g ON t.group_jid = g.jid
        ORDER BY f.sent_at DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def get_group_last_refreshed(jid: str) -> Optional[str]:
    """Return the last_refreshed_at timestamp for a group, or None."""
    conn = get_db_connection_v2()
    cursor = conn.cursor()
    cursor.execute('SELECT last_refreshed_at FROM groups WHERE jid = ?', (jid,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_task_group_jid(task_id: str) -> Optional[str]:
    """Return the group_jid for a task."""
    conn = get_db_connection_v2()
    cursor = conn.cursor()
    cursor.execute('SELECT group_jid FROM tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _row_to_task_dict(row) -> Optional[Dict]:
    """Convert a sqlite3.Row to a dict with JSON columns parsed."""
    if row is None:
        return None
    d = dict(row)
    for col in ('people', 'progress_log', 'blockers', 'decisions'):
        val = d.get(col)
        if isinstance(val, str):
            try:
                d[col] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                d[col] = []
        elif val is None:
            d[col] = []
    return d


def backfill_resolve_names():
    """
    One-shot backfill: resolve all unresolved JID/LID-based assignees and
    sender_names in the v2 DB to human-readable names.
    Safe to re-run (only updates unresolved entries).
    """
    import sys
    import os as _os
    _backfill_dir = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    if _backfill_dir not in sys.path:
        sys.path.insert(0, _backfill_dir)
    from utils.contact_resolver import resolve_contact

    with _write_lock:
        conn = get_db_connection_v2()
        c = conn.cursor()

        # 1. Fix tasks.assignee
        c.execute("SELECT id, assignee FROM tasks WHERE assignee IS NOT NULL AND assignee != ''")
        tasks = c.fetchall()
        updated = 0
        for task_id, assignee in tasks:
            resolved = resolve_contact(assignee)
            if resolved != assignee:
                c.execute("UPDATE tasks SET assignee = ? WHERE id = ?", (resolved, task_id))
                updated += 1

        # 2. Fix task_messages.sender_name
        c.execute("SELECT rowid, sender_name FROM task_messages WHERE sender_name IS NOT NULL AND sender_name != ''")
        msgs = c.fetchall()
        msg_updated = 0
        for rowid, sender_name in msgs:
            resolved = resolve_contact(sender_name)
            if resolved != sender_name:
                c.execute("UPDATE task_messages SET sender_name = ? WHERE rowid = ?", (resolved, rowid))
                msg_updated += 1

        # 3. Fix JSON columns: people, blockers, decisions from old deep-dives
        json_updated = 0
        for col in ("people", "blockers", "decisions"):
            c.execute(f"SELECT id, {col} FROM tasks WHERE {col} IS NOT NULL AND {col} != '' AND {col} != '[]' AND {col} != 'null'")
            for task_id, raw in c.fetchall():
                try:
                    data = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    continue
                if not data:
                    continue
                changed = False
                for item in data:
                    if isinstance(item, dict):
                        if col == "people" and item.get("name"):
                            resolved = resolve_contact(item["name"])
                            if resolved != item["name"]:
                                item["name"] = resolved
                                changed = True
                        elif col == "blockers" and item.get("raised_by"):
                            resolved = resolve_contact(item["raised_by"])
                            if resolved != item["raised_by"]:
                                item["raised_by"] = resolved
                                changed = True
                        elif col == "decisions" and item.get("made_by"):
                            resolved = resolve_contact(item["made_by"])
                            if resolved != item["made_by"]:
                                item["made_by"] = resolved
                                changed = True
                if changed:
                    c.execute(f"UPDATE tasks SET {col} = ? WHERE id = ?", (json.dumps(data), task_id))
                    json_updated += 1

        conn.commit()
        conn.close()

    print(f"[backfill] tasks.assignee: {updated} resolved, {len(tasks) - updated} already ok")
    print(f"[backfill] task_messages.sender_name: {msg_updated} resolved, {len(msgs) - msg_updated} already ok")
    print(f"[backfill] JSON columns (people/blockers/decisions): {json_updated} tasks updated")


# Auto-initialize on import if the DB file doesn't exist
if not os.path.exists(DATABASE_PATH_V2):
    init_db_v2()
