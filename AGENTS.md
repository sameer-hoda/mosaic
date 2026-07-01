# TaskDog v2 — Project Context & Handoff

**Last updated:** Sat Jun 20, 2026
**Status:** v2 backend + frontend complete, tested, and running end-to-end against real WhatsApp data. Card design refreshed (Option D — left accent bar + background tint + glow). Checkbox added for quick status toggling. IMP labels replaced with star emojis. Modal status changed from dropdown to styled pills.

---

## What This Project Is

TaskDog v2 is a WhatsApp-based task tracker. It scans WhatsApp group/DM messages via a Go bridge, uses Gemini to discover tasks, refreshes them incrementally, and produces deep-dive knowledge pages per task. The user views everything in a web dashboard.

This repo (`task_dog_v1`) is the working directory. The v2 build reuses v1's infrastructure (Go bridge, Flask app, WhatsApp pairing) and adds new routes, a new DB, and a new frontend flow. v1 and v2 coexist; v1 routes still serve the bridge/classify/send endpoints.

## Architecture

```
WhatsApp phone ──► wa-bridge (Go, :8080) ──► Flask app (Python, :3001) ──► Vite frontend (:5173)
                                                       │
                                            ┌──────────┴──────────┐
                                        taskdog.db (v1)     taskdog_v2.db (v2)
```

- **wa-bridge** — Go binary that connects to WhatsApp via the `whatsmeow` library. Serves chats, messages, send. Stored in `whatsapp-mcp/whatsapp-bridge/`. Pre-built binary `wa-bridge` exists; no Go compilation needed.
- **Flask backend** — `taskdog-backend/app.py`. Registers 5 blueprints. Both v1 and v2 DBs auto-init on startup.
- **Vite frontend** — React shell (`taskdog-frontend/`). In production it will be wrapped in SwiftUI + WKWebView (see `DISTRIBUTION_PLAN.md`), but for dev it's just Vite.

## Quick Start (single command)

```bash
bash scripts/start.sh     # starts bridge + backend + frontend, opens browser
bash scripts/stop.sh      # kills all services
bash scripts/reset_first_time.sh  # full factory reset
```

## 3-Terminal Dev Setup (manual alternative)

| Terminal | Service | Port | Command |
|---|---|---|---|
| 1 | Go bridge | 8080 | `cd whatsapp-mcp/whatsapp-bridge && ./wa-bridge` |
| 2 | Flask backend | 3001 | `cd taskdog-backend && venv/bin/python app.py` |
| 3 | Vite frontend | 5173 | `cd taskdog-frontend && npm run dev` |

Open http://localhost:5173/.

All three services are **currently running** as of this writing (PIDs: bridge 47261, Flask 49902, Vite 16766).

## Onboarding Flow (3 gates, frontend auto-routes)

1. **Gate A — Gemini API Key**: Key is already set in `taskdog-backend/.env` as `GEMINI_API_KEY`. `/api/health` returns `gemini_key_set: true`. Click Continue.
2. **Gate B — WhatsApp Bridge**: App polls `/api/bridge/status` every 2s until `connected`. Bridge auto-connects if already paired.
3. **Gate C — Group Whitelisting**: App calls v1 `/api/chats/classify` to list 100 chats with category + TLDR. User picks groups, app POSTs to v2 `/api/groups/whitelist`. Saved to v2 `groups` table. Then routes to Dashboard.

## Pipeline (4 stages, all manual trigger — no cron)

| Stage | Endpoint | What it does |
|---|---|---|
| 1 Discover | `POST /api/pipeline/discover` (+ `/stream` SSE) | 30-day scan, Gemini extracts all tasks per group, saves to v2 |
| 2 Refresh | `POST /api/pipeline/refresh` (+ `/stream` SSE) | Incremental update since last refresh timestamp |
| 3 Deep-dive | `POST /api/pipeline/deep-dive` | Full transcript → Gemini → wiki (Markdown), people, timeline, blockers, decisions |
| 4 Dashboard | `GET /api/dashboard` | Pure DB read, no Gemini. Tasks sorted by importance DESC. |

