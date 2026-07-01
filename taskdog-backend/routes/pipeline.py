"""
TaskDog v2 — Pipeline routes (Stages 1, 2, 3).

Stage 1: POST /api/pipeline/discover         — non-streaming
         POST /api/pipeline/discover/stream  — SSE streaming
Stage 2: POST /api/pipeline/refresh          — non-streaming
         POST /api/pipeline/refresh/stream   — SSE streaming
Stage 3: POST /api/pipeline/deep-dive        — synchronous
"""
from flask import Blueprint, request, jsonify, Response, stream_with_context
import json
import uuid
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from models.database import fetch_chat_messages_since, get_user_identity
from models.database_v2 import (
    get_group,
    get_tasks_by_group,
    get_tasks_for_refresh,
    insert_groups,
    insert_tasks,
    save_task,
    update_task_status,
    update_task_importance,
    update_task_progress,
    update_group_refreshed_at,
    update_task_deep_dive,
    get_task,
    get_task_group_jid,
    insert_task_messages,
    get_group_last_refreshed,
)
from utils.gemini_v2 import discover_tasks, refresh_tasks, deep_dive_task
from utils.contact_resolver import resolve_contact

bp = Blueprint("pipeline", __name__, url_prefix="/api/pipeline")

MAX_WORKERS = 3


def _sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _ensure_group_exists(jid: str, name: str = None):
    """Ensure the group exists in v2 groups table. Auto-insert if missing.
    This prevents FK constraint failures when a JID was whitelisted via v1
    but not yet in the v2 table."""
    group = get_group(jid)
    if not group:
        insert_groups([jid], [name or jid.split("@")[0]], ["Personal"], [""])


# ---------------------------------------------------------------------------
# Stage 1 — Task Discovery
# ---------------------------------------------------------------------------

def _process_discovery(jid: str):
    """Run discovery for a single group. Returns (jid, name, status_dict)."""
    group = get_group(jid)
    name = group["name"] if group else jid.split("@")[0]

    # Ensure the group exists in v2 table (prevents FK constraint failures)
    _ensure_group_exists(jid, name)

    try:
        messages = fetch_chat_messages_since(jid, days=30)
    except Exception as e:
        return jid, name, {"status": "no_messages", "error": f"fetch error: {e}"}

    if not messages:
        return jid, name, {"status": "no_messages", "error": "No messages in last 30 days"}

    try:
        result = discover_tasks(name, messages)
    except Exception as e:
        return jid, name, {"status": "gemini_failed", "error": f"discover error: {e}"}

    tasks = result.get("tasks") or []
    if not tasks and result.get("error"):
        return jid, name, {"status": "gemini_failed", "error": result["error"]}

    # Save tasks to DB
    try:
        inserted = insert_tasks(tasks, jid)

        # Save relevant messages for each task
        for i, task in enumerate(inserted):
            indices = task.get("relevant_message_indices") or []
            if indices:
                relevant_msgs = []
                for idx in indices:
                    if 0 <= idx < len(messages):
                        m = messages[idx]
                        relevant_msgs.append({
                            "message_content": m.get("content", ""),
                            "sender_name": m.get("sender", ""),
                            "message_time": m.get("timestamp", ""),
                            "relevance": 1.0,
                        })
                if relevant_msgs:
                    insert_task_messages(task["id"], relevant_msgs)

        update_group_refreshed_at(jid)
    except Exception as e:
        return jid, name, {"status": "save_failed", "task_count": len(tasks),
                           "error": f"save error: {e}"}

    return jid, name, {"status": "ok", "task_count": len(inserted)}


@bp.route("/discover", methods=["POST"])
def discover():
    """Stage 1: Non-streaming task discovery for one or more groups."""
    data = request.get_json(silent=True) or {}
    group_jids = data.get("group_jids") or []
    if not group_jids:
        return jsonify({"ok": False, "error": "No group_jids provided"}), 400

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_process_discovery, jid): jid for jid in group_jids}
        for future in concurrent.futures.as_completed(futures):
            jid = futures[future]
            try:
                rjid, name, status = future.result()
            except Exception as e:
                name = jid
                status = {"status": "gemini_failed", "error": f"worker error: {e}"}
            results.append({
                "jid": rjid,
                "name": name,
                "status": status.get("status", "error"),
                "task_count": status.get("task_count", 0),
                "error": status.get("error"),
            })

    summary = {
        "total_groups": len(group_jids),
        "groups_with_tasks": sum(1 for r in results if r["task_count"] > 0),
        "total_tasks_found": sum(r["task_count"] for r in results),
    }
    return jsonify({"ok": True, "results": results, "summary": summary})


