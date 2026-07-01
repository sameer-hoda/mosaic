"""
API routes for TaskDog v1 backend.
Handles session resets, bridge status, classification, extraction, Kanban queries, and nudges.
"""
from flask import Blueprint, request, jsonify, Response, stream_with_context
import os
import json
import glob
import socket
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

from models.database import (
    init_db,
    fetch_top_chats,
    fetch_chat_messages,
    fetch_chat_messages_since,
    save_whitelisted_groups,
    get_whitelisted_groups,
    get_whitelisted_jids,
    save_extracted_themes_and_tasks,
    get_kanban_tasks,
    update_task_status,
    record_nudge,
    get_nudge_history,
    get_tasks_stats,
    get_cached_classifications_for_jids,
    upsert_classification,
    update_classification_category,
)
from models.database_v2 import get_whitelisted_jids_v2

# Default to fetching the top 100 active chats so the user has plenty
# to whitelist without a second round-trip.
DEFAULT_CLASSIFY_LIMIT = 100
from utils.gemini_client import classify_chat, extract_tasks

bp = Blueprint('tasks', __name__, url_prefix='/api')

BRIDGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..',
                                          'whatsapp-mcp', 'whatsapp-bridge'))

# Resolve the correct bridge binary for the platform
_arch = __import__('platform').machine()
if os.path.isfile(os.path.join(BRIDGE_DIR, 'wa-bridge')):
    BRIDGE_BIN = os.path.join(BRIDGE_DIR, 'wa-bridge')
elif _arch == 'x86_64':
    BRIDGE_BIN = os.path.join(BRIDGE_DIR, 'wa-bridge-x86_64')
elif _arch == 'arm64':
    BRIDGE_BIN = os.path.join(BRIDGE_DIR, 'wa-bridge-arm64')
else:
    BRIDGE_BIN = os.path.join(BRIDGE_DIR, 'wa-bridge')

# Track the bridge process so we can manage its lifecycle
_bridge_process = None


def _get_bridge_pid():
    """Return the PID of the running wa-bridge Go binary process, or None.

    NOTE: We match the full path to the wa-bridge binary, NOT the generic
    'whatsapp-bridge' substring, because on macOS the WhatsApp desktop app
    process (WhatsApp.app) also matches that substring and would cause a
    false positive (the app is always running), preventing the bridge from
    ever being started.
    """
    try:
        output = subprocess.check_output(
            ["pgrep", "-f", BRIDGE_BIN], text=True
        )
        pids = [p for p in output.strip().split('\n') if p]
        if pids:
            return int(pids[0])
    except (subprocess.CalledProcessError, ValueError):
        pass
    return None


# Helper to check if bridge REST server is listening on port 8080
def is_port_open(port=8080):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.connect(('127.0.0.1', port))
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False


# Helper to check if Go bridge process is running.
# Matches the full path to the wa-bridge binary to avoid false positives
# from the macOS WhatsApp desktop app (WhatsApp.app), which would otherwise
# match a generic 'whatsapp-bridge' substring and cause the bridge to never
# start.
def is_bridge_process_running():
    try:
        output = subprocess.check_output(["pgrep", "-f", BRIDGE_BIN], text=True)
        return len(output.strip()) > 0
    except subprocess.CalledProcessError:
        return False


