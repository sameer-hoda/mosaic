"""
Database models and initialization for TaskDog backend.
Integrates task tracking state with WhatsApp bridge databases.
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pytz

DATABASE_PATH = os.environ.get('DATABASE_PATH', 'taskdog.db')

def init_db(force=False):
    """Initialize the local taskdog.db database with the required schema."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    if force:
        cursor.execute("DROP TABLE IF EXISTS nudge_history")
        cursor.execute("DROP TABLE IF EXISTS tasks")
        cursor.execute("DROP TABLE IF EXISTS themes")
        cursor.execute("DROP TABLE IF EXISTS whitelisted_groups")
        cursor.execute("DROP TABLE IF EXISTS chat_classifications")
        cursor.execute("DROP TABLE IF EXISTS users")

    # Create chat_classifications table (cache; survives across visits)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_classifications (
            jid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL CHECK (category IN ('Work', 'Personal')),
            tldr TEXT,
            classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create whitelisted_groups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS whitelisted_groups (
            jid TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL, -- Work, Personal, Others
            tldr TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create themes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS themes (
            id TEXT PRIMARY KEY,
            group_jid TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_jid) REFERENCES whitelisted_groups(jid) ON DELETE CASCADE
        )
    ''')
    
    # Create tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            theme_id TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('not started', 'pending', 'done')),
            context TEXT,
            assignee TEXT,
            response_concise TEXT NOT NULL,
            response_moderate TEXT NOT NULL,
            response_with_context TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE
        )
    ''')
    
    # Create nudge_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nudge_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT NOT NULL,
            sent_text TEXT NOT NULL,
            recipient_jid TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    ''')

    # Create users table (optional fallback)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash) 
        VALUES (?, ?, ?)
    ''', ('admin', 'admin@taskdog.com', 'hashed_password_placeholder'))
    
    conn.commit()
    conn.close()
    print(f"✓ TaskDog Database initialized at {DATABASE_PATH}")


def get_db_connection():
    """Get a database connection to taskdog.db."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_whatsapp_db_conn():
    """Open a read-only attached connection to messages.db and whatsapp.db."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    whatsapp_db_path = os.path.join(base_dir, 'whatsapp-mcp', 'whatsapp-bridge', 'store', 'whatsapp.db')
    messages_db_path = os.path.join(base_dir, 'whatsapp-mcp', 'whatsapp-bridge', 'store', 'messages.db')

    if not os.path.exists(messages_db_path):
        return None
    try:
        conn = sqlite3.connect(f"file:{messages_db_path}?mode=ro", uri=True)
        if os.path.exists(whatsapp_db_path):
            conn.execute(f"ATTACH DATABASE '{whatsapp_db_path}' AS whatsapp_db")
        return conn
    except Exception as e:
        print(f"Error connecting to WhatsApp databases: {e}")
        return None


def fetch_top_chats(limit: int = 30) -> List[Dict]:
    """Fetch top N active, non-archived chats, sorted by most recent message."""
    conn = get_whatsapp_db_conn()
    if not conn:
        print("⚠️ WhatsApp database connection not available.")
        return []
    try:
        cursor = conn.cursor()
        query = """
        SELECT 
            c.jid, 
            COALESCE(
                contacts.push_name, 
                contacts.full_name, 
                contacts.first_name, 
                contacts.business_name, 
                c.name, 
                c.jid
            ) as display_name,
            msg_stats.last_ts
        FROM chats c
        LEFT JOIN whatsapp_db.whatsmeow_chat_settings cs ON c.jid = cs.chat_jid
        LEFT JOIN whatsapp_db.whatsmeow_contacts contacts ON c.jid = contacts.their_jid
        INNER JOIN (
            SELECT chat_jid, MAX(timestamp) as last_ts
            FROM messages 
            GROUP BY chat_jid
            HAVING last_ts >= datetime('now', '-45 days')
        ) msg_stats ON c.jid = msg_stats.chat_jid
        WHERE (cs.archived IS NULL OR cs.archived = 0)
          AND (c.jid LIKE '%@g.us' OR c.jid LIKE '%@s.whatsapp.net')
          AND c.jid != 'status@broadcast'
          AND c.jid NOT LIKE '%@lid'
        ORDER BY msg_stats.last_ts DESC
        LIMIT ?
        """
        try:
            cursor.execute(query, (limit,))
        except sqlite3.OperationalError:
            fallback_query = """
            SELECT c.jid, COALESCE(c.name, c.jid) as display_name, msg_stats.last_ts
            FROM chats c
            INNER JOIN (
                SELECT chat_jid, MAX(timestamp) as last_ts
                FROM messages 
                GROUP BY chat_jid
                HAVING last_ts >= datetime('now', '-45 days')
            ) msg_stats ON c.jid = msg_stats.chat_jid
            WHERE c.jid != 'status@broadcast'
              AND c.jid NOT LIKE '%@lid'
              AND (c.jid LIKE '%@g.us' OR c.jid LIKE '%@s.whatsapp.net')
            ORDER BY msg_stats.last_ts DESC
            LIMIT ?
            """
            cursor.execute(fallback_query, (limit,))
            
        rows = cursor.fetchall()
        chats = []
        for r in rows:
            chats.append({
                "jid": r[0],
                "name": r[1] or r[0].split("@")[0],
                "last_message_time": r[2]
            })
        return chats
    except Exception as e:
        print(f"Error fetching top chats: {e}")
        return []
    finally:
        conn.close()


