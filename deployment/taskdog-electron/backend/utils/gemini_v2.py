"""
TaskDog v2 — Gemini client for the 3-stage pipeline.

Stage 1: discover_tasks()   — first-time extraction from 30-day transcript
Stage 2: refresh_tasks()    — incremental update of known tasks
Stage 3: deep_dive_task()   — comprehensive single-task analysis

All stages use the REST API (same pattern as v1's gemini_client.py).
Model: gemini-3.1-flash-lite-preview (stage 3 may upgrade to pro).
"""
import os
import sys
import json
import time
import requests
from typing import Dict, List
from dotenv import load_dotenv

_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_dir, '..', '.env'))

_PROJECT_ROOT = os.path.abspath(os.path.join(_dir, '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from models.database import get_user_identity
except Exception:
    def get_user_identity():
        return {"jid": "", "push_name": "", "lid": ""}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
GEMINI_MODEL_PRO = "gemini-3.1-pro-preview"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _get_api_key():
    """Read API key at call time (not import time) so it picks up
    keys set mid-process via /api/setup/validate-key."""
    return os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY

if not _get_api_key():
    print("WARNING: GEMINI_API_KEY not found. v2 AI features will return empty results.")


# ---------------------------------------------------------------------------
# Core REST call (extended from v1's _call_gemini)
# ---------------------------------------------------------------------------

def _call_gemini_v2(prompt: str, response_schema: Dict = None,
                    temperature: float = 0.3, timeout: int = 120,
                    model: str = None) -> Dict:
    """Make a single Gemini API call with configurable temperature and timeout."""
    api_key = _get_api_key()
    if not api_key:
        return None

    used_model = model or GEMINI_MODEL
    url = f"{GEMINI_API_BASE}/models/{used_model}:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}

    generation_config = {
        "temperature": temperature,
        "topK": 40,
        "topP": 0.95,
        "maxOutputTokens": 8192,
    }
    if response_schema:
        generation_config["responseMimeType"] = "application/json"
        generation_config["responseSchema"] = response_schema

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }

    try:
        response = requests.post(url, headers=headers, params=params,
                                 json=payload, timeout=timeout)
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


def _build_transcript(messages: List[Dict]) -> str:
    """Format message list into a transcript string for Gemini.
    Messages marked is_from_me get [you] tag.
    """
    lines = []
    for msg in messages:
        ts = msg.get("timestamp", "")
        sender = msg.get("sender") or "Unknown"
        content = msg.get("content", "")
        if msg.get("is_from_me"):
            lines.append(f"[{ts}] {sender} [you]: {content}")
        else:
            lines.append(f"[{ts}] {sender}: {content}")
    return "\n".join(lines)


def _retry(fn, attempts=3, base_delay=1):
    """Retry a callable up to `attempts` times with exponential backoff."""
    last_error = None
    for attempt in range(attempts):
        if attempt > 0:
            time.sleep(base_delay * attempt)
        try:
            result = fn()
            if result:
                return result
            last_error = "no data returned"
        except Exception as e:
            last_error = str(e)
    return None


# ---------------------------------------------------------------------------
# Stage 1 — Task Discovery
# ---------------------------------------------------------------------------

DISCOVERY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "tasks": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "status": {"type": "STRING", "enum": ["active", "completed"]},
                    "importance": {"type": "INTEGER"},
                    "assignee": {"type": "STRING"},
                    "context": {"type": "STRING"},
                    "people": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "name": {"type": "STRING"},
                                "role": {"type": "STRING",
                                         "enum": ["assignee", "requestor",
                                                  "reviewer", "stakeholder"]}
                            },
                            "required": ["name", "role"]
                        }
                    },
                    "suggested_responses": {
                        "type": "OBJECT",
                        "properties": {
                            "concise": {"type": "STRING"},
                            "moderate": {"type": "STRING"},
                            "with_context": {"type": "STRING"}
                        },
                        "required": ["concise", "moderate", "with_context"]
                    },
                    "relevant_message_indices": {
                        "type": "ARRAY",
                        "items": {"type": "INTEGER"}
                    }
                },
                "required": ["title", "status", "importance", "assignee",
                             "context", "people", "suggested_responses"]
            }
        }
    },
    "required": ["tasks"]
}


