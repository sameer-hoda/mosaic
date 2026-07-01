"""
TaskDog v2 — Nudge generation + Persona management.

POST /api/nudge/generate     — generate 3 nudge variants (gentle, passive, aggressive)
GET  /api/persona            — read current persona
POST /api/persona            — save persona
POST /api/persona/generate   — auto-generate persona from user's WhatsApp messages
"""
import json
import os
import requests
from flask import Blueprint, request, jsonify

from models.database_v2 import get_task, get_task_group_jid, get_task_messages
from utils.gemini_v2 import _call_gemini_v2
from utils.gemini_client import GEMINI_API_KEY, GEMINI_API_BASE, GEMINI_MODEL
from utils.contact_resolver import get_user_name, get_user_identity, resolve_contact
from models.database import fetch_chat_messages

bp = Blueprint("nudge_v2", __name__, url_prefix="/api")

PERSONA_FILE = os.path.join(os.path.dirname(__file__), "..", "persona.txt")
BRIDGE_URL = "http://localhost:8080/api"


def _read_persona() -> str:
    if os.path.exists(PERSONA_FILE):
        with open(PERSONA_FILE, "r") as f:
            return f.read().strip()
    return ""


def _write_persona(text: str):
    with open(PERSONA_FILE, "w") as f:
        f.write(text.strip())


# ═══════════════════════════════════════════════════════════════════
# Persona
# ═══════════════════════════════════════════════════════════════════

@bp.route("/persona", methods=["GET"])
def get_persona():
    return jsonify({"ok": True, "persona": _read_persona()})


@bp.route("/persona", methods=["POST"])
def save_persona():
    data = request.get_json(silent=True) or {}
    persona = (data.get("persona") or "").strip()
    _write_persona(persona)
    return jsonify({"ok": True})


@bp.route("/persona/generate", methods=["POST"])
def generate_persona():
    try:
        res = requests.get(f"{BRIDGE_URL}/messages", params={"limit": 50}, timeout=30)
        if not res.ok:
            return jsonify({"ok": False, "error": f"Bridge error: {res.status_code}"}), 502
        msgs = res.json()
        if isinstance(msgs, list):
            all_msgs = msgs
        elif isinstance(msgs, dict):
            all_msgs = msgs.get("messages", [])
        else:
            all_msgs = []
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to fetch messages: {str(e)}"}), 502

    my_msgs = [
        m for m in all_msgs
        if m.get("is_from_me") or m.get("fromMe") or (m.get("sender", "").lower() in ("you", "me"))
    ]
    if not my_msgs:
        return jsonify({"ok": False, "error": "No messages from you found. Send some WhatsApp messages first."}), 400

    sample_msgs = my_msgs[:50]
    transcript_parts = []
    for m in sample_msgs:
        ts = m.get("timestamp") or m.get("time") or m.get("message_time", "")
        body = m.get("body") or m.get("content") or m.get("message", "")
        if body:
            transcript_parts.append(f"[{ts}] Me: {body}")

    transcript = "\n".join(transcript_parts)
    if len(transcript) < 100:
        return jsonify({"ok": False, "error": "Not enough message content to analyze."}), 400

    user_name = get_user_name()

    prompt = f"""You are analyzing the writing style of a WhatsApp user named "{user_name}" based on their recent messages.

Below is a sample of messages sent by {user_name}. Analyze their tone, style, vocabulary, message length, formality, emoji usage, and any other communication patterns.

Generate a crisp, half-page persona document that serves as a style guide for an AI assistant writing messages ON BEHALF of {user_name}. The persona should capture:
1. Communication tone (formal/casual/direct/warm/humorous)
2. Typical message style (short/long, question-heavy, directive, collaborative)
3. Writing quirks (capitalization, punctuation habits, emojis, abbreviations)
4. How to best communicate with this person (direct vs diplomatic, data-driven vs emotional)
5. Any cultural or contextual notes visible from the messages

Keep it concise - maximum 3 short paragraphs. Write it as a persona profile.

USER'S RECENT MESSAGES:
{transcript[:8000]}

PERSONA:"""

    # Use direct REST call since we need raw text (not structured JSON)
    url = f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}:generateContent"
    try:
        direct_res = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1024},
            },
            timeout=60,
        )
        direct_res.raise_for_status()
        body = direct_res.json()
        text = body["candidates"][0]["content"]["parts"][0]["text"]
        persona_text = text.strip()
        if persona_text:
            _write_persona(persona_text)
            return jsonify({"ok": True, "persona": persona_text})
    except Exception as e:
        return jsonify({"ok": False, "error": f"Gemini error: {str(e)}"}), 502

    return jsonify({"ok": False, "error": "Failed to generate persona"}), 502


