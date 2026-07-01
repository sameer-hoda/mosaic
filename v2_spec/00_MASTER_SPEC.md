# TaskDog v2 — Master Specification

## Overview

TaskDog v2 is a complete rewrite of the backend pipeline while retaining the v1 infrastructure (Go bridge, Flask backend, React frontend, SwiftUI shell). The v1 theme-based task model is replaced with a flat, group-keyed task model that supports incremental refresh and per-task deep-dive analysis.

**Top-level decisions (locked):**

| # | Decision | Rationale |
|---|---|---|
| D1 | Packaging | SwiftUI shell + WKWebView (existing `taskdog-app/DISTRIBUTION_PLAN.md`) |
| D2 | API key storage | macOS Keychain (shell-owned, backend reads from env) |
| D3 | Database | Fresh `taskdog_v2.db` — no migration from v1 |
| D4 | No themes table | Tasks are flat, keyed directly by group |
| D5 | Deep-dive trigger | On-demand only (user clicks "Deep Dive" per task) |
| D6 | Refresh trigger | Manual only (user clicks "Refresh" on dashboard) |
| D7 | Pipeline mode | Real-time synchronous, SSE streaming for stages 1-2 |
| D8 | Deep-dive input | Full group transcript sent to Gemini, no pre-filtering |
| D9 | Gemini model | `gemini-3.1-flash-lite-preview` for all stages (stage 3 may upgrade to pro) |
| D10 | Gemini transport | REST API (not gRPC) — same pattern as v1 `utils/gemini_client.py` |

---

## Onboarding (3 sequential gates)

Before any task features unlock, the app must pass three gates in order:

```
Gate A: GEMINI API KEY
  │ GET /api/health → {gemini_key_set: false}
  │ User enters key → POST /api/setup/validate-key
  │ Valid? → Keychain save → backend restart → proceed
  └─► Gate B: WHATSAPP BRIDGE
       │ GET /api/bridge/status → poll every 2s
       │ offline → pairing (QR) → connected
       │ QR code shown inline
       └─► Gate C: GROUP WHITELISTING
            │ POST /api/chats/classify → all chats with category+TLDR
            │ User ticks groups → POST /api/groups/whitelist
            └─► DASHBOARD UNLOCKED
```

---

## Backend Pipeline (4 stages)