def fetch_chat_messages_since(jid: str, days: int = 30) -> List[Dict]:
    """Fetch all messages from the last N days for a specific JID, in chronological order."""
    conn = get_whatsapp_db_conn()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cutoff = datetime.now() - timedelta(days=days)
        # Format cutoff as string
        cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')

        query = """
        SELECT
            COALESCE(
                c_jid.push_name, c_jid.full_name, c_jid.first_name, c_jid.business_name,
                c_lid.push_name, c_lid.full_name, c_lid.first_name, c_lid.business_name,
                ms.sender_jid,
                m.sender
            ) AS sender_name,
            m.content,
            m.timestamp,
            COALESCE(m.is_from_me, 0) AS is_from_me
        FROM messages m
        LEFT JOIN whatsapp_db.whatsmeow_message_secrets ms
               ON m.id = ms.message_id AND m.chat_jid = ms.chat_jid
        LEFT JOIN whatsapp_db.whatsmeow_contacts c_jid ON ms.sender_jid = c_jid.their_jid
        LEFT JOIN whatsapp_db.whatsmeow_lid_map lm
               ON (lm.lid || '@lid') = ms.sender_jid
        LEFT JOIN whatsapp_db.whatsmeow_contacts c_lid
               ON (lm.pn || '@s.whatsapp.net') = c_lid.their_jid
        WHERE m.chat_jid = ? AND m.timestamp >= ? AND m.content IS NOT NULL AND TRIM(m.content) != ''
        ORDER BY m.timestamp ASC
        """
        try:
            cursor.execute(query, (jid, cutoff_str,))
        except sqlite3.OperationalError:
            # Fallback if whatsapp.db is not attached
            fallback_query = """
            SELECT sender, content, timestamp, COALESCE(is_from_me, 0) FROM messages
            WHERE chat_jid = ? AND timestamp >= ? AND content IS NOT NULL AND content != ''
            ORDER BY timestamp ASC
            """
            cursor.execute(fallback_query, (jid, cutoff_str,))

        rows = cursor.fetchall()
        messages = []
        for r in rows:
            messages.append({
                "sender": r[0] or "Unknown",
                "content": r[1],
                "timestamp": r[2],
                "is_from_me": bool(r[3]),
            })
        return messages
    except Exception as e:
        print(f"Error fetching messages since for JID {jid}: {e}")
        return []
    finally:
        conn.close()


def fetch_chat_messages(jid: str, limit: int = 25) -> List[Dict]:
    """Fetch the most recent N messages from a specific JID."""
    conn = get_whatsapp_db_conn()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        query = """
        SELECT 
            COALESCE(
                c_jid.push_name, c_jid.full_name, c_jid.first_name, c_jid.business_name,
                c_lid.push_name, c_lid.full_name, c_lid.first_name, c_lid.business_name,
                ms.sender_jid,
                m.sender
            ) AS sender_name,
            m.content,
            m.timestamp
        FROM messages m
        LEFT JOIN whatsapp_db.whatsmeow_message_secrets ms
               ON m.id = ms.message_id AND m.chat_jid = ms.chat_jid
        LEFT JOIN whatsapp_db.whatsmeow_contacts c_jid ON ms.sender_jid = c_jid.their_jid
        LEFT JOIN whatsapp_db.whatsmeow_lid_map lm
               ON (lm.lid || '@lid') = ms.sender_jid
        LEFT JOIN whatsapp_db.whatsmeow_contacts c_lid
               ON (lm.pn || '@s.whatsapp.net') = c_lid.their_jid
        WHERE m.chat_jid = ? AND m.content IS NOT NULL AND TRIM(m.content) != ''
        ORDER BY m.timestamp DESC
        LIMIT ?
        """
        try:
            cursor.execute(query, (jid, limit))
        except sqlite3.OperationalError:
            # Fallback if whatsapp.db is not attached
            fallback_query = """
            SELECT sender, content, timestamp FROM messages
            WHERE chat_jid = ? AND content IS NOT NULL AND content != ''
            ORDER BY timestamp DESC LIMIT ?
            """
            cursor.execute(fallback_query, (jid, limit))
            
        rows = cursor.fetchall()
        messages = []
        # Return in chronological order (oldest to newest)
        for r in reversed(rows):
            messages.append({
                "sender": r[0] or "Unknown",
                "content": r[1],
                "timestamp": r[2]
            })
        return messages
    except Exception as e:
        print(f"Error fetching messages for JID {jid}: {e}")
        return []
    finally:
        conn.close()