# ═══════════════════════════════════════════════════════════════════
# Nudge Generation
# ═══════════════════════════════════════════════════════════════════

NUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "nudges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tone": {"type": "string", "enum": ["gentle", "passive", "aggressive"]},
                    "text": {"type": "string"},
                },
                "required": ["tone", "text"],
            },
            "minItems": 3,
            "maxItems": 3,
        },
    },
    "required": ["nudges"],
}


def _resolve_recipient(task: dict) -> str:
    """Pick a recipient JID for the nudge. Prefer the group JID (send back to group).
    If assignee is a recognizable JID (contains @), use that."""
    group_jid = task.get("group_jid", "")
    assignee = task.get("assignee", "")
    if assignee and "@" in assignee and not assignee.endswith("@lid"):
        return assignee
    if group_jid:
        return group_jid
    if assignee and "@" in assignee:
        return assignee
    return group_jid or ""


@bp.route("/nudge/generate", methods=["POST"])
def generate_nudges():
    data = request.get_json(silent=True) or {}
    task_id = data.get("task_id", "").strip()
    if not task_id:
        return jsonify({"ok": False, "error": "task_id is required"}), 400

    task = get_task(task_id)
    if not task:
        return jsonify({"ok": False, "error": "Task not found"}), 404

    persona = _read_persona()
    user_name = get_user_name()
    user_identity = get_user_identity()
    user_jid = user_identity.get("jid", "")

    # Resolve assignee to a human name
    assignee_raw = task.get("assignee") or ""
    assignee_name = resolve_contact(assignee_raw) if assignee_raw else "Unassigned"

    # Build context
    progress_log = task.get("progress_log") or []
    latest_progress = ""
    if progress_log:
        latest = progress_log[-1]
        latest_progress = f"{latest.get('date', '')}: {latest.get('summary', '')}"

    blockers = task.get("blockers") or []
    blockers_text = ""
    if blockers:
        blockers_text = "\n".join(
            f"- {b.get('blocker', b.get('summary', ''))}" for b in blockers[:3]
        )

    # ── Group conversation sample (captures the tone of THIS group) ──
    group_jid = task.get("group_jid", "")
    group_conv = ""
    if group_jid:
        try:
            recent = fetch_chat_messages(group_jid, limit=20)
            if recent:
                lines = []
                for m in recent[-20:]:
                    who = "Me" if m.get("is_from_me") else (m.get("sender") or "Someone")
                    body = (m.get("content") or "").strip().replace("\n", " ")
                    if body:
                        lines.append(f"{who}: {body[:200]}")
                group_conv = "\n".join(lines)
        except Exception as e:
            print(f"[nudge] failed to fetch group messages: {e}", flush=True)

    # ── Task-specific evidence (tagged messages) ──
    task_msgs = []
    try:
        task_msgs = get_task_messages(task_id)
    except Exception:
        pass
    evidence_text = ""
    if task_msgs:
        ev_lines = []
        for m in task_msgs[-8:]:
            who = m.get("sender_name") or "Someone"
            body = (m.get("message_content") or "").strip().replace("\n", " ")
            if body:
                ev_lines.append(f"{who}: {body[:200]}")
        evidence_text = "\n".join(ev_lines)

    # Build the "who am I" block — critical for first-person nudge generation
    identity_block = f"""YOU ARE: {user_name}
Your WhatsApp JID is: {user_jid}
You are the person sending these nudge messages. Write ALL nudge messages
in FIRST PERSON (using "I", "me", "my"). The task context may refer to
you by name ("{user_name}"). Replace any third-person references to yourself
with first-person pronouns when writing the nudge. Do NOT use your own name
in the nudge — use "I" instead.

"""

    persona_block = ""
    if persona:
        persona_block = f"""COMMUNICATION STYLE (YOUR PERSONA):
{persona}

"""

    group_tone_block = ""
    if group_conv:
        group_tone_block = f"""RECENT CONVERSATION IN THIS GROUP (mirror this group's tone, slang,
formality, and emoji usage when writing your nudge):
{group_conv}

"""

    evidence_block = ""
    if evidence_text:
        evidence_block = f"""TASK-SPECIFIC EVIDENCE (messages tagged as relevant to this task):
{evidence_text}

"""

    prompt = f"""{identity_block}{persona_block}{group_tone_block}{evidence_block}TASK:
- Title: {task.get('title', '')}
- Group: {task.get('group_name', '')}
- Assignee: {assignee_name}
- Status: {task.get('status', 'active')}
- Importance: {task.get('importance', 3)}/5
- Context: {task.get('context', '')}
{"- Latest progress: " + latest_progress if latest_progress else ""}
{"- Current blockers:\n" + blockers_text if blockers_text else ""}

Generate 3 WhatsApp nudge messages to send to the group/person. Write them as YOU ({user_name}) speaking in first person.

The 3 nudges must feel like 3 genuinely different people wrote them — different sentence structures, different openings, different asks, different lengths. Pull a concrete detail from the task or evidence above into EACH nudge so they don't read like templates with variables swapped.

TONES:
1. GENTLE — Warm, collaborative, low-pressure. Short. Treat it like a casual check-in between people who trust each other. 1-2 sentences.
2. PASSIVE-AGGRESSIVE — Indirectly surfaces the delay. Slightly pointed but plausibly polite. References the missed timing or stalled progress without naming it as a complaint. 2-3 sentences.
3. AGGRESSIVE — Direct, specific, urgency-driven. Cite the actual blocker or consequence from the task. State what you need and by when. 2-4 sentences.

RULES:
- Write IN FIRST PERSON using "I" and "me" — you ARE {user_name}
- Never write the literal string "{user_name}" — use "I"
- WhatsApp style, not email. Lowercase is fine. No subject lines. No "Hi team,".
- Match the group's actual conversational tone from the sample above (slang, emoji habits, brevity).
- Reference at least ONE concrete detail from the task/evidence in each nudge.
- Each nudge must be structurally DIFFERENT — do NOT start all three the same way or use the same closing.
- Do not include the tone label in the message text."""

    try:
        result = _call_gemini_v2(
            prompt,
            NUDGE_SCHEMA,
            temperature=0.85,
            model="gemini-3.1-flash-lite-preview",
        )
    except Exception as e:
        print(f"[nudge] gemini exception: {e}", flush=True)
        return jsonify({"ok": False, "error": f"Gemini error: {str(e)}"}), 502

    if not result:
        print("[nudge] gemini returned empty result", flush=True)
        return jsonify({"ok": False, "error": "Gemini returned no response"}), 502

    nudges = result.get("nudges", [])
    if not nudges:
        print(f"[nudge] no nudges in result: {result}", flush=True)
        return jsonify({"ok": False, "error": "No nudges generated"}), 502

    print(f"[nudge] generated {len(nudges)} nudges for task {task_id}", flush=True)
    return jsonify({"ok": True, "nudges": nudges, "recipient": _resolve_recipient(task)})