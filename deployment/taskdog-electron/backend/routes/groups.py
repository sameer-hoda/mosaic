"""
TaskDog v2 — Group whitelisting routes.

POST /api/groups/whitelist  — save selected groups for task monitoring
GET  /api/groups            — list all whitelisted groups with task counts
"""
from flask import Blueprint, request, jsonify

from models.database_v2 import (
    init_db_v2,
    insert_groups,
    delete_groups_not_in,
    get_groups,
)
from models.database import (
    fetch_top_chats,
    get_cached_classifications_for_jids,
)

bp = Blueprint("groups_v2", __name__, url_prefix="/api")


@bp.route("/groups/whitelist", methods=["POST"])
def whitelist():
    """Save the user's selected groups for task monitoring.

    Request: { "jids": ["jid1@g.us", "jid2@g.us"] }

    For each JID:
      - Resolves the display name from the WhatsApp messages.db
      - Looks up cached classification (category + tldr) from v1's
        chat_classifications table
      - Inserts into v2 groups table
    """
    data = request.get_json(silent=True) or {}
    jids = data.get("jids") or []
    if not jids:
        return jsonify({"ok": False, "error": "No jids provided"}), 400

    # Resolve display names from WhatsApp DB
    top_chats = fetch_top_chats(limit=500)
    chat_name_map = {c["jid"]: c["name"] for c in top_chats}

    # Pull cached classifications (category + tldr) from v1 DB
    cached = get_cached_classifications_for_jids(jids)

    names = []
    categories = []
    tldrs = []
    for jid in jids:
        name = chat_name_map.get(jid, jid.split("@")[0])
        names.append(name)

        cls = cached.get(jid, {})
        category = cls.get("category", "Personal")
        if category not in ("Work", "Personal"):
            category = "Personal"
        categories.append(category)

        tldrs.append(cls.get("tldr", ""))

    insert_groups(jids, names, categories, tldrs)

    # Remove groups that the user deselected (not in jids)
    delete_groups_not_in(jids)

    return jsonify({"ok": True, "count": len(jids)})


@bp.route("/groups", methods=["GET"])
def list_groups():
    """Return all whitelisted groups with task counts."""
    groups = get_groups()
    return jsonify({
        "ok": True,
        "groups": [
            {
                "jid": g["jid"],
                "name": g["name"],
                "category": g["category"],
                "tldr": g.get("tldr") or "",
                "whitelisted_at": g.get("whitelisted_at"),
                "task_count": g.get("task_count", 0),
                "active_count": g.get("active_count", 0),
                "last_refreshed_at": g.get("last_refreshed_at"),
            }
            for g in groups
        ],
    })