@bp.route('/setup/reset', methods=['POST'])
def setup_reset():
    """
    Terminates any running bridge instance, purges SQLite DB files in bridge store,
    and resets the local task database to start fresh.
    """
    try:
        # 1. Kill any running bridge processes
        # Use the full binary path to avoid killing the macOS WhatsApp app.
        subprocess.run(["pkill", "-f", BRIDGE_BIN], capture_output=True)
        subprocess.run(["pkill", "-f", "server"], capture_output=True)

        # 2. Delete database files in store directory
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        store_dir = os.path.join(base_dir, 'whatsapp-mcp', 'whatsapp-bridge', 'store')
        
        # Ensure directory exists
        os.makedirs(store_dir, exist_ok=True)
        
        # Purge files
        purged_files = []
        for file_pattern in ["whatsapp.db*", "messages.db*"]:
            for filepath in glob.glob(os.path.join(store_dir, file_pattern)):
                try:
                    os.remove(filepath)
                    purged_files.append(os.path.basename(filepath))
                except OSError as e:
                    print(f"Error removing {filepath}: {e}")

        # 3. Reset local taskdog database
        init_db(force=True)

        return jsonify({
            "ok": True,
            "message": "Session and tasks reset successfully.",
            "purged_files": purged_files
        })
    except Exception as e:
        print(f"Error in setup_reset: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route('/bridge/start', methods=['POST'])
def start_bridge():
    """Start the WhatsApp bridge process (route handler)."""
    result = _do_start_bridge()
    if result.get("error"):
        return jsonify(result), 400
    return jsonify(result)


def _do_start_bridge():
    """
    Start the WhatsApp bridge process. Idempotent — no-op if already running.
    Only starts if a GEMINI_API_KEY is set (Gate A must be passed first).
    Returns a plain dict (not Flask response) so non-route code can call it.
    """
    global _bridge_process

    key = os.environ.get('GEMINI_API_KEY', '').strip()
    if not key:
        print("[bridge/start] No GEMINI_API_KEY set, refusing to start")
        return {"ok": False, "error": "Gemini API key not set."}

    port_open = is_port_open(8080)
    proc_running = is_bridge_process_running()
    print(f"[bridge/start] key_set={bool(key)} port_open={port_open} proc_running={proc_running}", flush=True)

    if port_open or proc_running:
        print("[bridge/start] bridge already running, skipping", flush=True)
        return {"ok": True, "status": "already_running"}

    if not os.path.isfile(BRIDGE_BIN):
        print(f"[bridge/start] binary not found: {BRIDGE_BIN}", flush=True)
        return {"ok": False, "error": f"Bridge binary not found: {BRIDGE_BIN}"}

    try:
        bridge_log = open('/tmp/taskdog_bridge.log', 'w')
        _bridge_process = subprocess.Popen(
            [BRIDGE_BIN],
            cwd=BRIDGE_DIR,
            stdout=bridge_log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        print(f"[bridge/start] started bridge pid={_bridge_process.pid} cwd={BRIDGE_DIR}", flush=True)
        return {"ok": True, "status": "started"}
    except Exception as e:
        print(f"[bridge/start] failed: {e}", flush=True)
        return {"ok": False, "error": f"Failed to start bridge: {e}"}


@bp.route('/bridge/stop', methods=['POST'])
def stop_bridge():
    """Stop the WhatsApp bridge process."""
    try:
        # Use the full binary path to avoid killing the macOS WhatsApp app.
        subprocess.run(["pkill", "-f", BRIDGE_BIN], capture_output=True)
        return jsonify({"ok": True, "message": "Bridge stopped."})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route('/bridge/status', methods=['GET'])
def get_bridge_status():
    """
    Returns the current state of the WhatsApp bridge:
    - 'connected': Go REST server is up on port 8080 and reports authenticated
    - 'pairing': Go process is running but not authenticated (waiting for QR scan)
    - 'offline': Go process is not running
    """
    try:
        port_open = is_port_open(8080)
        process_running = is_bridge_process_running()
        print(f"[bridge/status] port_open={port_open} process_running={process_running}", flush=True)

        if port_open:
            try:
                resp = requests.get('http://127.0.0.1:8080/api/status', timeout=2)
                print(f"[bridge/status] bridge /api/status -> {resp.status_code} {resp.text[:200]}", flush=True)
                if resp.status_code == 200:
                    bdata = resp.json()
                    if bdata.get('connected') and bdata.get('jid'):
                        return jsonify({"connected": True, "status": "connected"})
            except Exception as e:
                print(f"[bridge/status] error hitting bridge /api/status: {e}", flush=True)
            return jsonify({"connected": False, "status": "pairing"})
        elif process_running:
            return jsonify({"connected": False, "status": "pairing"})
        else:
            return jsonify({"connected": False, "status": "offline"})
    except Exception as e:
        print(f"Error in get_bridge_status: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route('/bridge/qr', methods=['GET'])
def get_bridge_qr():
    """
    Proxies the current QR code from the WhatsApp bridge's /api/qr endpoint.
    Returns {qr: string, event: "code"|"success"|"timeout"|"offline"|"error"}
    """
    try:
        port_open = is_port_open(8080)
        print(f"[bridge/qr] port_open={port_open}", flush=True)
        if not port_open:
            print("[bridge/qr] returning offline (port 8080 not open)", flush=True)
            return jsonify({"qr": "", "event": "offline"})
        resp = requests.get('http://127.0.0.1:8080/api/qr', timeout=2)
        print(f"[bridge/qr] bridge /api/qr -> {resp.status_code}, event={resp.json().get('event','')}, qrRawLen={len(resp.json().get('qr_raw',''))}", flush=True)
        if resp.status_code == 200:
            return jsonify(resp.json())
    except Exception as e:
        print(f"[bridge/qr] error: {e}", flush=True)
    return jsonify({"qr": "", "event": "error"})


@bp.route('/chats/classify', methods=['POST'])
def classify_chats():
    """
    Fetches the top N non-archived chats (default 100) and returns each
    chat's category + TLDR. Cached classifications are returned from the
    `chat_classifications` table; only uncached chats hit Gemini.

    Request body (all optional):
        { "force": true, "limit": 100 }   — bypass cache; cap chats.

    Response:
        {
          "ok": true,
          "chats": [{jid, name, category, tldr, is_whitelisted, from_cache}, ...],
          "total": 30,
          "cached_count": 25,
          "new_count": 5
        }
    """
    try:
        body = request.get_json(silent=True) or {}
        force = bool(body.get('force', False)) or \
                request.args.get('force', '').lower() == 'true'
        try:
            limit = int(body.get('limit') or request.args.get('limit') or DEFAULT_CLASSIFY_LIMIT)
            limit = max(1, min(limit, 500))  # hard cap
        except (TypeError, ValueError):
            limit = DEFAULT_CLASSIFY_LIMIT

        chats = fetch_top_chats(limit=limit)
        if not chats:
            return jsonify({
                "ok": True,
                "chats": [],
                "total": 0,
                "cached_count": 0,
                "new_count": 0,
                "message": "No chats found in WhatsApp database yet."
            })

        # Whitelisted JIDs go to a set for O(1) lookup. The response
        # carries `is_whitelisted` so the UI can pre-tick the cards.
        whitelisted = get_whitelisted_jids() | get_whitelisted_jids_v2()

        # Cached classifications. Bypassed when force=True.
        cached = {} if force else get_cached_classifications_for_jids([c['jid'] for c in chats])

        def process_chat(chat):
            jid = chat['jid']
            name = chat['name']
            cached_row = cached.get(jid)
            if cached_row:
                # Keep the live display name (WhatsApp rename) but use cached
                # category + tldr.
                return {
                    "jid": jid,
                    "name": name,
                    "category": cached_row['category'],
                    "tldr": cached_row['tldr'],
                    "is_whitelisted": jid in whitelisted,
                    "from_cache": True,
                }

            messages = fetch_chat_messages(jid, limit=25)
            if not messages:
                return {
                    "jid": jid,
                    "name": name,
                    "category": "Personal",
                    "tldr": "No recent messages found.",
                    "is_whitelisted": jid in whitelisted,
                    "from_cache": False,
                }
            classification = classify_chat(name, messages)
            category = classification.get("category", "Personal")
            if category not in ("Work", "Personal"):
                category = "Personal"
            return {
                "jid": jid,
                "name": name,
                "category": category,
                "tldr": classification.get("tldr", "No summary available."),
                "is_whitelisted": jid in whitelisted,
                "from_cache": False,
            }

        classified_chats = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_chat = {executor.submit(process_chat, chat): chat for chat in chats}
            for future in concurrent.futures.as_completed(future_to_chat):
                try:
                    res = future.result()
                    classified_chats.append(res)
                    if not res.get('from_cache'):
                        # Persist to cache so the next visit is instant.
                        try:
                            upsert_classification(
                                res['jid'], res['name'], res['category'], res['tldr']
                            )
                        except Exception as e:
                            print(f"Error caching classification for {res['jid']}: {e}")
                except Exception as e:
                    chat = future_to_chat[future]
                    print(f"Error classifying chat '{chat['name']}': {e}")
                    classified_chats.append({
                        "jid": chat['jid'],
                        "name": chat['name'],
                        "category": "Personal",
                        "tldr": "Classification failed.",
                        "is_whitelisted": chat['jid'] in whitelisted,
                        "from_cache": False,
                    })

        # Stable display order: Work first, then Personal, then by name.
        classified_chats.sort(key=lambda c: (c.get('category', ''), (c.get('name') or '').lower()))

        return jsonify({
            "ok": True,
            "chats": classified_chats,
            "total": len(classified_chats),
            "cached_count": sum(1 for c in classified_chats if c.get('from_cache')),
            "new_count": sum(1 for c in classified_chats if not c.get('from_cache')),
        })
    except Exception as e:
        print(f"Error in classify_chats: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route('/chats/classify/stream', methods=['POST'])
def classify_chats_stream():
    """
    Streaming variant of /chats/classify. Returns Server-Sent Events:

        event: meta
        data: {"total": 100}

        event: chat
        data: {"jid": "...", "name": "...", "category": "Work", "tldr": "...",
               "is_whitelisted": false, "from_cache": true}

        event: done
        data: {"ok": true}

    Cached chats are emitted synchronously up front so the UI can fill
    instantly. Uncached chats are emitted as Gemini returns them, in
    completion order (not insertion order).
    """
    body = request.get_json(silent=True) or {}
    force = bool(body.get('force', False))
    try:
        limit = int(body.get('limit') or DEFAULT_CLASSIFY_LIMIT)
        limit = max(1, min(limit, 500))
    except (TypeError, ValueError):
        limit = DEFAULT_CLASSIFY_LIMIT

    def _sse(event: str, payload: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(payload)}\n\n"

    def generate():
        try:
            chats = fetch_top_chats(limit=limit)
        except Exception as e:
            yield _sse('error', {'ok': False, 'error': str(e)})
            return

        if not chats:
            yield _sse('meta', {'total': 0, 'cached_count': 0, 'new_count': 0})
            yield _sse('done', {'ok': True})
            return

        try:
            whitelisted = get_whitelisted_jids() | get_whitelisted_jids_v2()
            cached = {} if force else get_cached_classifications_for_jids([c['jid'] for c in chats])
        except Exception as e:
            yield _sse('error', {'ok': False, 'error': f'cache lookup failed: {e}'})
            return

        uncached = []
        cached_count = 0
        # Emit cached rows first so the UI fills instantly.
        for chat in chats:
            jid = chat['jid']
            row = cached.get(jid)
            if row:
                cached_count += 1
                yield _sse('chat', {
                    'jid': jid,
                    'name': chat['name'],
                    'category': row['category'],
                    'tldr': row['tldr'],
                    'is_whitelisted': jid in whitelisted,
                    'from_cache': True,
                })
            else:
                uncached.append(chat)

        yield _sse('meta', {
            'total': len(chats),
            'cached_count': cached_count,
            'new_count': len(uncached),
        })

        if not uncached:
            yield _sse('done', {'ok': True})
            return

        def process_chat(chat):
            jid = chat['jid']
            messages = fetch_chat_messages(jid, limit=25)
            if not messages:
                return {
                    'jid': jid,
                    'name': chat['name'],
                    'category': 'Personal',
                    'tldr': 'No recent messages found.',
                    'is_whitelisted': jid in whitelisted,
                    'from_cache': False,
                }
            classification = classify_chat(chat['name'], messages)
            category = classification.get('category', 'Personal')
            if category not in ('Work', 'Personal'):
                category = 'Personal'
            return {
                'jid': jid,
                'name': chat['name'],
                'category': category,
                'tldr': classification.get('tldr', 'No summary available.'),
                'is_whitelisted': jid in whitelisted,
                'from_cache': False,
            }

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_chat = {executor.submit(process_chat, chat): chat for chat in uncached}
            for future in concurrent.futures.as_completed(future_to_chat):
                try:
                    res = future.result()
                except Exception as e:
                    chat = future_to_chat[future]
                    print(f"Error classifying chat '{chat['name']}': {e}")
                    res = {
                        'jid': chat['jid'],
                        'name': chat['name'],
                        'category': 'Personal',
                        'tldr': 'Classification failed.',
                        'is_whitelisted': chat['jid'] in whitelisted,
                        'from_cache': False,
                    }
                # Persist to cache.
                try:
                    upsert_classification(res['jid'], res['name'], res['category'], res['tldr'])
                except Exception as e:
                    print(f"Error caching classification for {res['jid']}: {e}")
                yield _sse('chat', res)

        yield _sse('done', {'ok': True})

    response = Response(stream_with_context(generate()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # disable proxy buffering
    response.headers['Connection'] = 'keep-alive'
    return response


@bp.route('/chats/classify/update_category', methods=['POST'])
def update_classify_category():
    """
    Update the cached category for a single chat. Used after the user
    drags a card from one column to another.

    Body: { "jid": "<jid>", "category": "Work" | "Personal" }
    """
    try:
        body = request.get_json(silent=True) or {}
        jid = (body.get('jid') or '').strip()
        category = (body.get('category') or '').strip()
        if not jid or category not in ('Work', 'Personal'):
            return jsonify({
                'ok': False,
                'error': 'jid and category ("Work" or "Personal") are required.'
            }), 400
        updated = update_classification_category(jid, category)
        return jsonify({'ok': True, 'updated': updated, 'jid': jid, 'category': category})
    except Exception as e:
        print(f"Error in update_classify_category: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/tasks/extract', methods=['POST'])
def extract_tasks_route():
    """
    Receives list of whitelisted chats, saves them, and runs theme/task
    extraction concurrently on the last 30 days of messages.

    Returns a per-chat status so the UI can show the user what actually
    happened (vs. silently dropping groups on Gemini errors):

        {
          "ok": true,
          "total": N,
          "processed": <count of chats with >=1 theme saved>,
          "empty":    <count with 0 themes from Gemini>,
          "failed":   <count where Gemini or save threw>,
          "details":  [{jid, name, status, theme_count, task_count, error?}, ...]
        }

    Possible per-chat `status` values:
        - "ok"            : Gemini returned themes, all saved.
        - "no_messages"   : No 30-day history in the bridge DB.
        - "gemini_failed" : Gemini errored 3x or returned 0 themes.
        - "save_failed"   : DB write failed.
    """
    try:
        data = request.get_json() or {}
        whitelisted_chats = data.get("chats", [])

        if not whitelisted_chats:
            return jsonify({"ok": False, "error": "No whitelisted chats specified."}), 400

        # Persist whitelisted groups first so the dashboard can show them
        # even if extraction fails for some.
        try:
            save_whitelisted_groups(whitelisted_chats)
        except Exception as e:
            print(f"Error saving whitelisted groups: {e}")

        # Cap concurrency to avoid hitting Gemini rate limits. 3 is a
        # good balance — fast enough that 30 chats finish in ~10 batches,
        # slow enough that 30 parallel calls don't trip a 429.
        MAX_WORKERS = 3
        status_lock = __import__("threading").Lock()
        results = {}  # jid -> {status, theme_count, task_count, error}

        def process_group(chat):
            """Returns (jid, status_dict). All failure modes captured."""
            jid = chat['jid']
            name = chat.get('name') or jid
            try:
                messages = fetch_chat_messages_since(jid, days=30)
            except Exception as e:
                return jid, {"status": "no_messages", "error": f"fetch error: {e}"}
            if not messages:
                return jid, {"status": "no_messages"}

            try:
                result = extract_tasks(name, messages)
            except Exception as e:
                return jid, {"status": "gemini_failed", "error": f"extract error: {e}"}

            themes = result.get("themes") or []
            if not themes:
                return jid, {
                    "status": "gemini_failed",
                    "error": result.get("error") or "no themes returned"
                }

            task_count = sum(len(t.get("tasks") or []) for t in themes)
            try:
                save_extracted_themes_and_tasks(jid, themes)
            except Exception as e:
                return jid, {
                    "status": "save_failed",
                    "theme_count": len(themes),
                    "task_count": task_count,
                    "error": f"save error: {e}",
                }
            return jid, {
                "status": "ok",
                "theme_count": len(themes),
                "task_count": task_count,
            }

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_chat = {
                executor.submit(process_group, chat): chat
                for chat in whitelisted_chats
            }
            for future in concurrent.futures.as_completed(future_to_chat):
                chat = future_to_chat[future]
                try:
                    jid, payload = future.result()
                except Exception as e:
                    jid = chat.get('jid')
                    payload = {"status": "gemini_failed", "error": f"worker error: {e}"}
                with status_lock:
                    results[jid] = {
                        "name": chat.get('name') or jid,
                        **payload,
                    }
                # Log the per-chat outcome for the operator.
                print(f"[extract] jid={jid} status={payload.get('status')} "
                      f"themes={payload.get('theme_count', 0)} "
                      f"tasks={payload.get('task_count', 0)} "
                      f"err={payload.get('error', '-')}")

        # Build the summary.
        details = [
            {"jid": jid, "name": v.get("name", jid), **v}
            for jid, v in results.items()
        ]
        processed = sum(1 for v in results.values() if v.get("status") == "ok")
        empty = sum(
            1 for v in results.values()
            if v.get("status") in ("no_messages", "gemini_failed")
            and not v.get("theme_count")
        )
        failed = sum(
            1 for v in results.values()
            if v.get("status") in ("save_failed", "gemini_failed")
        )
        # `empty` here is "tried but got no themes"; `failed` is "error path".
        # We re-compute for clarity:
        no_messages = sum(1 for v in results.values() if v.get("status") == "no_messages")
        gemini_failed = sum(1 for v in results.values()
                            if v.get("status") == "gemini_failed" and not v.get("theme_count"))
        save_failed = sum(1 for v in results.values() if v.get("status") == "save_failed")
        gemini_empty = sum(1 for v in results.values()
                           if v.get("status") == "gemini_failed" and v.get("theme_count"))

        print(f"[extract] summary: total={len(whitelisted_chats)} "
              f"ok={processed} no_messages={no_messages} "
              f"gemini_empty={gemini_empty} gemini_failed={gemini_failed} "
              f"save_failed={save_failed}")

        return jsonify({
            "ok": True,
            "total": len(whitelisted_chats),
            "processed": processed,
            "no_messages": no_messages,
            "gemini_empty": gemini_empty,
            "gemini_failed": gemini_failed,
            "save_failed": save_failed,
            "details": details,
        })
    except Exception as e:
        print(f"Error in extract_tasks_route: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route('/tasks/extract/stream', methods=['POST'])
def extract_tasks_stream_route():
    """
    Streaming variant of /tasks/extract. Emits Server-Sent Events as each
    group finishes so the UI can show real-time per-group progress.

    Events:
      - meta  : {"total": N}  — sent once, before any chat events.
      - chat  : {jid, name, status, theme_count, task_count, error?}
                 sent once per completed group, in finish order.
      - done  : {ok, total, processed, no_messages, gemini_empty,
                 gemini_failed, save_failed}  — sent last.
      - error : {ok: false, error}  — only on hard failure.

    `status` values match /tasks/extract: "ok" | "no_messages" |
    "gemini_failed" | "save_failed".
    """
    try:
        data = request.get_json() or {}
        whitelisted_chats = data.get("chats", [])

        if not whitelisted_chats:
            return jsonify({"ok": False, "error": "No whitelisted chats specified."}), 400

        # Persist whitelisted groups first so the dashboard can show them
        # even if extraction fails for some.
        try:
            save_whitelisted_groups(whitelisted_chats)
        except Exception as e:
            print(f"Error saving whitelisted groups: {e}")

        MAX_WORKERS = 3

        def _sse(event: str, payload: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(payload)}\n\n"

        def process_group(chat):
            """Same per-chat handler as the non-streaming route."""
            jid = chat['jid']
            name = chat.get('name') or jid
            try:
                messages = fetch_chat_messages_since(jid, days=30)
            except Exception as e:
                return jid, name, {"status": "no_messages", "error": f"fetch error: {e}"}
            if not messages:
                return jid, name, {"status": "no_messages"}

            try:
                result = extract_tasks(name, messages)
            except Exception as e:
                return jid, name, {"status": "gemini_failed", "error": f"extract error: {e}"}

            themes = result.get("themes") or []
            if not themes:
                return jid, name, {
                    "status": "gemini_failed",
                    "error": result.get("error") or "no themes returned"
                }

            task_count = sum(len(t.get("tasks") or []) for t in themes)
            try:
                save_extracted_themes_and_tasks(jid, themes)
            except Exception as e:
                return jid, name, {
                    "status": "save_failed",
                    "theme_count": len(themes),
                    "task_count": task_count,
                    "error": f"save error: {e}",
                }
            return jid, name, {
                "status": "ok",
                "theme_count": len(themes),
                "task_count": task_count,
            }

        def generate():
            """Generator that yields chat events as they complete."""
            yield _sse('meta', {'total': len(whitelisted_chats)})

            processed = 0
            no_messages = 0
            gemini_empty = 0
            gemini_failed = 0
            save_failed = 0

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_chat = {
                    executor.submit(process_group, chat): chat
                    for chat in whitelisted_chats
                }
                for future in concurrent.futures.as_completed(future_to_chat):
                    chat = future_to_chat[future]
                    try:
                        jid, name, payload = future.result()
                    except Exception as e:
                        jid = chat.get('jid')
                        name = chat.get('name') or jid
                        payload = {"status": "gemini_failed", "error": f"worker error: {e}"}

                    status = payload.get("status", "gemini_failed")
                    if status == "ok":
                        processed += 1
                    elif status == "no_messages":
                        no_messages += 1
                    elif status == "save_failed":
                        save_failed += 1
                    else:  # gemini_failed
                        if payload.get("theme_count"):
                            gemini_empty += 1
                        else:
                            gemini_failed += 1

                    # Build the per-chat event payload. Always include the
                    # chat name so the UI can show it without a second
                    # request. theme_count/task_count only meaningful for
                    # "ok" / "save_failed".
                    chat_event = {
                        "jid": jid,
                        "name": name,
                        "status": status,
                        "theme_count": payload.get("theme_count", 0),
                        "task_count": payload.get("task_count", 0),
                    }
                    if payload.get("error"):
                        chat_event["error"] = payload["error"]
                    yield _sse('chat', chat_event)

            yield _sse('done', {
                "ok": True,
                "total": len(whitelisted_chats),
                "processed": processed,
                "no_messages": no_messages,
                "gemini_empty": gemini_empty,
                "gemini_failed": gemini_failed,
                "save_failed": save_failed,
            })

        response = Response(stream_with_context(generate()), mimetype='text/event-stream')
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Accel-Buffering'] = 'no'  # disable proxy buffering
        return response
    except Exception as e:
        print(f"Error in extract_tasks_stream_route: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route('/tasks', methods=['GET'])
def get_tasks():
    """
    Returns tasks for the Kanban board, optionally filtered by a specific group JID.
    """
    try:
        group_jid = request.args.get('group_jid')
        tasks = get_kanban_tasks(group_jid)
        stats = get_tasks_stats()
        return jsonify({
            "ok": True,
            "tasks": tasks,
            "stats": stats
        })
    except Exception as e:
        print(f"Error in get_tasks: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route('/tasks/update_status', methods=['POST'])
def update_status_route():
    """
    Manually update a task's Kanban column (e.g. from drag & drop).
    """
    try:
        data = request.get_json() or {}
        task_id = data.get("task_id")
        status = data.get("status")
        
        if not task_id or not status:
            return jsonify({"ok": False, "error": "task_id and status are required."}), 400
            
        if status not in ['not started', 'pending', 'done']:
            return jsonify({"ok": False, "error": "Invalid status. Must be 'not started', 'pending', or 'done'."}), 400
            
        update_task_status(task_id, status)
        return jsonify({"ok": True})
    except Exception as e:
        print(f"Error in update_status_route: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route('/send', methods=['POST'])
def send_nudge():
    """
    Dispatches a nudge message to WhatsApp via the Go bridge.
    Resolves the recipient from the v2 task's group if not explicitly provided.
    """
    try:
        data = request.get_json() or {}
        task_id = data.get("task_id")
        message = data.get("message")
        recipient = data.get("recipient")

        if not task_id or not message:
            return jsonify({"ok": False, "error": "task_id and message are required."}), 400

        if not recipient:
            # Auto-resolve from v2 tasks table
            try:
                from models.database_v2 import get_task_group_jid
                recipient = get_task_group_jid(task_id)
            except Exception:
                pass

        if not recipient:
            return jsonify({"ok": False, "error": "recipient is required (could not be auto-resolved from task)."}), 400

        payload = {
            "recipient": recipient,
            "message": message
        }

        response = requests.post("http://localhost:8080/api/send", json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            update_task_status(task_id, 'pending')
            record_nudge(task_id, message, recipient)
            # Also record in v2 followup_history
            try:
                from models.database_v2 import record_followup
                record_followup(task_id, message, recipient)
            except Exception:
                pass
            return jsonify({"ok": True})
        else:
            return jsonify({
                "ok": False,
                "error": f"Failed to send: {result.get('message', 'Unknown error')}"
            }), 500
    except requests.exceptions.ConnectionError:
        return jsonify({
            "ok": False,
            "error": "Cannot connect to WhatsApp bridge. Make sure the Go bridge is running on port 8080."
        }), 500
    except Exception as e:
        print(f"Error in send_nudge: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route('/history', methods=['GET'])
def get_history():
    """
    Returns nudge dispatch history log.
    """
    try:
        history = get_nudge_history(limit=50)
        return jsonify({
            "ok": True,
            "history": history
        })
    except Exception as e:
        print(f"Error in get_history: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


# NOTE: GET /api/groups is now handled by v2's routes/groups.py
# (reads from the v2 `groups` table with task counts).


@bp.route('/chats/list', methods=['GET'])
def list_chats():
    """
    Returns a flat list of all non-archived chats from the bridge DB,
    sorted by most recent message first. No Gemini calls, no classification.
    Used by the simplified whitelist page.

    Response:
        {
          "ok": true,
          "chats": [{jid, name, last_message_time, is_whitelisted}, ...],
          "total": N
        }
    """
    try:
        chats = fetch_top_chats(limit=200)
        whitelisted = get_whitelisted_jids() | get_whitelisted_jids_v2()
        result = []
        for c in chats:
            result.append({
                "jid": c["jid"],
                "name": c["name"],
                "last_message_time": c.get("last_message_time"),
                "is_whitelisted": c["jid"] in whitelisted,
            })
        return jsonify({
            "ok": True,
            "chats": result,
            "total": len(result),
        })
    except Exception as e:
        print(f"Error in list_chats: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500