```
┌────────────────────────────────────────────────────────────────┐
│  STAGE 1 — TASK DISCOVERY                                      │
│  ────────────────────────────────────────────────────────────  │
│  Trigger: First run per group (manual, from dashboard)         │
│  Input:   Group JID → 30-day transcript → Gemini Prompt 1      │
│  Output:  tasks + task_messages saved to DB                    │
│  Mode:    SSE streaming — per-group progress events            │
│  Endpoint: POST /api/pipeline/discover/stream                  │
├────────────────────────────────────────────────────────────────┤
│  STAGE 2 — TASK REFRESH                                        │
│  ────────────────────────────────────────────────────────────  │
│  Trigger: Manual "Refresh" button                              │
│  Input:   Known tasks (JSON) + new messages → Gemini Prompt 2  │
│  Output:  Status updates, progress notes, new tasks            │
│  Mode:    SSE streaming — per-task update events               │
│  Endpoint: POST /api/pipeline/refresh/stream                   │
├────────────────────────────────────────────────────────────────┤
│  STAGE 3 — TASK DEEP-DIVE                                      │
│  ────────────────────────────────────────────────────────────  │
│  Trigger: "Deep Dive" button on a task card (on-demand)        │
│  Input:   Task metadata + FULL group transcript → Prompt 3     │
│  Output:  wiki, people, progress_log, blockers, decisions      │
│  Mode:    Synchronous call (5-20s), loading spinner in UI      │
│  Endpoint: POST /api/pipeline/deep-dive                        │
├────────────────────────────────────────────────────────────────┤
│  STAGE 4 — DASHBOARD                                           │
│  ────────────────────────────────────────────────────────────  │
│  Trigger: Page load / after any pipeline stage completes       │
│  Input:   DB read (no Gemini call)                             │
│  Output:  Tasks grouped by importance, stats, summaries        │
│  Endpoint: GET /api/dashboard                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Task Data Model

A task in v2 has these fields:

| Field | Type | Source | Description |
|---|---|---|---|
| `id` | UUID | System | Primary key |
| `group_jid` | TEXT | System | Source WhatsApp group |
| `title` | TEXT | Stage 1 (Gemini) | Action-oriented title |
| `status` | ENUM | Stage 1/2 (Gemini) | `active`, `completed`, `archived` |
| `importance` | INT 1-5 | Stage 1/3 (Gemini) | AI-assessed importance to user. 5 = critical |
| `assignee` | TEXT | Stage 1 (Gemini) | Person responsible |
| `context` | TEXT | Stage 1 (Gemini) | What happened, who asked, what's the blocker |
| `wiki` | TEXT | Stage 3 (Gemini) | 3-5 paragraph knowledge page |
| `people` | JSON | Stage 1/3 (Gemini) | `[{name, role, jid}]` |
| `progress_log` | JSON | Stage 3 (Gemini) | `[{date, summary}]` day-by-day entries |
| `blockers` | JSON | Stage 3 (Gemini) | `[{description, raised_by, date}]` |
| `decisions` | JSON | Stage 3 (Gemini) | `[{description, made_by, date}]` |
| `last_deep_dived_at` | TIMESTAMP | System | When Stage 3 last ran for this task |
| `created_at` | TIMESTAMP | System | When first discovered |
| `updated_at` | TIMESTAMP | System | Last write |

---

## What stays unchanged from v1

These v1 components carry over without modification:

| Component | Path | Role in v2 |
|---|---|---|
| Go bridge binary | `whatsapp-mcp/whatsapp-bridge/wa-bridge` | WhatsApp connectivity, port 8080 |
| Flask app shell | `taskdog-backend/app.py` | Blueprint host, port 3001 |
| Gemini REST client | `taskdog-backend/utils/gemini_client.py` | `_call_gemini()` helper, reused by v2 |
| SQLite helpers | `taskdog-backend/models/database.py` | `fetch_top_chats`, `fetch_chat_messages`, `fetch_chat_messages_since` — reused |
| Chat classifier | `taskdog-backend/routes/tasks.py` (`/api/chats/classify`) | Used in onboarding Gate C |
| Bridge status | `taskdog-backend/routes/tasks.py` (`/api/bridge/status`) | Used in onboarding Gate B |
| Send nudge | `taskdog-backend/routes/tasks.py` (`/api/send`) | Same endpoint, points at v2 followup_history |
| SwiftUI shell | `taskdog-app/` | Unchanged architecture from DISTRIBUTION_PLAN.md |
| Frontend base | `taskdog-frontend/` | Vite + vanilla JS, adapted to new data model |

---

## v2 Files to create

```
v2_spec/                           ← THIS FOLDER (specs only)
├── 00_MASTER_SPEC.md              ← this file
├── 01_database_schema.md          ← full DDL + migration notes
├── 02_api_contracts.md            ← every endpoint, request/response
├── 03_gemini_prompts.md           ← 3 prompts in full detail
├── 04_implementation_plan.md      ← ordered stages, file-by-file
└── 05_runbook.md                  ← how to run and test

taskdog-backend/                   ← new v2 files (to be created)
├── models/
│   └── database_v2.py             ← new schema + CRUD for v2
├── routes/
│   ├── setup.py                   ← /api/health, /api/setup/validate-key
│   ├── groups.py                  ← /api/groups/whitelist
│   ├── pipeline.py                ← /discover, /refresh, /deep-dive
│   └── dashboard.py               ← GET /api/dashboard, /api/tasks/{id}
├── utils/
│   └── gemini_v2.py               ← discover_tasks(), refresh_tasks(), deep_dive_task()
└── tests/
    └── test_v2.py                 ← integration tests for all stages

taskdog-frontend/                  ← adapted components (to be updated)
└── src/
    └── components/
        ├── Dashboard.js           ← new: task list + stats (replaces Kanban.js)
        ├── DeepDive.js            ← new: wiki, people, timeline view
        └── ApiKey.js              ← from DISTRIBUTION_PLAN.md
```

---

## Key architectural differences from v1

| Concern | v1 | v2 |
|---|---|---|
| Task grouping | Themes contain tasks | Flat tasks keyed by group |
| Task statuses | `not started`, `pending`, `done` | `active`, `completed`, `archived` |
| Task enrichment | None | Wiki, people, progress_log, blockers, decisions |
| Extraction | One-shot per group | Discovery + incremental Refresh + on-demand Deep-Dive |
| Importance | None | 1-5 score, AI-assessed |
| Follow-up tracking | `nudge_history` table | Renamed to `followup_history` (identical schema) |
| Database file | `taskdog.db` | `taskdog_v2.db` (coexists with v1) |
| Gemini calls | 2 types (classify, extract) | 3 types (discover, refresh, deep-dive) + classify unchanged |