def save_whitelisted_groups(groups: List[Dict]):
    """Insert or update groups marked as whitelisted."""
    conn = get_db_connection()
    cursor = conn.cursor()
    for g in groups:
        # Default category to 'Personal' if the caller didn't provide one
        # (e.g. extract_tasks_route gets a bare jid/name list).
        category = g.get('category') or 'Personal'
        cursor.execute('''
            INSERT OR REPLACE INTO whitelisted_groups (jid, name, category, tldr)
            VALUES (?, ?, ?, ?)
        ''', (g['jid'], g['name'], category, g.get('tldr', '')))
    conn.commit()
    conn.close()


def get_cached_classifications_for_jids(jids: List[str]) -> Dict[str, Dict]:
    """Bulk-fetch cached classifications for a list of JIDs. Returns dict keyed by JID."""
    if not jids:
        return {}
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(jids))
    cursor.execute(
        f"SELECT jid, name, category, tldr, classified_at FROM chat_classifications WHERE jid IN ({placeholders})",
        jids,
    )
    rows = cursor.fetchall()
    conn.close()
    return {
        r[0]: {
            'name': r[1],
            'category': r[2],
            'tldr': r[3] or '',
            'classified_at': r[4],
        }
        for r in rows
    }


def upsert_classification(jid: str, name: str, category: str, tldr: str):
    """Insert or update a single classification cache row."""
    # Normalize legacy 'Others' values to 'Personal' so the simplified UI
    # never has to deal with a third bucket.
    if category not in ('Work', 'Personal'):
        category = 'Personal'
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_classifications (jid, name, category, tldr, classified_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(jid) DO UPDATE SET
            name = excluded.name,
            category = excluded.category,
            tldr = excluded.tldr,
            classified_at = CURRENT_TIMESTAMP
    ''', (jid, name, category, tldr or ''))
    conn.commit()
    conn.close()


def is_jid_whitelisted(jid: str) -> bool:
    """Fast lookup of whether a JID is in the whitelisted_groups table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM whitelisted_groups WHERE jid = ? LIMIT 1', (jid,))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def get_whitelisted_jids() -> set:
    """Return the set of all currently whitelisted JIDs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT jid FROM whitelisted_groups')
    rows = cursor.fetchall()
    conn.close()
    return {r[0] for r in rows}


def update_classification_category(jid: str, category: str) -> bool:
    """Update the cached category for a single chat (e.g. after a user
    drags the card to a different column). Returns True if a row was
    updated, False if the JID had no cached row. Legacy 'Others' values
    are normalised to 'Personal'."""
    if category not in ('Work', 'Personal'):
        category = 'Personal'
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE chat_classifications
        SET category = ?, classified_at = CURRENT_TIMESTAMP
        WHERE jid = ?
    ''', (category, jid))
    updated = cursor.rowcount > 0
    if not updated:
        # Defensive insert: if there's no cached row yet, create a minimal
        # one. The name will be updated the next time the chat is fetched
        # for classification.
        cursor.execute('''
            INSERT OR IGNORE INTO chat_classifications (jid, name, category, tldr)
            VALUES (?, ?, ?, '')
        ''', (jid, jid, category))
        updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def get_user_identity() -> Dict:
    """
    Look up the connected WhatsApp account owner.

    Returns a dict with at least `jid` and `push_name`. Falls back to empty
    strings if the WhatsApp bridge isn't paired yet.
    """
    conn = get_whatsapp_db_conn()
    if not conn:
        return {"jid": "", "push_name": "", "lid": ""}
    try:
        cur = conn.cursor()
        cur.execute("SELECT jid, push_name, lid FROM whatsmeow_device LIMIT 1")
        row = cur.fetchone()
        if not row:
            return {"jid": "", "push_name": "", "lid": ""}
        return {"jid": row[0] or "", "push_name": row[1] or "", "lid": row[2] or ""}
    except Exception as e:
        print(f"Error reading user identity: {e}")
        return {"jid": "", "push_name": "", "lid": ""}
    finally:
        conn.close()