def discover_tasks(group_name: str, messages: List[Dict]) -> Dict:
    """Stage 1: First-time extraction of ALL tasks from a 30-day transcript.

    Returns {"tasks": [...]} on success, {"tasks": [], "error": "..."} on failure.
    Each task dict has: title, status, importance, assignee, context, people,
    suggested_responses, relevant_message_indices.
    """
    fallback = {"tasks": []}
    if not _get_api_key():
        return fallback

    user = get_user_identity()
    user_name = user.get("push_name") or "the account owner"
    user_jid = user.get("jid") or ""

    transcript_text = _build_transcript(messages)

    prompt = f"""You are an AI project manager for TaskDog, a WhatsApp productivity tool.

Analyze the following WhatsApp chat transcript from the last 30 days for the group "{group_name}".

Account owner: the WhatsApp account this is being analyzed from belongs to {user_name} (jid: {user_jid}).
Lines in the transcript marked with "[you]" were sent by {user_name}.

Identify EVERY outstanding task, action item, commitment, open question, or deliverable discussed in this group. A task is anything where someone is expected to do something — a follow-up, a decision, a review, a report, a deliverable, a sign-off, etc.

For each task, determine:
1. title: Clear, action-oriented title (e.g., "Finalize Q3 budget approval", not just "Budget").
2. status: "active" if still open/unresolved, "completed" if clearly done from the transcript.
3. importance: 1-5 score where:
   - 5 = blocking {user_name}'s top priorities, urgent, high-stakes
   - 4 = important deliverable, directly impacts {user_name}'s work
   - 3 = normal task, should be tracked
   - 2 = minor task, low urgency
   - 1 = trivial, nice-to-have
4. assignee: The person responsible for completing this task.
5. context: A detailed narrative (2-4 sentences) covering:
   - Who asked for what and when.
   - What has happened so far.
   - What the current blocker or next step is.
6. people: List of everyone involved, with their role:
   - "assignee" = responsible for doing the task
   - "requestor" = asked for the task to be done
   - "reviewer" = needs to approve/sign off
   - "stakeholder" = informed/affected
   Do NOT include {user_name} in the people list unless they are the assignee.
7. suggested_responses: Three follow-up messages that {user_name} can send to the group:
   - "concise": Direct, brief check-in (1 sentence).
   - "moderate": Polite, professional check-in (2-3 sentences).
   - "with_context": Detailed follow-up referencing specifics from the chat (3-5 sentences).
8. relevant_message_indices: 0-based indices of messages from the transcript that are relevant to this task.

CRITICAL — Direction of messages:
The "suggested_responses" are messages {user_name} will TYPE and SEND to the group. They must be addressed to OTHER members (the assignee, stakeholders). NEVER write messages addressed to {user_name} or asking {user_name} for status updates.

Bad examples (DO NOT generate):
- "{user_name}, what's the latest on this?"
- "Hey {user_name}, can you give an update?"

Good examples:
- "<Assignee>, can you share an update on <task>?"
- "Hey team, any progress on <task> since <date>?"

Transcript:
{transcript_text}
"""

    def call():
        return _call_gemini_v2(prompt, response_schema=DISCOVERY_SCHEMA,
                                temperature=0.3, timeout=120)

    data = _retry(call, attempts=3, base_delay=1)
    if data and "tasks" in data:
        return data

    print(f"discover_tasks: Gemini failed after 3 attempts for '{group_name}'")
    return {"tasks": [], "error": "Gemini failed after 3 attempts"}


# ---------------------------------------------------------------------------
# Stage 2 — Task Refresh
# ---------------------------------------------------------------------------

REFRESH_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "task_updates": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "status_update": {"type": "STRING",
                                      "enum": ["still_active", "completed", "archived"]},
                    "progress_note": {"type": "STRING"},
                    "importance": {"type": "INTEGER"}
                },
                "required": ["id", "status_update", "progress_note", "importance"]
            }
        },
        "new_tasks": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "status": {"type": "STRING", "enum": ["active"]},
                    "importance": {"type": "INTEGER"},
                    "assignee": {"type": "STRING"},
                    "context": {"type": "STRING"},
                    "people": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "name": {"type": "STRING"},
                                "role": {"type": "STRING",
                                         "enum": ["assignee", "requestor",
                                                  "reviewer", "stakeholder"]}
                            },
                            "required": ["name", "role"]
                        }
                    },
                    "suggested_responses": {
                        "type": "OBJECT",
                        "properties": {
                            "concise": {"type": "STRING"},
                            "moderate": {"type": "STRING"},
                            "with_context": {"type": "STRING"}
                        },
                        "required": ["concise", "moderate", "with_context"]
                    }
                },
                "required": ["title", "status", "importance", "assignee",
                             "context", "people", "suggested_responses"]
            }
        }
    },
    "required": ["task_updates", "new_tasks"]
}


