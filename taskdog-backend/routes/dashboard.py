"""
TaskDog v2 — Dashboard routes (Stage 4).

GET  /api/dashboard              — all tasks with stats, sorted by importance
GET  /api/tasks/<task_id>        — full task detail
GET  /api/tasks/<task_id>/messages — messages tagged for a task
PATCH /api/tasks/<task_id>       — manual override (status, importance)
"""
from flask import Blueprint, request, jsonify
from datetime import datetime

from models.database_v2 import (
    get_all_tasks,
    get_dashboard_stats,
    get_task,
    get_task_messages,
    update_task_status,
    update_task_importance,
)
from utils.contact_resolver import resolve_contact, resolve_task_assignees

bp = Blueprint("dashboard_v2", __name__, url_prefix="/api")


def _days_since(iso_ts: str) -> int:
    if not iso_ts:
        return 0
    try:
        dt = datetime.strptime(iso_ts[:19], "%Y-%m-%d %H:%M:%S")
        return (datetime.now() - dt).days
    except (ValueError, TypeError):
        return 0


@bp.route("/dashboard")
def dashboard():
    group_jid = request.args.get("group_jid")

    tasks = get_all_tasks(group_jid)
    stats = get_dashboard_stats()

    enriched = []
    for t in tasks:
        assignee_raw = t.get("assignee") or ""
        assignee_name = resolve_contact(assignee_raw) if assignee_raw else ""
        if not assignee_name or assignee_name == assignee_raw:
            assignee_name = assignee_raw

        enriched.append({
            "id": t["id"],
            "group_jid": t["group_jid"],
            "group_name": t.get("group_name", ""),
            "title": t["title"],
            "status": t["status"],
            "importance": t["importance"],
            "assignee": assignee_name,
            "context": t.get("context") or "",
            "latest_progress": t.get("latest_progress"),
            "has_deep_dive": t.get("has_deep_dive", False),
            "days_since_refresh": _days_since(t.get("updated_at")),
            "message_count": t.get("message_count", 0),
            "created_at": t.get("created_at"),
            "updated_at": t.get("updated_at"),
        })

    return jsonify({"ok": True, "tasks": enriched, "stats": stats})


@bp.route("/tasks/<task_id>")
def task_detail(task_id):
    task = get_task(task_id)
    if not task:
        return jsonify({"ok": False, "error": "Task not found"}), 404
    task = resolve_task_assignees(task)
    return jsonify({"ok": True, "task": task})


@bp.route("/tasks/<task_id>/messages")
def task_messages(task_id):
    """Return messages tagged as relevant to a task."""
    messages = get_task_messages(task_id)
    return jsonify({"ok": True, "messages": messages})


@bp.route("/tasks/<task_id>", methods=["PATCH"])
def update_task(task_id):
    """Manual override for task fields. Only `status` and `importance` are editable."""
    data = request.get_json(silent=True) or {}

    if "status" in data:
        status = data["status"]
        if status not in ("active", "completed", "archived"):
            return jsonify({
                "ok": False,
                "error": "status must be 'active', 'completed', or 'archived'",
            }), 400
        update_task_status(task_id, status)

    if "importance" in data:
        importance = data["importance"]
        try:
            importance = int(importance)
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "importance must be an integer 1-5"}), 400
        if not (1 <= importance <= 5):
            return jsonify({"ok": False, "error": "importance must be 1-5"}), 400
        update_task_importance(task_id, importance)

    return jsonify({"ok": True})
