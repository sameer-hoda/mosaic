#!/usr/bin/env python3
"""
WhatsApp Brain Generator — reads the bridge's messages.db + whatsapp.db
and produces an OKF-style documentation tree about the user's WhatsApp
universe (contacts, groups, message patterns, relationships).

Usage:
    cd sandbox/whatsapp-brain
    python3 generate_brain.py

Output:
    ./brain/          — the generated knowledge tree (50+ markdown files)
"""

import sqlite3
import os
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# ── Paths ─────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(BASE, "..", ".."))
BRIDGE_STORE = os.path.join(PROJECT_ROOT, "whatsapp-mcp", "whatsapp-bridge", "store")
MESSAGES_DB = os.path.join(BRIDGE_STORE, "messages.db")
WHATSAPP_DB = os.path.join(BRIDGE_STORE, "whatsapp.db")
OUTPUT_DIR = os.path.join(BASE, "brain")

OWN_JID_PREFIX = "919967151186"


# ── DB helpers ────────────────────────────────────────────────────────

def _get_conn(dbfile):
    conn = sqlite3.connect(dbfile)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def _resolve_name(jid, contacts_map, lid_map, chat_name_map, device_name, own_jid_full):
    """Resolve a JID to name using pre-loaded maps (no DB queries)."""
    if not jid:
        return "Unknown"

    # Already a plain name
    if "@" not in jid and not jid.isdigit():
        return jid

    # Strip session suffix like :5
    clean = re.sub(r":\d+(@|$)", r"\1", jid)

    # Group → chat name
    if "@g.us" in clean:
        name = chat_name_map.get(clean)
        if name and name != clean.split("@")[0]:
            return name
        # Also check non-suffixed
        name = chat_name_map.get(jid)
        if name and name != jid.split("@")[0]:
            return name
        return clean.split("@")[0]

    # Contact
    if clean in contacts_map:
        c = contacts_map[clean]
        name = c.get("push_name") or c.get("full_name") or c.get("first_name") or c.get("business_name") or ""
        if name:
            return name
    # Also try without suffix
    if jid != clean and clean in contacts_map:
        c = contacts_map[clean]
        name = c.get("push_name") or c.get("full_name") or c.get("first_name") or c.get("business_name") or ""
        if name:
            return name

    # LID → phone
    phone = clean.split("@")[0]
    if phone in lid_map:
        phone = lid_map[phone]
    if "@lid" in clean:
        pn = lid_map.get(phone)
        if pn:
            phone = pn

    # Own JID
    if phone == OWN_JID_PREFIX:
        return device_name or "Me"

    # Format phone
    if phone.isdigit():
        if phone.startswith("91") and len(phone) == 12:
            return f"+91 {phone[2:7]} {phone[7:]}"
        return f"+{phone}"

    return clean.split("@")[0]


# ── Data Collection (bulk queries) ────────────────────────────────────