def refresh_tasks(group_name: str, current_tasks: List[Dict],
                  new_messages: List[Dict]) -> Dict:
    """Stage 2: Incremental update of known tasks.

    Returns {"task_updates": [...], "new_tasks": [...]} on success,
    {"task_updates": [], "new_tasks": [], "error": "..."} on failure.
    """
    fallback = {"task_updates": [], "new_tasks": []}
    if not _get_api_key():
        return fallback

    user = get_user_identity()
    user_name = user.get("push_name") or "the account owner"

    current_tasks_json = json.dumps(current_tasks, indent=2)
    new_messages_text = _build_transcript(new_messages)

    prompt = f"""You are updating the task list for WhatsApp group "{group_name}" for {user_name}.

Below is the CURRENT list of known tasks for this group. Each task has an `id`, `title`, `status`, `assignee`, and `importance`.

CURRENT TASKS:
{current_tasks_json}

Below are NEW MESSAGES that have appeared since the last refresh. Focus ONLY on what's changed.

NEW MESSAGES:
{new_messages_text}

Your job:
1. For EACH known task, determine if its status has changed based on the new messages:
   - "still_active": No resolution visible. Task continues.
   - "completed": The task has been clearly completed or resolved.
   - "archived": The task is no longer relevant or was mentioned in passing without any update. Nobody is actively working on it anymore.

2. For each task, provide a 1-line progress_note summarizing any new developments. If nothing new, use the string "No change".

3. Re-assess importance if the situation has changed. If unchanged, return the current value.

4. CRITICAL — Use the EXACT `id` field from the current task list for updates. Do not create new IDs for existing tasks.

5. Scan for NEW tasks that are NOT in the current list. If you find genuinely new action items, commitments, or deliverables, add them using the same structure as the current tasks (title, status, importance, assignee, context, people, suggested_responses). Assign them a new unique ID in the format "new-001", "new-002", etc.

6. When creating new tasks, follow the same rules as the original discovery:
   - suggested_responses must be addressed to OTHER people, never to {user_name}.
   - people list should not include {user_name} unless they are the assignee.

Rules:
- Do NOT mark a task as "completed" just because the chat moved on. Only mark it completed if there is explicit evidence (e.g., "done", "submitted", "approved", "launched").
- A task is "archived" if it was mentioned once and never followed up on, or if the context has shifted so the task is no longer needed.
- If a task was previously "active" and hasn't been mentioned in new messages, keep it as "still_active" — silence doesn't mean completion.
"""

    def call():
        return _call_gemini_v2(prompt, response_schema=REFRESH_SCHEMA,
                                temperature=0.2, timeout=90)

    data = _retry(call, attempts=3, base_delay=1)
    if data and ("task_updates" in data or "new_tasks" in data):
        return data

    print(f"refresh_tasks: Gemini failed after 3 attempts for '{group_name}'")
    return {"task_updates": [], "new_tasks": [], "error": "Gemini failed after 3 attempts"}


# ---------------------------------------------------------------------------
# Stage 3 — Task Deep-Dive
# ---------------------------------------------------------------------------

DEEP_DIVE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "wiki": {"type": "STRING"},
        "people": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "role": {"type": "STRING",
                             "enum": ["assignee", "requestor", "reviewer", "stakeholder"]},
                    "jid": {"type": "STRING"}
                },
                "required": ["name", "role"]
            }
        },
        "progress_log": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "date": {"type": "STRING"},
                    "summary": {"type": "STRING"}
                },
                "required": ["date", "summary"]
            }
        },
        "blockers": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "description": {"type": "STRING"},
                    "raised_by": {"type": "STRING"},
                    "date": {"type": "STRING"}
                },
                "required": ["description", "raised_by", "date"]
            }
        },
        "decisions": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "description": {"type": "STRING"},
                    "made_by": {"type": "STRING"},
                    "date": {"type": "STRING"}
                },
                "required": ["description", "made_by", "date"]
            }
        },
        "importance": {"type": "INTEGER"}
    },
    "required": ["wiki", "people", "progress_log", "blockers", "decisions", "importance"]
}