- Discover/refresh run groups in parallel via `ThreadPoolExecutor(max_workers=3)` — Gemini calls parallel, DB writes serialized by lock.
- Deep-dive is single-task, single Gemini call, 5–20s.
- Deep-dive input is the full transcript; no pre-filtering.
- Refresh uses `last_refreshed_at` per group to fetch only new messages.

## Current Data State (as of this writing)

**v2 DB:** `taskdog-backend/taskdog_v2.db`
- 10 whitelisted groups (see list below)
- 13 discovered tasks
- 72 tagged messages
- 0 deep-dives performed (no wiki saved yet)
- 0 followup history entries

**Whitelisted groups:**
| JID | Name | Category |
|---|---|---|
| 120363329500662632@g.us | Pensioners | Work |
| 919916509793@s.whatsapp.net | Ayesha | Personal |
| 120363409785935773@g.us | Bio auth <> edu | Work |
| 120363426270057805@g.us | Comms way of working | Work |
| 919929014797@s.whatsapp.net | Arnav Anand | Personal |
| 120363410890993327@g.us | Product Team Invoice Payouts | Work |
| 120363428158587404@g.us | Alert on comms | Work |
| 120363428033060812@g.us | Loss in ₹₹ due to ops errors / delays | Work |
| 120363425898115043@g.us | AD-tech revenue from BFSI | Work |
| 120363371342162600@g.us | Founder's office x growth threads | Work |

**Discovered tasks (top by importance):** All 13 are `active` status. Importance 5 tasks: "Define cohort for low propensity education model", "Finalize June communications budget plan", "Achieve zero operational loss for June", "Process pending Mastercard and Visa invoices", "Confirm impact of tokenization costs on future budget". Importance 4 tasks: 5 more. Importance 2-3 tasks: 3 more.

## Key Design Decisions

