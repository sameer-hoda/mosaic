"""
Gemini REST API client wrapper for TaskDog classification and task extraction.
Uses direct HTTPS calls to the Gemini REST API to avoid binary gRPC dependency.
"""
import os
import json
import sys
import requests
from typing import Dict, List
from dotenv import load_dotenv

_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_dir, '..', '.env'))

# Make the project's models package importable so we can read the connected
# WhatsApp account owner (push_name + JID) for use in the extraction prompt.
_PROJECT_ROOT = os.path.abspath(os.path.join(_dir, '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
try:
    from models.database import get_user_identity  # noqa: E402
except Exception:  # pragma: no cover - database not available in some envs
    def get_user_identity():
        return {"jid": "", "push_name": "", "lid": ""}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment. AI features will be mock-only.")


def _get_api_key_v1():
    """Read API key at call time so it picks up keys set mid-process."""
    return os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY


def _call_gemini(prompt: str, response_schema: Dict = None, timeout: int = 60) -> Dict:
    """Make a single Gemini API call using the REST generateContent endpoint."""
    api_key = _get_api_key_v1()
    if not api_key:
        return None

    url = f"{GEMINI_API_BASE}/models/{GEMINI_MODEL}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}

    generation_config = {
        "temperature": 0.3,
        "topK": 40,
        "topP": 0.95,
        "maxOutputTokens": 4096,
    }
    if response_schema:
        generation_config["responseMimeType"] = "application/json"
        generation_config["responseSchema"] = response_schema

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }

    try:
        response = requests.post(url, headers=headers, params=params, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        if "candidates" not in result or not result["candidates"]:
            return None
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except requests.exceptions.Timeout:
        print(f"Gemini API timeout (>{timeout}s)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Gemini API request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Gemini response not valid JSON: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Unexpected Gemini response shape: {e}")
        return None


def classify_chat(chat_name: str, messages: List[Dict]) -> Dict:
    """
    Classify a chat into Work or Personal and generate a one-line TL;DR.
    """
    fallback = {"category": "Personal", "tldr": "Chat with no recent updates."}
    if not _get_api_key_v1():
        return fallback

    history_lines = [f"{msg['sender']}: {msg['content']}" for msg in messages]
    history_text = "\n".join(history_lines)

    prompt = f"""You are an AI classifier for TaskDog.
Analyze the following WhatsApp message history for the chat named "{chat_name}".
Determine which category the chat belongs to:
- "Work": Professional, business, projects, tasks, office, scheduling, or work-related coordination.
- "Personal": Family, friends, personal relationships, casual chats, and any chat that does not clearly fit Work.

Also, generate a one-line TL;DR summary (maximum 15 words) of the most recent discussion in the chat.

Message History:
{history_text}
"""

    schema = {
        "type": "OBJECT",
        "properties": {
            "category": {"type": "STRING", "enum": ["Work", "Personal"]},
            "tldr": {"type": "STRING"},
        },
        "required": ["category", "tldr"],
    }

    data = _call_gemini(prompt, response_schema=schema)
    if not data:
        return fallback
    if data.get("category") not in ["Work", "Personal"]:
        data["category"] = "Personal"
    if not data.get("tldr"):
        data["tldr"] = "No summary available."
    return data


def extract_tasks(chat_name: str, messages: List[Dict]) -> Dict:
    """
    Extract themes and tasks with follow-up responses from a 30-day chat transcript.

    Retries the Gemini call up to 2 additional times (3 total attempts) with
    exponential backoff (1s, 2s) on transient failures. Returns a dict with a
    `themes` array on success, or `{"themes": [], "error": "..."}` on failure
    so callers can surface the failure to the user.
    """
    fallback = {"themes": []}
    if not _get_api_key_v1():
        return fallback

    user = get_user_identity()
    user_name = user.get("push_name") or "the account owner"
    user_jid = user.get("jid") or ""

    transcript_lines = []
    for msg in messages:
        ts = msg.get("timestamp", "")
        sender = msg.get("sender") or "Unknown"
        if msg.get("is_from_me"):
            # The user is the WhatsApp account owner — mark their own lines
            # with a [you] tag so Gemini knows which side they're on.
            transcript_lines.append(f"[{ts}] {sender} [you]: {msg['content']}")
        else:
            transcript_lines.append(f"[{ts}] {sender}: {msg['content']}")
    transcript_text = "\n".join(transcript_lines)

    prompt = f"""You are an AI project manager for TaskDog.
Analyze the following WhatsApp chat transcript from the last 30 days for the group "{chat_name}".

Account owner: the WhatsApp account this is being analyzed from belongs to {user_name} (jid: {user_jid}).
Lines in the transcript marked with "[you]" were sent by {user_name} — the other people in the chat are the recipients of any messages we draft.

Identify the key themes/topics discussed and extract outstanding tasks/action items under each theme.
For each task, determine:
1. Title: Clear, action-oriented task title.
2. Status: Exactly one of "not started", "pending", "done".
3. Context: Contextual narrative detailing who asked for it, what was requested, and any blocker.
4. Assignee: The person responsible for the task.
5. Suggested Responses: Three versions of a follow-up message that {user_name} will SEND FROM THEIR OWN ACCOUNT back to the group:
   - "concise": Direct, brief check-in.
   - "moderate": Polite, professional check-in.
   - "with_context": Detailed follow-up referencing specific details and context from the chat.

CRITICAL — Direction of the message:
The "suggested_responses" are messages that {user_name} will type and send to the rest of the group. They must be addressed to OTHER members of the group (the assignee, or whoever is unblocked / has the update), never to {user_name} themselves.

DO NOT write suggestions that ask {user_name} what they are doing, what their status is, or what they plan to do next. {user_name} is the SENDER, not the recipient.

Bad examples (do NOT generate):
- "{user_name}, what's the latest on this?"
- "Hey {user_name}, can you give an update?"
- "What are you doing about it, {user_name}?"

Good examples:
- "<Assignee name>, can you share an update on this?"
- "Hey team, has anyone got eyes on the <theme name> thread?"

Transcript:
{transcript_text}
"""

    schema = {
        "type": "OBJECT",
        "properties": {
            "themes": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "name": {"type": "STRING"},
                        "description": {"type": "STRING"},
                        "tasks": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "title": {"type": "STRING"},
                                    "status": {
                                        "type": "STRING",
                                        "enum": ["not started", "pending", "done"],
                                    },
                                    "context": {"type": "STRING"},
                                    "assignee": {"type": "STRING"},
                                    "suggested_responses": {
                                        "type": "OBJECT",
                                        "properties": {
                                            "concise": {"type": "STRING"},
                                            "moderate": {"type": "STRING"},
                                            "with_context": {"type": "STRING"},
                                        },
                                        "required": ["concise", "moderate", "with_context"],
                                    },
                                },
                                "required": [
                                    "title",
                                    "status",
                                    "context",
                                    "assignee",
                                    "suggested_responses",
                                ],
                            },
                        },
                    },
                    "required": ["name", "description", "tasks"],
                },
            }
        },
        "required": ["themes"],
    }

    import time
    last_error = None
    for attempt in range(3):
        if attempt > 0:
            time.sleep(attempt)  # 1s, then 2s
        # Use a longer timeout for extraction — 30 days of messages
        # across hundreds of chats can produce a large payload.
        data = _call_gemini(prompt, response_schema=schema, timeout=120)
        if data and "themes" in data:
            return data
        last_error = "no data returned"
    print(f"extract_tasks: Gemini failed after 3 attempts for '{chat_name}'")
    return {"themes": [], "error": last_error or "Gemini failed after 3 attempts"}