def collect_all():
    """Collect all data using bulk queries. Returns a big dict."""
    print("  Reading databases...")
    wa = _get_conn(WHATSAPP_DB)
    msg = _get_conn(MESSAGES_DB)

    # ├─ User identity ──
    cur = wa.cursor()
    cur.execute("SELECT jid, push_name, lid FROM whatsmeow_device LIMIT 1")
    device = cur.fetchone()
    user_jid_full = device[0] if device else ""
    user_name = device[1] if device else "Unknown"
    user_lid = device[2] if device else ""

    # ├─ Pre-load lookup maps ──
    print("  Loading contacts map...")
    cur = wa.cursor()
    cur.execute("SELECT their_jid, push_name, full_name, first_name, business_name FROM whatsmeow_contacts")
    contacts_map = {}
    for r in cur.fetchall():
        j = r[0]
        # Normalize: strip :5 suffix
        j_clean = re.sub(r":\d+@", "@", j)
        contacts_map[j] = {
            "push_name": r[1] or "",
            "full_name": r[2] or "",
            "first_name": r[3] or "",
            "business_name": r[4] or "",
        }
        if j_clean != j:
            contacts_map[j_clean] = contacts_map[j]

    print("  Loading lid map...")
    cur = wa.cursor()
    cur.execute("SELECT lid, pn FROM whatsmeow_lid_map")
    lid_map = {}
    for r in cur.fetchall():
        lid_map[r[0]] = r[1]

    print("  Loading chat settings...")
    cur = wa.cursor()
    cur.execute("SELECT chat_jid, archived, pinned FROM whatsmeow_chat_settings")
    chat_settings = {}
    for r in cur.fetchall():
        chat_settings[r[0]] = {"archived": bool(r[1]), "pinned": bool(r[2])}

    # ├─ Load all chats ──
    print("  Loading chat list...")
    cur = msg.cursor()
    cur.execute("SELECT jid, name, last_message_time FROM chats WHERE jid != 'status@broadcast'")
    chat_name_map = {}
    all_chats = []
    for r in cur.fetchall():
        jid = r[0]
        name = r[1] or jid.split("@")[0]
        chat_name_map[jid] = name
        domain = jid.split("@")[1] if "@" in jid else "unknown"
        if "@g.us" in jid:
            chat_type = "group"
        elif "newsletter" in jid:
            chat_type = "newsletter"
        elif "broadcast" in jid:
            chat_type = "broadcast"
        elif "@lid" in jid or "@s.whatsapp.net" in jid:
            chat_type = "dm"
        else:
            chat_type = domain
        s = chat_settings.get(jid, {"archived": False, "pinned": False})
        all_chats.append({
            "jid": jid,
            "name": name,
            "last_message_time": r[2],
            "type": chat_type,
            "archived": s["archived"],
            "pinned": s["pinned"],
            "domain": domain,
        })

    active_chats = [c for c in all_chats if not c["archived"]]
    archived_chats = [c for c in all_chats if c["archived"]]
    print(f"  Chats: {len(active_chats)} active / {len(archived_chats)} archived / {len(all_chats)} total")

    # ├─ Bulk message stats ──
    print("  Computing message stats...")
    cur = msg.cursor()
    cur.execute("""
        SELECT chat_jid,
               COUNT(*) as total,
               SUM(CASE WHEN is_from_me = 1 THEN 1 ELSE 0 END) as my_count,
               MIN(REPLACE(timestamp, '+05:30', '')) as first_ts,
               MAX(REPLACE(timestamp, '+05:30', '')) as last_ts
        FROM messages
        GROUP BY chat_jid
    """)
    msg_stats = {}
    for r in cur.fetchall():
        msg_stats[r["chat_jid"]] = {
            "total": r["total"],
            "my_count": r["my_count"] or 0,
            "first_ts": (r["first_ts"] or "")[:10],
            "last_ts": (r["last_ts"] or "")[:10],
        }

    # ├─ Bulk last message content ──
    cur = msg.cursor()
    cur.execute("""
        SELECT chat_jid, content, timestamp
        FROM messages
        WHERE (chat_jid, timestamp) IN (
            SELECT chat_jid, MAX(timestamp)
            FROM messages
            WHERE content IS NOT NULL AND content != ''
            GROUP BY chat_jid
        )
    """)
    last_msg = {}
    for r in cur.fetchall():
        last_msg[r["chat_jid"]] = r["content"][:120] + ("…" if len(r["content"] or "") > 120 else "")

    # ├─ Bulk top senders per chat ──
    print("  Computing top senders...")
    cur = msg.cursor()
    cur.execute("""
        SELECT chat_jid, sender, COUNT(*) as cnt
        FROM messages
        GROUP BY chat_jid, sender
        ORDER BY chat_jid, cnt DESC
    """)
    senders_raw = defaultdict(list)
    for r in cur.fetchall():
        if len(senders_raw[r["chat_jid"]]) < 15:
            senders_raw[r["chat_jid"]].append({"jid": r["sender"], "count": r["cnt"]})

    # ├─ Global stats ──
    cur = msg.cursor()
    cur.execute("SELECT COUNT(*) FROM messages")
    total_msgs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM messages WHERE is_from_me = 1")
    my_msgs = cur.fetchone()[0]
    cur.execute("SELECT MIN(REPLACE(timestamp, '+05:30', '')), MAX(REPLACE(timestamp, '+05:30', '')) FROM messages")
    dr = cur.fetchone()
    first_msg_date = dr[0][:10] if dr and dr[0] else ""
    last_msg_date = dr[1][:10] if dr and dr[1] else ""

    wa.close()
    msg.close()

    # ├─ Enrich active chats ──
    print("  Enriching active chats...")

    # Figure out own device's base JID for name resolution
    own_base = user_jid_full.split("@")[0]

    for c in active_chats:
        jid = c["jid"]
        stats = msg_stats.get(jid, {"total": 0, "my_count": 0, "first_ts": "", "last_ts": ""})
        c["message_count"] = stats["total"]
        c["my_message_count"] = stats["my_count"]
        c["first_message_date"] = stats["first_ts"]
        c["last_message_date"] = stats["last_ts"]
        c["last_message_preview"] = last_msg.get(jid, "")

        senders = senders_raw.get(jid, [])
        for s in senders:
            s["name"] = _resolve_name(s["jid"], contacts_map, lid_map, chat_name_map, user_name, user_jid_full)
        c["top_senders"] = senders

        c["resolved_name"] = _resolve_name(jid, contacts_map, lid_map, chat_name_map, user_name, user_jid_full)

    active_chats.sort(key=lambda c: c["message_count"], reverse=True)

    return {
        "user_name": user_name,
        "user_jid": user_jid_full,
        "user_lid": user_lid,
        "total_messages": total_msgs,
        "my_messages": my_msgs,
        "first_message_date": first_msg_date,
        "last_message_date": last_msg_date,
        "total_chats": len(all_chats),
        "active_chats": len(active_chats),
        "archived_chats": len(archived_chats),
        "active_chats_data": active_chats,
        "archived_chats_data": archived_chats,
        "contacts_count": len(contacts_map),
        "chat_settings_count": len(chat_settings),
    }


