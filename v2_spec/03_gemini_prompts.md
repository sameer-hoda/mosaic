# TaskDog v2 — Gemini Prompts

All three pipeline stages use Google Gemini via the REST API (same `_call_gemini()` pattern from v1's `utils/gemini_client.py`). Each prompt has a strict JSON response schema enforced by Gemini's `responseSchema` parameter.

**Model:** `gemini-3.1-flash-lite-preview` for stages 1 and 2. Stage 3 may use `gemini-3.1-pro-preview` for better synthesis quality — TBD based on testing.

**Transport:** REST API — `POST https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent` with `responseMimeType: application/json`.

---

## Shared Context (injected into all prompts)

Every prompt receives:
- **`user_name`**: The WhatsApp account owner's push_name (e.g., "Sameer"), fetched from `whatsmeow_device`.
- **`user_jid`**: The account's JID.
- **`group_name`**: The WhatsApp group display name.
- **Direction instruction**: Messages marked `[you]` were sent by the user. All follow-up suggestions must be addressed to OTHER people, never to the user themselves.

---

## Prompt 1 — Task Discovery (Stage 1)

**Purpose:** First-time extraction of ALL tasks from a 30-day transcript. No prior task list exists.

**Function:** `discover_tasks(group_name: str, messages: List[Dict]) -> Dict`

**Temperature:** 0.3
**Timeout:** 120s (30 days of messages can be large)
**Retries:** 3 attempts with 1s/2s backoff

### System prompt

```
You are an AI project manager for TaskDog, a WhatsApp productivity tool.

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

CRITICAL — Direction of messages:
The "suggested_responses" are messages {user_name} will TYPE and SEND to the group. They must be addressed to OTHER members (the assignee, stakeholders). NEVER write messages addressed to {user_name} or asking {user_name} for status updates.

Bad examples (DO NOT generate):
- "{user_name}, what's the latest on this?"
- "Hey {user_name}, can you give an update?"
- "What are you doing about it, {user_name}?"

Good examples:
- "<Assignee>, can you share an update on <task>?"
- "Hey team, any progress on <task> since <date>?"
- "Hi <Assignee>, following up on <task> from <date>. The ask was <specific>. Could you confirm?"

Transcript:
{transcript_text}
```

### Response schema

```json
{
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
                "role": {"type": "STRING", "enum": ["assignee", "requestor", "reviewer", "stakeholder"]}
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
            "items": {"type": "INTEGER"},
            "description": "0-based indices of messages that are relevant to this task"
          }
        },
        "required": ["title", "status", "importance", "assignee", "context", "people", "suggested_responses"]
      }
    }
  },
  "required": ["tasks"]
}
```

The `relevant_message_indices` field lets Gemini tag which transcript messages are relevant to each task. These are stored in the `task_messages` table.

---

## Prompt 2 — Task Refresh (Stage 2)

**Purpose:** Incremental update. Receives the current task list + new messages since last refresh. Updates statuses, adds progress notes, detects new tasks.

**Function:** `refresh_tasks(group_name: str, current_tasks: List[Dict], new_messages: List[Dict]) -> Dict`

**Temperature:** 0.2 (lower — must be consistent with prior runs)
**Timeout:** 90s
**Retries:** 3 attempts with 1s/2s backoff

### System prompt

```
You are updating the task list for WhatsApp group "{group_name}" for {user_name}.

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
```

### Response schema

```json
{
  "type": "OBJECT",
  "properties": {
    "task_updates": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "id": {"type": "STRING"},
          "status_update": {"type": "STRING", "enum": ["still_active", "completed", "archived"]},
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
                "role": {"type": "STRING", "enum": ["assignee", "requestor", "reviewer", "stakeholder"]}
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
        "required": ["title", "status", "importance", "assignee", "context", "people", "suggested_responses"]
      }
    }
  },
  "required": ["task_updates", "new_tasks"]
}
```

**Note on IDs:** Gemini generates `new-001` style IDs for new tasks. The backend replaces these with real UUIDs before insertion.

---

## Prompt 3 — Task Deep-Dive (Stage 3)

**Purpose:** Comprehensive analysis of a single task. Produces the wiki, people list, progress timeline, blockers, and decisions.

**Function:** `deep_dive_task(task: Dict, full_messages: List[Dict]) -> Dict`

**Temperature:** 0.4 (slightly higher for better narrative synthesis)
**Timeout:** 120s (full transcript can be large)
**Retries:** 3 attempts with 1s/2s backoff

### System prompt

```
You are performing a deep-dive analysis on a single task for {user_name}, the owner of a WhatsApp account monitored by TaskDog.

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

Use `## Headings` and bullet points in the wiki for readability. The wiki will be rendered as Markdown in the app.
```

### Response schema

```json
{
  "type": "OBJECT",
  "properties": {
    "wiki": {"type": "STRING"},
    "people": {
      "type": "ARRAY",
      "items": {
        "type": "OBJECT",
        "properties": {
          "name": {"type": "STRING"},
          "role": {"type": "STRING", "enum": ["assignee", "requestor", "reviewer", "stakeholder"]},
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
```

---

## Prompt testing strategy

Before building the full pipeline, test each prompt in isolation:

1. **Discovery test**: Pick a real WhatsApp group with 30 days of messages. Run `discover_tasks()`. Manually review the output. Are all tasks found? Are importance scores reasonable? Are suggested responses correctly addressed?

2. **Refresh test**: Take the discovery output from step 1. Add 2-3 days of new messages. Run `refresh_tasks()`. Verify: existing tasks correctly updated? New tasks found? No phantom completions?

3. **Deep-dive test**: Pick one task from step 1. Run `deep_dive_task()` with the full transcript. Verify: wiki is coherent Markdown? Progress log covers all mentions? Blockers/decisions extracted correctly?

Tune prompts (temperature, wording, examples) based on test results before wiring into the Flask routes.

---

## Cost estimate

| Stage | Avg tokens (input) | Avg tokens (output) | Calls per group | Cost per call (flash-lite) |
|---|---|---|---|---|
| Discovery | ~8,000 tokens | ~2,000 tokens | 1 per group | ~$0.0005 |
| Refresh | ~4,000 tokens | ~1,500 tokens | 1 per group | ~$0.0003 |
| Deep-dive | ~15,000 tokens | ~3,000 tokens | 1 per task | ~$0.001 |

**Estimated monthly cost** (10 groups, 1 discovery, 4 refreshes, 5 deep-dives):
- Discovery: 10 × $0.0005 = $0.005
- Refresh: 10 × 4 × $0.0003 = $0.012
- Deep-dive: 5 × $0.001 = $0.005
- **Total: ~$0.02/month**

`gemini-3.1-flash-lite-preview` is extremely cost-efficient. Even with heavy usage, costs should stay under $1/month. If Stage 3 upgrades to `gemini-3.1-pro-preview`, deep-dive costs 5-10x but still negligible at this scale.