@bp.route("/discover/stream", methods=["POST"])
def discover_stream():
    """Stage 1: SSE streaming task discovery."""
    data = request.get_json(silent=True) or {}
    group_jids = data.get("group_jids") or []
    if not group_jids:
        return jsonify({"ok": False, "error": "No group_jids provided"}), 400

    def generate():
        yield _sse("meta", {"total": len(group_jids)})

        groups_with_tasks = 0
        total_tasks = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(_process_discovery, jid): jid for jid in group_jids}
            for future in concurrent.futures.as_completed(futures):
                jid = futures[future]
                try:
                    rjid, name, status = future.result()
                except Exception as e:
                    name = jid
                    status = {"status": "gemini_failed", "error": f"worker error: {e}"}

                task_count = status.get("task_count", 0)
                if task_count > 0:
                    groups_with_tasks += 1
                    total_tasks += task_count

                event_data = {
                    "jid": rjid,
                    "name": name,
                    "status": status.get("status", "error"),
                    "task_count": task_count,
                }
                if status.get("error"):
                    event_data["error"] = status["error"]
                yield _sse("group", event_data)

        yield _sse("done", {
            "ok": True,
            "total_groups": len(group_jids),
            "groups_with_tasks": groups_with_tasks,
            "total_tasks_found": total_tasks,
        })

    response = Response(stream_with_context(generate()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Connection"] = "keep-alive"
    return response


# ---------------------------------------------------------------------------
# Stage 2 — Task Refresh
# ---------------------------------------------------------------------------

def _process_refresh(jid: str):
    """Run refresh for a single group. Returns (jid, name, status_dict)."""
    group = get_group(jid)
    name = group["name"] if group else jid.split("@")[0]

    # Ensure the group exists in v2 table
    _ensure_group_exists(jid, name)

    # Get current tasks
    current_tasks = get_tasks_for_refresh(jid)
    if not current_tasks:
        # No tasks yet — discovery hasn't run
        return jid, name, {"status": "no_tasks", "error": "No tasks found. Run discovery first."}

    # Determine new messages since last refresh
    last_refreshed = get_group_last_refreshed(jid)
    if last_refreshed:
        # Calculate days since last refresh (add 1 day buffer)
        from datetime import datetime, timedelta
        try:
            dt = datetime.strptime(last_refreshed[:19], "%Y-%m-%d %H:%M:%S")
            days_since = max(1, (datetime.now() - dt).days + 1)
        except (ValueError, TypeError):
            days_since = 30
    else:
        days_since = 30

    try:
        new_messages = fetch_chat_messages_since(jid, days=days_since)
    except Exception as e:
        return jid, name, {"status": "error", "error": f"fetch error: {e}"}

    if not new_messages:
        return jid, name, {"status": "no_messages", "error": "No new messages since last refresh"}

    try:
        result = refresh_tasks(name, current_tasks, new_messages)
    except Exception as e:
        return jid, name, {"status": "error", "error": f"refresh error: {e}"}

    task_updates = result.get("task_updates") or []
    new_tasks_data = result.get("new_tasks") or []

    if result.get("error") and not task_updates and not new_tasks_data:
        return jid, name, {"status": "error", "error": result["error"]}

    # Apply task updates
    updated_count = 0
    completed_count = 0
    archived_count = 0
    for upd in task_updates:
        task_id = upd.get("id")
        status_update = upd.get("status_update", "still_active")
        progress_note = upd.get("progress_note", "")
        importance = upd.get("importance")

        if not task_id:
            continue

        if status_update == "completed":
            update_task_status(task_id, "completed")
            completed_count += 1
        elif status_update == "archived":
            update_task_status(task_id, "archived")
            archived_count += 1

        if importance is not None:
            update_task_importance(task_id, importance)

        if progress_note and progress_note != "No change":
            update_task_progress(task_id, progress_note)

        updated_count += 1

    # Create new tasks (replace "new-XXX" IDs with UUIDs)
    new_count = 0
    for nt in new_tasks_data:
        nt["group_jid"] = jid
        nt["id"] = str(uuid.uuid4())
        task_id = save_task(nt)
        if task_id:
            new_count += 1

    update_group_refreshed_at(jid)

    return jid, name, {
        "status": "ok",
        "tasks_updated": updated_count,
        "tasks_completed": completed_count,
        "tasks_archived": archived_count,
        "new_tasks_found": new_count,
        "task_updates": task_updates,
        "new_tasks": new_tasks_data,
    }


@bp.route("/refresh", methods=["POST"])
def refresh():
    """Stage 2: Non-streaming task refresh for one or more groups."""
    data = request.get_json(silent=True) or {}
    group_jids = data.get("group_jids") or []
    if not group_jids:
        return jsonify({"ok": False, "error": "No group_jids provided"}), 400

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_process_refresh, jid): jid for jid in group_jids}
        for future in concurrent.futures.as_completed(futures):
            jid = futures[future]
            try:
                rjid, name, status = future.result()
            except Exception as e:
                name = jid
                status = {"status": "error", "error": f"worker error: {e}"}
            results.append({
                "jid": rjid,
                "name": name,
                "status": status.get("status", "error"),
                "tasks_updated": status.get("tasks_updated", 0),
                "tasks_completed": status.get("tasks_completed", 0),
                "tasks_archived": status.get("tasks_archived", 0),
                "new_tasks_found": status.get("new_tasks_found", 0),
                "error": status.get("error"),
            })

    return jsonify({"ok": True, "results": results})