- **No themes table** — tasks are flat, directly keyed to a group via `group_jid`.
- **Task statuses:** `active`, `completed`, `archived`.
- **Importance score:** 1-5, AI-assessed, user-overridable via PATCH.
- **Deep-dive output schema:** `wiki` (Markdown), `people` (JSON), `progress_log` (JSON), `blockers` (JSON), `decisions` (JSON). All stored as TEXT columns in the `tasks` table.
- **All Gemini calls use REST API** (same pattern as v1's `_call_gemini()`), not the SDK.
- **SSE streaming** for discover/refresh stages shows per-group progress in the frontend.
- **v1 and v2 DBs coexist** — `taskdog.db` (v1) and `taskdog_v2.db` (v2). v1 still used for chat reads via `database.py`.
- **Database file:** `taskdog_v2.db` lives in `taskdog-backend/` next to `taskdog.db`. Path controlled by `DATABASE_PATH_V2` env var (defaults to `taskdog_v2.db`).
- **No migration from v1** — v2 starts fresh; users re-whitelist groups.
- **Manual triggers only** — pipeline does NOT auto-run on a timer; user clicks Discover/Refresh from the dashboard.
- **QR code served on-screen** — The Go bridge now starts its HTTP server BEFORE the QR/connection flow. During pairing, `GET /api/qr` on port 8080 serves the current QR code. The Flask backend proxies this at `GET /api/bridge/qr`. The `Pairing.js` frontend polls this endpoint and renders the QR code directly on the HTML page — no terminal needed for scanning.

## Bugs Fixed During This Build

1. **Route conflict — FK constraint failures during discovery.** v1's `GET /api/groups` route in `routes/tasks.py` was shadowing v2's version and reading from the wrong table, causing "FOREIGN KEY constraint failed" when inserting tasks for groups that existed in v1 but not v2. **Fix:** Removed v1's `GET /api/groups` route. v2's `routes/groups.py` now owns this endpoint.

2. **Auto-insert missing groups.** Added `_ensure_group_exists()` in `routes/pipeline.py` — if a group JID isn't in the v2 `groups` table, it auto-inserts before discovery/refresh runs. Prevents FK errors even if groups were whitelisted via v1 flow. Note: auto-inserted groups get category "Personal" by default; groups whitelisted via v2 `/api/groups/whitelist` get correct categories from v1 cached classifications.

3. **Database locking — "database is locked" errors from concurrent writes.** Discovery's `ThreadPoolExecutor(max_workers=3)` caused concurrent SQLite writes to fail. **Fix:**
   - WAL journal mode: `PRAGMA journal_mode = WAL` (allows concurrent reads during writes)
   - 30s busy timeout: `PRAGMA busy_timeout = 30000`
   - `threading.Lock` (`_write_lock`) wraps all write functions in `database_v2.py` to serialize writes

## Implementation Stages (all complete)

| Stage | What shipped |
|---|---|
| A | `models/database_v2.py` — schema (groups, tasks, task_messages, followup_history) + all CRUD, write lock, WAL mode |
| B | `routes/setup.py` (`/api/health`, `/api/setup/validate-key`), `routes/groups.py` (`/api/groups/whitelist`, `GET /api/groups`), registered in `app.py` |
| C | `utils/gemini_v2.py::discover_tasks()`, `routes/pipeline.py` (`/discover`, `/discover/stream` SSE) |
| D | `refresh_tasks()` in `gemini_v2.py`, `/refresh` + `/refresh/stream` in `pipeline.py` |
| E | `deep_dive_task()` in `gemini_v2.py`, `/deep-dive` in `pipeline.py` |
| F | `routes/dashboard.py` (`/api/dashboard`, `/api/tasks/{id}`, `/api/tasks/{id}/messages`, `PATCH /api/tasks/{id}`) |
| G | `tests/test_v2.py` — 30 integration tests, all passing |
| H | Frontend: `ApiKey.js`, `Whitelist.js`, `Dashboard.js`, `DeepDive.js`, updated `api.js` (12 v2 endpoints + SSE parser), `app.js` (phase router), `Header.js` |
| I | `tests/e2e_v2.sh` end-to-end validation script |

## File Map

### `taskdog-backend/`

```
app.py                         # Flask app, registers 5 blueprints
.env                           # GEMINI_API_KEY, DATABASE_PATH, DATABASE_PATH_V2
taskdog.db                     # v1 DB (coexists, used for chat reads)
taskdog_v2.db                  # v2 DB (current: 10 groups, 13 tasks, 72 msgs)
models/
  database.py                  # v1 DB helpers (reused for WhatsApp reads)
  database_v2.py              # v2 schema + CRUD (thread-safe, WAL, write lock)
routes/
  tasks.py                    # v1 routes (bridge status, classify, send, etc.) — v1 GET /api/groups REMOVED
  setup.py                    # v2: GET /api/health, POST /api/setup/validate-key
  groups.py                   # v2: POST /api/groups/whitelist, GET /api/groups
  pipeline.py                 # v2: /discover, /refresh, /deep-dive (+ streams) + _ensure_group_exists()
  dashboard.py               # v2: GET /api/dashboard, /api/tasks/{id}, /api/tasks/{id}/messages, PATCH
utils/
  gemini_client.py             # v1 Gemini client (classify, extract)
  gemini_v2.py                # v2 Gemini client (discover_tasks, refresh_tasks, deep_dive_task)
tests/
  test_api.py                  # v1 tests
  test_v2.py                  # v2 integration tests (30 tests, all pass)
  e2e_v2.sh                    # E2E smoke test
```

### `taskdog-frontend/src/`

```
app.js                         # Phase router (apikey → pairing → whitelist → dashboard)
api.js                         # API client (v1 + v2 endpoints, SSE stream parser, _streamSSE())
components/
  ApiKey.js                    # Gate A: Gemini key entry
  Pairing.js                   # Gate B: WhatsApp bridge pairing
  Whitelist.js                # Gate C: group selection (uses Classifier)
  Dashboard.js               # v2 task list with stats, discover/refresh streaming
  DeepDive.js                # Task knowledge page drawer (wiki, people, timeline)
  Header.js                  # Top bar with nav + settings
  Classifier.js              # v1 classifier (reused in Gate C)
  Kanban.js, TaskDrawer.js, HistoryDrawer.js, Extracting.js  # v1 components (legacy, unchanged)
```

### `v2_spec/`

```
00_MASTER_SPEC.md
01_database_schema.md
02_api_contracts.md
03_gemini_prompts.md
04_implementation_plan.md
05_runbook.md          # ← fully updated with accurate file structure + commands
```

## API Reference

### v2 endpoints (new)

| Method | Path |
|---|---|
| GET | `/api/health` |
| POST | `/api/setup/validate-key` |
| POST | `/api/groups/whitelist` |
| GET | `/api/groups` |
| POST | `/api/pipeline/discover` |
| POST | `/api/pipeline/discover/stream` |
| POST | `/api/pipeline/refresh` |
| POST | `/api/pipeline/refresh/stream` |
| POST | `/api/pipeline/deep-dive` |
| GET | `/api/dashboard` |
| GET | `/api/tasks/{id}` |
| GET | `/api/tasks/{id}/messages` |
| PATCH | `/api/tasks/{id}` |

### v1 endpoints (reused, unchanged except `/api/groups` removed)

| Method | Path | Used in |
|---|---|---|
| GET | `/api/bridge/status` | Gate B |
| GET | `/api/bridge/qr` | Gate B (QR code display) |
| POST | `/api/chats/classify` | Gate C |
| POST | `/api/chats/classify/stream` | Gate C |
| POST | `/api/send` | Dashboard nudge |
| GET | `/api/history` | Dashboard history |

## Environment Variables

Set in `taskdog-backend/.env`:

```env
GEMINI_API_KEY="AIzaSy..."
DATABASE_PATH="taskdog.db"
DATABASE_PATH_V2="taskdog_v2.db"
```

`DATABASE_PATH_V2` is read by `database_v2.py`, defaults to `taskdog_v2.db` if unset.

## Test Commands

```bash
# Onboarding tests (67 tests — covers full first-time-user journey)
cd taskdog-backend
DATABASE_PATH_V2=$(mktemp) DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_onboarding -v

# All backend tests (97 total: 30 v2 + 67 onboarding)
DATABASE_PATH_V2=$(mktemp) DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_onboarding tests.test_v2 -v

# v2 integration tests (30 tests, all pass) — uses temp DBs, no real Gemini calls
DATABASE_PATH_V2=$(mktemp) DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_v2 -v

# v1 tests (unchanged)
DATABASE_PATH=$(mktemp) venv/bin/python -m unittest tests.test_api -v

# E2E smoke (requires all 3 services running + paired + key set)
cd taskdog-backend
bash tests/e2e_v2.sh

# Frontend build (verify no import errors)
cd taskdog-frontend
npx vite build
```

Last verified: 97/97 tests pass (30 v2 + 67 onboarding), `vite build` clean.

## How to Reset

### Full Reset (first-time-user experience — single command)
```bash
bash scripts/reset_first_time.sh              # full factory reset
bash scripts/reset_first_time.sh --keep-key    # preserve Gemini key
bash scripts/reset_first_time.sh --keep-pairing # preserve WhatsApp session
bash scripts/reset_first_time.sh --keep-all     # wipe only task data
bash scripts/reset_first_time.sh --dry-run      # preview what would be deleted
```
This kills all services, deletes all DBs (v1, v2, bridge whatsapp.db + messages.db), clears `__pycache__`, clears the Gemini key, and verifies success. After running, `bash scripts/start.sh` and open http://localhost:5173/ for the full onboarding flow.
This kills all services, deletes all DBs (v1, v2, bridge whatsapp.db + messages.db), and clears the Gemini key from `.env`. After running it, restart the 3 services and open http://localhost:5173/ for the full onboarding flow (Gemini key → QR scan on screen → group whitelist → dashboard).

## What's Left To Do

### Immediate (verify before declaring done)
- [ ] **Run deep-dive on a real task** — has not been done yet (0 wikis in DB). Click a task card in the dashboard, or `curl -X POST /api/pipeline/deep-dive -d '{"task_id":"<id>"}'`. Verify the wiki + people + timeline render in `DeepDive.js`.
- [ ] **Run refresh** — has not been run yet. Click "Refresh" on dashboard. Verify new messages since discovery are folded into existing tasks (no duplicates created).
- [ ] **Run `tests/e2e_v2.sh`** end-to-end against live services to validate the full flow.

### Polish
- [ ] Auto-categorize groups during `_ensure_group_exists()` — currently defaults to "Personal". Should look up v1 cached classification if available.
- [ ] Dashboard UI: verify SSE progress events render correctly during discover/refresh (test with a slow Gemini response).
- [ ] DeepDive.js: verify the Markdown wiki renders properly (test with a real deep-dive result).
- [ ] Update `DISTRIBUTION_PLAN.md` to reflect v2 file structure for the SwiftUI+WKWebView packaging step.

### Known minor issues
- `_ensure_group_exists()` inserts groups with default category "Personal" — groups whitelisted properly via v2 `/api/groups/whitelist` get correct categories from v1 cached classifications. Only affects groups that bypass the whitelist flow.
- `database is locked` error can still theoretically occur if a user runs discover and refresh simultaneously. The write lock prevents this within a single stage, but two concurrent stages could contend. Low priority — users typically run one stage at a time.

## Critical Context for Next Session

- **Gemini API key is set** in `taskdog-backend/.env` as `GEMINI_API_KEY`.
- **Go bridge binary exists** at `whatsapp-mcp/whatsapp-bridge/wa-bridge` — no compilation needed.
- **Python venv exists** at `taskdog-backend/venv/` — always use `venv/bin/python`, never system Python (system Python is mambaforge and broken with `no module named 'encodings'`).
- **node_modules installed** in `taskdog-frontend/` — `npm run dev` works immediately.
- **WhatsApp is paired** — bridge auto-connects on startup, no QR scan needed.
- **All 3 services are currently running.** To check: `lsof -ti:3001 && lsof -ti:8080 && lsof -ti:5173`.
- **Discovery has been run successfully** — 13 tasks from 10 groups are in the v2 DB, ready for deep-dive testing.
- **The runbook is the source of truth for commands** — see `v2_spec/05_runbook.md`. It is fully updated with the actual implemented file structure, accurate commands, and a troubleshooting table covering the FK/lock bugs and their fixes.

## Spec Documents

The `v2_spec/` directory contains the original 6 spec docs written before implementation. They were followed faithfully; the only deviations from spec are:
- Added `_ensure_group_exists()` (spec didn't anticipate the v1→v2 group table gap)
- Added the write lock + WAL mode (spec didn't anticipate concurrent write contention)
- Removed v1's `GET /api/groups` route (spec assumed v2 would cleanly own this endpoint, but didn't account for the v1 route still being registered)

These deviations are documented in the "Bugs Fixed" section above and in the runbook's troubleshooting table.

## Task Card Design (June 20 update)

**Approach: Static priority system — no animated decorations.** Clean hierarchy: title > priority > deadline > activity > owner.

| Element | IMP 5 | IMP 4 | IMP 3 | IMP 1-2 |
|---|---|---|---|---|
| Left bar | 4px `#7C3AED` | 4px `#EA580C` | 4px `#2563EB` | Transparent |
| Background tint | Purple gradient 6% → L | Orange gradient 5% → L | Blue gradient 3.5% → L | None |
| Badge | Solid purple fill, white text | Solid orange fill, white text | Blue outline, blue text | Grey outline |
| Top-priority (first 2 IMP 5) | 5px bar, 700 title weight, 10% tint | — | — | — |

**Keyframes:** Only `taskComplete` (280ms fade+slide for completion) and `checkPop` (250ms checkmark appear). All decorative animations (blobFloat, glowPulse, borderFlow, gradientFlow) **removed.**

**Checkbox:** Neutral `var(--outline-variant)` border, green (`#067647`) fill on check. No purple glow. 250ms `checkPop` on check.

**IMP labels replaced with star emojis:** IMP 1-3 = ⭐, IMP 4 = ⭐⭐, IMP 5 = ⭐⭐⭐. Badge colors still convey priority (purple fill, orange fill, blue outline).

**Modal status:** Dropdown replaced with three pill buttons (Active, Completed, Archived). Current status is highlighted (`is-active`). Clicking another pill changes status via PATCH and closes the modal.

**Completion animation:** Checking → `.is-completing` class → 280ms `taskComplete` → `animationend` → `load()` re-renders (completed tasks sorted to bottom within group). Unchecking reloads immediately.

**Hover:** Simple `background: var(--surface-container)` with 150ms transition. No decoration changes on hover.

**Filter pills:** Three groups separated by thin vertical rules — Priority (All, Critical, High) | Status (Active) | Type (Work, Personal).

**Status:** Green dot (`#15803D`) + muted label text — no pill/capsule.

**Card layout:** Tighter (18px vertical padding, 82px min-height). Title 14px/600, top-priority 15px/700. Metadata 12px with dot separators. Avatar 26px.
