"""
Contact resolver: maps WhatsApp JID / LID / phone to human-readable names
by reading the bridge's whatsapp.db directly.

Uses the same DB path and approach as models/database.py's get_user_identity().
"""
import os
import sqlite3
from typing import Optional, Dict

# Path is relative to this file's location (taskdog-backend/utils/)
# The bridge DB lives at: ../../whatsapp-mcp/whatsapp-bridge/store/whatsapp.db
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WA_DB = os.path.join(_BASE_DIR, "..", "whatsapp-mcp", "whatsapp-bridge", "store", "whatsapp.db")
_WA_DB = os.path.normpath(_WA_DB)


def _get_wa_conn():
    """Open a read-only connection to the bridge's whatsapp.db."""
    if not os.path.exists(_WA_DB):
        return None
    conn = sqlite3.connect(_WA_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_user_identity() -> Dict[str, str]:
    """Return the connected WhatsApp user's jid, push_name, and lid."""
    conn = _get_wa_conn()
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
        print(f"get_user_identity error: {e}")
        return {"jid": "", "push_name": "", "lid": ""}
    finally:
        conn.close()


def resolve_contact(identifier: Optional[str]) -> str:
    """
    Resolve any WhatsApp identifier to a human-readable name.

    Handles:
        - LID like "13743945691279@lid" or plain "13743945691279"
        - JID like "919916509793@s.whatsapp.net" or "120363329500662632@g.us"
        - Phone like "919967151186"

    Falls back to returning the identifier as-is if unresolvable.
    """
    if not identifier or not isinstance(identifier, str):
        return "Unknown"

    identifier = identifier.strip()
    if not identifier:
        return "Unknown"

    # Skip non-identifiers (email, plain names)
    if "@" not in identifier and not identifier.isdigit() and not identifier.endswith("@lid"):
        return identifier

    # Already a name (no JID/LID pattern)
    if " " in identifier and "@" not in identifier:
        return identifier

    conn = _get_wa_conn()
    if not conn:
        return identifier

    try:
        cur = conn.cursor()
        jid = None

        # Case 1: LID format → "13743945691279@lid" or "219541632213229:5@lid"
        if "@lid" in identifier:
            lid_num = identifier.split("@")[0].split(":")[0]
            # Try lid_map
            cur.execute("SELECT pn FROM whatsmeow_lid_map WHERE lid = ?", (lid_num,))
            row = cur.fetchone()
            if row and row[0]:
                jid = f"{row[0]}@s.whatsapp.net"
            else:
                # Try as direct phone number
                jid = f"{lid_num}@s.whatsapp.net"

        # Case 2: Already a JID
        elif "@s.whatsapp.net" in identifier or "@g.us" in identifier:
            jid = identifier

        # Case 3: Plain digits — try lid_map first, then as phone number
        elif identifier.isdigit():
            cur.execute("SELECT pn FROM whatsmeow_lid_map WHERE lid = ?", (identifier,))
            row = cur.fetchone()
            if row and row[0]:
                jid = f"{row[0]}@s.whatsapp.net"
            else:
                jid = f"{identifier}@s.whatsapp.net"

        # Case 4: Unknown format, return as-is
        else:
            return identifier

        if not jid:
            return identifier

        # Look up name from contacts
        cur.execute("""
            SELECT COALESCE(push_name, full_name, first_name, business_name)
            FROM whatsmeow_contacts
            WHERE their_jid = ?
            LIMIT 1
        """, (jid,))
        row = cur.fetchone()

        if row and row[0]:
            return row[0]

        # Check if it's a group JID — try the chats DB
        if "@g.us" in jid:
            try:
                cur.execute("SELECT name, subject FROM chats WHERE jid = ? LIMIT 1", (jid,))
                crow = cur.fetchone()
                if crow and crow[0]:
                    return crow[0]
            except Exception:
                pass

        # Check if the JID matches our own — use push_name from device
        try:
            cur.execute("SELECT push_name FROM whatsmeow_device WHERE jid = ?", (jid,))
            drow = cur.fetchone()
            if drow and drow[0]:
                return drow[0]
        except Exception:
            pass

        # All lookups failed — if we have a phone, format it nicely
        phone = jid.split("@")[0] if jid and "@" in jid else ""
        if phone and phone.isdigit():
            if phone.startswith("91") and len(phone) == 12:
                return f"+91 {phone[2:7]} {phone[7:]}"
            return f"+{phone}"

        return identifier

    except Exception as e:
        print(f"resolve_contact error for '{identifier}': {e}")
        return identifier
    finally:
        conn.close()


def get_user_name() -> str:
    """Return the connected user's display name."""
    identity = get_user_identity()
    push_name = identity.get("push_name", "")
    if push_name:
        return push_name
    jid = identity.get("jid", "")
    if jid:
        resolved = resolve_contact(jid.replace(":5", ""))
        if resolved and "@" not in resolved:
            return resolved
    return "the account owner"


def resolve_task_assignees(task_dict: Dict) -> Dict:
    """
    Enrich a task dict with resolved assignee name.
    Adds 'assignee_name' field with the human-readable name.
    """
    assignee = task_dict.get("assignee") or ""
    if assignee:
        task_dict["assignee_name"] = resolve_contact(assignee)
    else:
        task_dict["assignee_name"] = ""
    return task_dict