@bp.route("/refresh/stream", methods=["POST"])
def refresh_stream():
    """Stage 2: SSE streaming task refresh."""
    data = request.get_json(silent=True) or {}
    group_jids = data.get("group_jids") or []
    if not group_jids:
        return jsonify({"ok": False, "error": "No group_jids provided"}), 400

    def generate():
        total_known = 0
        for jid in group_jids:
            tasks = get_tasks_for_refresh(jid)
            total_known += len(tasks)

        yield _sse("meta", {"total_groups": len(group_jids), "total_known_tasks": total_known})

        total_updated = 0
        total_completed = 0
        total_archived = 0
        total_new = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(_process_refresh, jid): jid for jid in group_jids}
            for future in concurrent.futures.as_completed(futures):
                jid = futures[future]
                try:
                    rjid, name, status = future.result()
                except Exception as e:
                    name = jid
                    status = {"status": "error", "error": f"worker error: {e}"}

                # Emit per-task update events
                for upd in status.get("task_updates") or []:
                    yield _sse("task", {
                        "task_id": upd.get("id"),
                        "status_update": upd.get("status_update"),
                        "progress_note": upd.get("progress_note"),
                    })

                # Emit new task events
                for nt in status.get("new_tasks") or []:
                    yield _sse("new_task", {
                        "title": nt.get("title"),
                        "importance": nt.get("importance"),
                        "assignee": nt.get("assignee"),
                    })

                total_updated += status.get("tasks_updated", 0)
                total_completed += status.get("tasks_completed", 0)
                total_archived += status.get("tasks_archived", 0)
                total_new += status.get("new_tasks_found", 0)

        yield _sse("done", {
            "ok": True,
            "updated": total_updated,
            "completed": total_completed,
            "archived": total_archived,
            "new": total_new,
        })

    response = Response(stream_with_context(generate()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Connection"] = "keep-alive"
    return response


# ---------------------------------------------------------------------------
# Stage 3 — Task Deep-Dive
# ---------------------------------------------------------------------------

@bp.route("/deep-dive", methods=["POST"])
def deep_dive():
    """Stage 3: Comprehensive analysis of a single task. Synchronous (5-20s)."""
    data = request.get_json(silent=True) or {}
    task_id = data.get("task_id")
    if not task_id:
        return jsonify({"ok": False, "error": "No task_id provided"}), 400

    # Get the task
    task = get_task(task_id)
    if not task:
        return jsonify({"ok": False, "error": f"Task not found: {task_id}"}), 404

    # Get group info
    group_jid = task.get("group_jid")
    group = get_group(group_jid) if group_jid else None
    task["group_name"] = group["name"] if group else ""

    # Fetch full transcript (365 days = effectively all)
    try:
        full_messages = fetch_chat_messages_since(group_jid, days=365)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to fetch messages: {e}"}), 500

    if not full_messages:
        return jsonify({"ok": False, "error": "No messages found for this group"}), 400

    # Call Gemini
    try:
        result = deep_dive_task(task, full_messages)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Deep-dive failed: {e}"}), 500

    if "error" in result and "wiki" not in result:
        return jsonify({"ok": False, "error": result["error"]}), 500

    # Resolve any raw JIDs/LIDs in people names and blocker/decision authors
    for person in result.get("people", []):
        if person.get("name"):
            person["name"] = resolve_contact(person["name"])
    for b in result.get("blockers", []):
        if b.get("raised_by"):
            b["raised_by"] = resolve_contact(b["raised_by"])
    for d in result.get("decisions", []):
        if d.get("made_by"):
            d["made_by"] = resolve_contact(d["made_by"])

    # Save to DB
    try:
        update_task_deep_dive(
            task_id,
            wiki=result.get("wiki", ""),
            people=result.get("people", []),
            progress_log=result.get("progress_log", []),
            blockers=result.get("blockers", []),
            decisions=result.get("decisions", []),
            importance=result.get("importance", task.get("importance", 3)),
        )
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to save deep-dive: {e}"}), 500

    # Return the updated task
    updated_task = get_task(task_id)
    return jsonify({"ok": True, "task": updated_task})
