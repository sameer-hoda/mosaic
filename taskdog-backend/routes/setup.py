"""
TaskDog v2 — Onboarding / setup routes.

Gate A: GET  /api/health          — combined health (gemini key + bridge)
         POST /api/setup/validate-key
Gate B: Uses v1's GET /api/bridge/status (unchanged)
Gate C: Uses v1's POST /api/chats/classify (unchanged)
"""
from flask import Blueprint, request, jsonify
import os
import socket
import subprocess
import requests

bp = Blueprint("setup_v2", __name__, url_prefix="/api")


def _is_port_open(port=8080):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.connect(("127.0.0.1", port))
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False


def _is_bridge_process_running():
    # Match the full path to the wa-bridge binary to avoid false positives
    # from the macOS WhatsApp desktop app (WhatsApp.app), which would match
    # a generic 'whatsapp-bridge' substring and cause the bridge to never
    # start.
    bridge_bin = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', '..',
        'whatsapp-mcp', 'whatsapp-bridge', 'wa-bridge'))
    try:
        output = subprocess.check_output(
            ["pgrep", "-f", bridge_bin], text=True
        )
        return len(output.strip()) > 0
    except subprocess.CalledProcessError:
        return False


def _get_bridge_status() -> str:
    """Return 'connected', 'pairing', or 'offline'."""
    if _is_port_open(8080):
        try:
            resp = requests.get("http://127.0.0.1:8080/api/status", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("connected") and data.get("jid"):
                    return "connected"
        except Exception:
            pass
        return "pairing"
    if _is_bridge_process_running():
        return "pairing"
    return "offline"


def _key_preview(key: str) -> str:
    """Show first 4 + last 3 chars of an API key."""
    if not key or len(key) < 8:
        return ""
    return f"{key[:4]}…{key[-3:]}"


@bp.route("/health")
def health():
    """Combined health check — gemini key status + bridge status.
    Auto-starts the bridge if the key is set but bridge is offline.
    """
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    bridge = _get_bridge_status()
    print(f"[health] key_set={bool(key)} bridge_status={bridge}", flush=True)

    # Auto-start bridge if key is set but bridge hasn't been started yet.
    if key and bridge == "offline":
        print("[health] key set + bridge offline → auto-starting bridge", flush=True)
        try:
            from routes.tasks import _do_start_bridge
            result = _do_start_bridge()
            print(f"[health] auto-start result: {result}", flush=True)
            import time
            time.sleep(2)  # give bridge a moment to open its port
            bridge = _get_bridge_status()
            print(f"[health] bridge status after auto-start: {bridge}", flush=True)
        except Exception as e:
            print(f"[health] auto-start failed: {e}", flush=True)

    return jsonify({
        "ok": True,
        "gemini_key_set": bool(key),
        "gemini_key_preview": _key_preview(key) if key else "",
        "bridge_status": bridge,
    })


@bp.route("/setup/validate-key", methods=["POST"])
def validate_key():
    """Validate and save a Gemini API key.

    On successful validation, persists the key to the .env file and sets it
    in the current process environment so downstream endpoints (bridge start,
    pipeline, etc.) can use it immediately.
    """
    data = request.get_json(silent=True) or {}
    key = (data.get("key") or "").strip()
    if not key:
        return jsonify({"ok": False, "error": "No key provided"}), 400

    try:
        resp = requests.get(
            "https://generativelanguage.googleapis.com/v1beta/models",
            params={"key": key},
            timeout=10,
        )
        if resp.status_code == 200:
            _save_key_to_env(key)
            os.environ['GEMINI_API_KEY'] = key
            return jsonify({"ok": True, "preview": _key_preview(key)})
        else:
            return jsonify({
                "ok": False,
                "error": f"Invalid key (rejected by Gemini: {resp.status_code})",
            })
    except requests.exceptions.Timeout:
        return jsonify({"ok": False, "error": "Gemini API timed out (10s)"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"ok": False, "error": f"Request failed: {e}"}), 502


def _save_key_to_env(key: str):
    """Persist the Gemini API key to the .env file in the backend directory."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    lines.append(f'GEMINI_API_KEY={key}\n')
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f'GEMINI_API_KEY={key}\n')
        if lines and not lines[-1].endswith('\n'):
            lines[-1] += '\n'
    with open(env_path, 'w') as f:
        f.writelines(lines)
    print(f"[setup] Saved Gemini API key to {env_path}")