# ── Output Writer ──────────────────────────────────────────────────────

def w(path, content):
    full = os.path.join(OUTPUT_DIR, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  ✦ {path}")

def fmt(n):
    if n >= 1000:
        return f"{n:,}"
    return str(n)


# ── Generators ─────────────────────────────────────────────────────────

def gen_index(d):
    active = d["active_chats_data"]
    groups = [c for c in active if c["type"] == "group"]
    dms = [c for c in active if c["type"] == "dm"]
    newsletters = [c for c in active if c["type"] == "newsletter"]

    return f"""---
title: WhatsApp Brain — {d["user_name"]}
description: Auto-generated knowledge base of your WhatsApp universe.
generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
messages: {fmt(d["total_messages"])}
chats: {d["active_chats"]} active / {d["total_chats"]} total
---

# 🧠 WhatsApp Brain — {d["user_name"]}

Auto-generated from the Go bridge's message store.

## At a Glance

| Metric | Value |
|---|---|
| Total messages | {fmt(d["total_messages"])} |
| Sent by you | {fmt(d["my_messages"])} ({round(d["my_messages"]/max(d["total_messages"],1)*100)}%) |
| Active chats | {d["active_chats"]} |
| Archived chats | {d["archived_chats"]} |
| Known contacts | {d["contacts_count"]} |
| Date range | {d["first_message_date"]} → {d["last_message_date"]} |

## Active Chats

| Type | Count |
|---|---|
| Groups | {len(groups)} |
| DMs | {len(dms)} |
| Newsletters | {len(newsletters)} |

## Sections

- [People & DMs](people/index.md)
- [Groups](groups/index.md)
- [Stats & Insights](stats/index.md)
- [Unresolved JIDs](references/unresolved.md)
- [Architecture](architecture/index.md)
"""


def gen_people(d):
    active = d["active_chats_data"]
    dms = [c for c in active if c["type"] == "dm"]
    dms.sort(key=lambda c: c["message_count"], reverse=True)

    lines = [f"""---
title: People & Direct Messages
description: All DM conversations, ranked by activity.
---

# People & Direct Messages

**{len(dms)}** DM conversations.

| # | Name | Messages | You | Last Active | Last Snippet |
|---|---|---|---|---|---|
"""]
    for i, c in enumerate(dms, 1):
        my_pct = round(c["my_message_count"] / max(c["message_count"], 1) * 100)
        lines.append(f"| {i} | {c['resolved_name']} | {fmt(c['message_count'])} | {my_pct}% | {c['last_message_date']} | {c['last_message_preview'][:50]} |")

    lines.append(f"\n## Individual Profiles\n")
    for c in dms[:30]:
        my_pct = round(c["my_message_count"] / max(c["message_count"], 1) * 100)
        top = "\n".join(f"    {j}. {s['name']} — {fmt(s['count'])}" for j, s in enumerate(c.get('top_senders', [])[:5], 1))
        lines.append(f"""
### {c['resolved_name']}

| Detail | Value |
|---|---|
| JID | `{c['jid']}` |
| Messages | {fmt(c['message_count'])} (you: {my_pct}%) |
| Active | {c['first_message_date']} → {c['last_message_date']} |
| Last | {c['last_message_preview'][:60]} |

""")

    return "\n".join(lines)


def gen_groups(d):
    active = d["active_chats_data"]
    groups = [c for c in active if c["type"] == "group"]
    newsletters = [c for c in active if c["type"] == "newsletter"]
    groups.sort(key=lambda c: c["message_count"], reverse=True)

    lines = [f"""---
title: Groups
description: All active group chats, ranked by message volume.
---

# Groups

**{len(groups)}** active groups.

| # | Group | Messages | You | Last Active | Last Snippet |
|---|---|---|---|---|---|
"""]
    for i, c in enumerate(groups, 1):
        my_pct = round(c["my_message_count"] / max(c["message_count"], 1) * 100)
        safe = c["resolved_name"].replace("/", "_").replace(" ", "_")
        lines.append(f"| {i} | [{c['resolved_name']}](profiles/{safe}.md) | {fmt(c['message_count'])} | {my_pct}% | {c['last_message_date']} | {c['last_message_preview'][:50]} |")

    if newsletters:
        lines.append(f"\n## Newsletters\n")
        for c in newsletters:
            lines.append(f"- {c['resolved_name']} ({fmt(c['message_count'])} messages)")

    # Individual profiles for top 30 groups
    lines.append(f"\n## Group Profiles\n")
    for c in groups[:30]:
        my_pct = round(c["my_message_count"] / max(c["message_count"], 1) * 100)
        safe = c["resolved_name"].replace("/", "_").replace(" ", "_")
        top = "\n".join(f"  {j}. {s['name']} — {fmt(s['count'])} msgs" for j, s in enumerate(c.get('top_senders', [])[:15], 1))

        lines.append(f"""
### {c['resolved_name']}

| Detail | Value |
|---|---|
| JID | `{c['jid']}` |
| Messages | {fmt(c['message_count'])} (you: {my_pct}%) |
| Active | {c['first_message_date']} → {c['last_message_date']} |
| Last | {c['last_message_preview'][:80]} |

**Top participants:**
{top}
""")

    return "\n".join(lines)


def gen_group_profile(c):
    my_pct = round(c["my_message_count"] / max(c["message_count"], 1) * 100)
    top = "\n".join(f"  {i}. {s['name']} — {fmt(s['count'])} msgs" for i, s in enumerate(c.get("top_senders", [])[:15], 1))

    return f"""---
title: {c["resolved_name"]}
jid: "{c["jid"]}"
messages: {c["message_count"]}
---

# {c["resolved_name"]}

| Detail | Value |
|---|---|
| JID | `{c['jid']}` |
| Total messages | {fmt(c['message_count'])} |
| You sent | {fmt(c['my_message_count'])} ({my_pct}%) |
| First message | {c['first_message_date']} |
| Last message | {c['last_message_date']} |

## Top Participants

{top}

## Latest

> {c['last_message_preview'][:200]}
"""


def gen_stats(d):
    active = d["active_chats_data"]
    groups = [c for c in active if c["type"] == "group"]
    dms = [c for c in active if c["type"] == "dm"]
    sorted_all = sorted(active, key=lambda c: c["message_count"], reverse=True)

    top10 = "\n".join(
        f"| {i} | {c['resolved_name']} | {'📢' if c['type']=='group' else '💬'} | {fmt(c['message_count'])} | {c['last_message_date']} |"
        for i, c in enumerate(sorted_all[:10], 1)
    )
    top10g = "\n".join(
        f"| {i} | {c['resolved_name']} | {fmt(c['message_count'])} | {fmt(c['my_message_count'])} |"
        for i, c in enumerate(sorted(groups, key=lambda x: x['message_count'], reverse=True)[:10], 1)
    )
    top10d = "\n".join(
        f"| {i} | {c['resolved_name']} | {fmt(c['message_count'])} | {fmt(c['my_message_count'])} |"
        for i, c in enumerate(sorted(dms, key=lambda x: x['message_count'], reverse=True)[:10], 1)
    )
    own_pct = round(d["my_messages"] / max(d["total_messages"], 1) * 100)

    return f"""---
title: Stats & Insights
description: Activity overview, top chats, and relationships.
---

# Stats & Insights

## Overview

| Metric | Value |
|---|---|
| Total messages | {fmt(d["total_messages"])} |
| You sent | {fmt(d["my_messages"])} ({own_pct}%) |
| Active groups | {len(groups)} |
| Active DMs | {len(dms)} |
| Known contacts | {d["contacts_count"]} |
| Date range | {d["first_message_date"]} → {d["last_message_date"]} |

## Top 10 Chats

| # | Name | Type | Messages | Last Active |
|---|---|---|---|---|
{top10}

## Top 10 Groups

| # | Name | Messages | You |
|---|---|---|---|
{top10g}

## Top 10 DMs

| # | Name | Messages | You |
|---|---|---|---|
{top10d}
"""


def gen_unresolved(d):
    active = d["active_chats_data"]
    unresolved = [c for c in active if
                  c["resolved_name"] == c["jid"].split("@")[0] or
                  (c["resolved_name"].startswith("+") and len(c["resolved_name"]) > 8)]

    if not unresolved:
        return "All JIDs resolved successfully.\n"

    lines = [f"""---
title: Unresolved JIDs
description: Chats that could not be mapped to human names ({len(unresolved)}).
---

# Unresolved JIDs

**{len(unresolved)}** chats not resolved to human names.

| JID | Label | Msgs | Type |
|---|---|---|---|
"""]
    for c in unresolved:
        lines.append(f"| `{c['jid']}` | {c['resolved_name']} | {fmt(c['message_count'])} | {c['type']} |")

    lines.append("\n## Fix\n- Add contact to phonebook, restart bridge\n- Check `whatsmeow_lid_map` for LID → phone mapping\n")
    return "\n".join(lines)


def gen_data_sources():
    return f"""---
title: Data Sources
description: Database schemas and resolution logic.
---

# Data Sources

## `messages.db`

| Table | Rows | Key Columns |
|---|---|---|
| `chats` | ~2,400 | `jid`, `name`, `last_message_time` |
| `messages` | ~64,000 | `chat_jid`, `sender`, `content`, `timestamp`, `is_from_me` |

## `whatsapp.db`

| Table | Rows | Key Columns |
|---|---|---|
| `whatsmeow_device` | 1 | `jid`, `push_name`, `lid` |
| `whatsmeow_contacts` | ~3,200 | `their_jid`, `push_name`, `full_name` |
| `whatsmeow_chat_settings` | ~540 | `chat_jid`, `archived`, `pinned` |
| `whatsmeow_lid_map` | varies | `lid`, `pn` (phone) |

## Resolution Priority

1. `whatsmeow_contacts.push_name` → `full_name` → `first_name` → `business_name`
2. Group JIDs: `chats.name` from messages.db
3. LIDs: `whatsmeow_lid_map` → phone → contacts lookup
4. Own JID: `whatsmeow_device.push_name`
5. Phone: formatted as `+91 XXXXX XXXXX`
"""


# ── Main ────────────────────────────────────────────────────────────────

def main():
    print("🧠 WhatsApp Brain Generator")
    print("═" * 40)
    data = collect_all()

    print(f"\n  User: {data['user_name']}")
    print(f"  Messages: {fmt(data['total_messages'])} ({fmt(data['my_messages'])} yours)")
    print(f"  Active: {data['active_chats']} / Archived: {data['archived_chats']}")

    print("\n📝 Generating...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "groups", "profiles"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "people"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "stats"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "architecture"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "references"), exist_ok=True)

    w("index.md", gen_index(data))
    w("log.md", f"""# Log

## {datetime.now().strftime("%Y-%m-%d")}
- Initial generation from bridge message store
- {fmt(data["total_messages"])} messages across {data["active_chats"]} active chats
- {data["user_name"]} — {data["user_jid"]}
""")

    w("architecture/index.md", "# Architecture\n\n- [Data Sources](data_sources.md)\n")
    w("architecture/data_sources.md", gen_data_sources())
    w("people/index.md", gen_people(data))
    w("groups/index.md", gen_groups(data))

    active = data["active_chats_data"]
    groups = [c for c in active if c["type"] == "group"]
    groups.sort(key=lambda c: c["message_count"], reverse=True)
    for c in groups[:30]:
        safe = c["resolved_name"].replace("/", "_").replace(" ", "_")
        w(f"groups/profiles/{safe}.md", gen_group_profile(c))

    w("stats/index.md", gen_stats(data))
    w("references/index.md", "# References\n\n- [Unresolved JIDs](unresolved.md)\n- [Data Sources](data_sources.md)\n")
    w("references/unresolved.md", gen_unresolved(data))
    w("references/data_sources.md", gen_data_sources())

    print(f"\n✅ Done! Generated to {OUTPUT_DIR}/")
    print(f"   {len(groups[:30])} group profiles")
    print(f"   Open {OUTPUT_DIR}/index.md to explore")


if __name__ == "__main__":
    main()