def get_whitelisted_groups() -> List[Dict]:
    """Get all whitelisted groups."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM whitelisted_groups')
    rows = cursor.fetchall()
    groups = [dict(row) for row in rows]
    conn.close()
    return groups


def save_extracted_themes_and_tasks(group_jid: str, themes_data: List[Dict]):
    """Save themes and tasks extracted for a specific group."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # We start by deleting existing themes/tasks for this group to avoid duplication
        cursor.execute("SELECT id FROM themes WHERE group_jid = ?", (group_jid,))
        theme_ids = [r[0] for r in cursor.fetchall()]
        
        for t_id in theme_ids:
            cursor.execute("DELETE FROM tasks WHERE theme_id = ?", (t_id,))
        cursor.execute("DELETE FROM themes WHERE group_jid = ?", (group_jid,))
        
        # Insert new themes and tasks
        import uuid
        for t_data in themes_data:
            theme_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO themes (id, group_jid, name, description)
                VALUES (?, ?, ?, ?)
            ''', (theme_id, group_jid, t_data['name'], t_data.get('description', '')))
            
            for t_task in t_data.get('tasks', []):
                task_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO tasks (
                        id, theme_id, title, status, context, assignee,
                        response_concise, response_moderate, response_with_context
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_id,
                    theme_id,
                    t_task['title'],
                    t_task.get('status', 'not started').lower(),
                    t_task.get('context', ''),
                    t_task.get('assignee', ''),
                    t_task['suggested_responses']['concise'],
                    t_task['suggested_responses']['moderate'],
                    t_task['suggested_responses']['with_context']
                ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error saving themes/tasks for JID {group_jid}: {e}")
        raise e
    finally:
        conn.close()


def get_kanban_tasks(group_jid: Optional[str] = None) -> List[Dict]:
    """Retrieve tasks with theme and group details for the Kanban board."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        t.id, 
        t.title, 
        t.status, 
        t.context, 
        t.assignee, 
        t.response_concise, 
        t.response_moderate, 
        t.response_with_context,
        t.created_at,
        th.name as theme_name,
        g.name as group_name,
        g.jid as group_jid
    FROM tasks t
    JOIN themes th ON t.theme_id = th.id
    JOIN whitelisted_groups g ON th.group_jid = g.jid
    """
    
    if group_jid:
        query += " WHERE g.jid = ?"
        cursor.execute(query, (group_jid,))
    else:
        cursor.execute(query)
        
    rows = cursor.fetchall()
    tasks = []
    for r in rows:
        tasks.append({
            "id": r[0],
            "title": r[1],
            "status": r[2],
            "context": r[3],
            "assignee": r[4],
            "suggested_responses": {
                "concise": r[5],
                "moderate": r[6],
                "with_context": r[7]
            },
            "created_at": r[8],
            "theme_name": r[9],
            "group_name": r[10],
            "group_jid": r[11]
        })
    conn.close()
    return tasks


def update_task_status(task_id: str, status: str):
    """Update task status in database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE tasks 
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, task_id))
    conn.commit()
    conn.close()


def record_nudge(task_id: str, sent_text: str, recipient_jid: str):
    """Log a sent follow-up message into nudge_history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO nudge_history (task_id, sent_text, recipient_jid)
        VALUES (?, ?, ?)
    ''', (task_id, sent_text, recipient_jid))
    conn.commit()
    conn.close()


def get_nudge_history(limit: int = 50) -> List[Dict]:
    """Retrieve follow-up dispatch history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT n.*, t.title as task_title, g.name as group_name
        FROM nudge_history n
        JOIN tasks t ON n.task_id = t.id
        JOIN themes th ON t.theme_id = th.id
        JOIN whitelisted_groups g ON th.group_jid = g.jid
        ORDER BY n.sent_at DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    history = [dict(row) for row in rows]
    conn.close()
    return history


def get_tasks_stats() -> Dict[str, int]:
    """Get count stats of tasks in different states."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "not started"')
    not_started = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "pending"')
    pending = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE status = "done"')
    done = cursor.fetchone()[0]
    
    conn.close()
    return {
        'not_started': not_started,
        'pending': pending,
        'done': done,
        'total': not_started + pending + done
    }


# Automatically initialize the database on startup
if not os.path.exists(DATABASE_PATH):
    init_db()