def deep_dive_task(task: Dict, full_messages: List[Dict]) -> Dict:
    """Stage 3: Comprehensive analysis of a single task.

    Produces wiki, people, progress_log, blockers, decisions, importance.
    Returns the dict on success, {"error": "..."} on failure.
    """
    fallback = {"error": "Gemini deep-dive failed"}
    if not _get_api_key():
        return fallback

    user = get_user_identity()
    user_name = user.get("push_name") or "the account owner"

    task_title = task.get("title", "")
    task_status = task.get("status", "")
    task_importance = task.get("importance", 3)
    task_assignee = task.get("assignee", "")
    task_context = task.get("context", "")
    group_name = task.get("group_name", "")

    full_transcript_text = _build_transcript(full_messages)

    prompt = f"""You are performing a deep-dive analysis on a single task for {user_name}, the owner of a WhatsApp account monitored by TaskDog.

TASK:
  Title:      {task_title}
  Status:     {task_status}
  Importance: {task_importance}/5
  Assignee:   {task_assignee}
  Context:    {task_context}

GROUP: {group_name}

Below is the FULL chat transcript from this group. It contains ALL messages (not just recent ones) so you can trace the complete history of this task.

TRANSCRIPT:
{full_transcript_text}

Your job: Build a comprehensive knowledge page for this task. Return the following:

1. wiki (string): A rich, well-structured knowledge page in Markdown format. Write 4-6 paragraphs covering:
   - **What this task is**: Why it exists, what the goal/deliverable is, and why it matters to {user_name}.
   - **Chronology**: A chronological narrative of every discussion, update, decision, and blocker related to this task. Mention specific dates and people from the transcript.
   - **Current status**: Where things stand right now. What's the immediate next step or blocker.
   - **Key quotes**: 2-3 direct quotes from the transcript (with sender names and approximate dates) that capture the essence of this task.

2. people (array): Everyone involved in this task, with their WhatsApp name and role:
   - "assignee" = responsible for doing the task
   - "requestor" = asked for the task to be done
   - "reviewer" = needs to approve/sign off
   - "stakeholder" = informed/affected
   Do NOT include {user_name} unless they are the assignee. If you can identify a JID from the transcript, include it.

3. progress_log (array): A day-by-day or week-by-week log of developments. For every date where this task was mentioned:
   - date: "YYYY-MM-DD"
   - summary: 1-sentence summary of what happened that day.
   Sort chronologically (oldest first).

4. blockers (array): Any blockers, dependencies, or obstacles mentioned:
   - description: What's blocking progress.
   - raised_by: Who mentioned the blocker.
   - date: When it was raised (YYYY-MM-DD).

5. decisions (array): Key decisions made about this task:
   - description: What was decided.
   - made_by: Who made the decision.
   - date: When (YYYY-MM-DD).

6. importance (integer): Re-assess the importance 1-5 based on the full context. Use the same scale:
   - 5 = critical, blocking {user_name}'s top priorities
   - 4 = important deliverable
   - 3 = normal task
   - 2 = minor
   - 1 = trivial

IMPORTANT: Only extract information that is PRESENT in the transcript. Do not fabricate or assume events, dates, or people that are not mentioned. If something is unclear or not mentioned, omit it rather than guessing.

Use ## Headings and bullet points in the wiki for readability. The wiki will be rendered as Markdown in the app.
"""

    def call():
        return _call_gemini_v2(prompt, response_schema=DEEP_DIVE_SCHEMA,
                                temperature=0.4, timeout=120)

    data = _retry(call, attempts=3, base_delay=1)
    if data and "wiki" in data:
        return data

    print(f"deep_dive_task: Gemini failed after 3 attempts for task '{task_title}'")
    return {"error": "Gemini deep-dive failed after 3 attempts"}
