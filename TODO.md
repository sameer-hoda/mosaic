# Mosaic — TODO

Last updated: 24 Jun 2026

---

## 1. Rebrand to "Mosaic"

### 1.1 Frontend UI
- [ ] `taskdog-frontend/index.html:7` — change `<title>` to "Mosaic · WhatsApp Task Intelligence"
- [ ] `taskdog-frontend/src/components/Header.js:21` — change `<h1>TaskDog</h1>` to `<h1>Mosaic</h1>`
- [ ] `taskdog-frontend/src/components/Header.js:64,71` — change `localStorage` key from `taskdog-theme` to `mosaic-theme`
- [ ] `taskdog-frontend/src/components/ApiKey.js:16` — change `<h2>TaskDog</h2>` to `<h2>Mosaic</h2>`
- [ ] `taskdog-frontend/src/components/ApiKey.js:25` — update copy from "TaskDog uses Google Gemini…" to "Mosaic uses Google Gemini…"
- [ ] `taskdog-frontend/src/components/Pairing.js:17` — change `<h2>TaskDog</h2>` to `<h2>Mosaic</h2>`
- [ ] `taskdog-frontend/src/styles.css:2` — update header comment branding
- [ ] `taskdog-frontend/src/api.js:1` — update comment

### 1.2 Frontend internals (no user-visible change, but good hygiene)
- [ ] `taskdog-frontend/package.json:2` — change `"name"` from `"taskdog-frontend"` to `"mosaic-frontend"` (or leave as-is since it's private)
- [ ] `taskdog-frontend/src/app.js:46` — rename custom event `taskdog:setCategory` → `mosaic:setCategory` (and all listeners in Kanban.js, Classifier.js)
- [ ] `taskdog-frontend/src/components/Classifier.js:25` — rename drag MIME type `application/x-taskdog-jid` → `application/x-mosaic-jid`
- [ ] `taskdog-frontend/src/components/Classifier.js:39` — change model name "TaskDog-v2.1" → "Mosaic-v1"
- [ ] `taskdog-frontend/src/components/Classifier.js:107` — update copy: "TaskDog will dig through…" → "Mosaic will dig through…"
- [ ] `taskdog-frontend/src/components/Kanban.js` — update event listeners (`taskdog:showHistory`, `taskdog:setCategory`)

### 1.3 Backend
- [ ] `taskdog-backend/app.py:3,45` — update docstring and index route message
- [ ] `taskdog-backend/routes/auth.py:2,12` — update docstring; change default SECRET_KEY from `taskdog-secret-key-change-in-production`
- [ ] `taskdog-backend/routes/setup.py:2` — update docstring
- [ ] `taskdog-backend/routes/groups.py:2` — update docstring
- [ ] `taskdog-backend/routes/pipeline.py:2` — update docstring
- [ ] `taskdog-backend/routes/dashboard.py:2` — update docstring
- [ ] `taskdog-backend/routes/tasks.py:2` — update docstring
- [ ] `taskdog-backend/routes/nudge.py:2` — update docstring
- [ ] `taskdog-backend/models/database_v2.py:2,116` — update docstring and init log message

### 1.4 Electron deployment
- [ ] `deployment/taskdog-electron/package.json` — change `name`, `appId` (`com.mosaic.desktop`), `productName`, `author`, `description`, DMG title, microphone/camera descriptions
- [ ] `deployment/taskdog-electron/main.js:2,207` — update docstring and window title
- [ ] `deployment/taskdog-electron/frontend-src/index.html:7` — update title

### 1.5 Docs
- [ ] `AGENTS.md` — update all TaskDog references
- [ ] `PROJECT_IDENTITY.md` — update if keeping
- [ ] `v2_spec/05_runbook.md` — update commands/names if they reference taskdog

---

## 2. Improve First-Time User Journey

### 2.1 Gate A — API Key entry (`ApiKey.js`)
- [ ] **Persist the Gemini key properly.** Currently the `validateKey` endpoint can't persist (comment: "that's the shell's job"). The `.env` has `GEMINI_API_KEY=` (empty). Add a `/api/setup/save-key` endpoint that writes the key to `.env` and restarts the Flask env var, so the user doesn't have to manually edit a file.
- [ ] **Visual feedback.** After "Valid!" shows, the spinner on the button says "Continuing…" but the timer is a hardcoded 1200ms. Add a progress bar or countdown indicator so the user isn't staring at a frozen screen.
- [ ] **Better error messages.** When Gemini rejects the key, show a more helpful message than "Invalid key (rejected by Gemini: 403)" — tell them to check they enabled the API in Google Cloud Console.
- [ ] **Let user paste full key with keyboard.** The current Enter key handler works, but add an explicit "Paste key" hint or button.

### 2.2 Gate B — WhatsApp Pairing (`Pairing.js`)
- [ ] **Show actual progress.** The three statuses (offline → pairing → connected) are good, but add an animated "waiting for scan" visual (pulsing ring around the QR code) to make it clear the app is alive.
- [ ] **Handle stale QR codes.** WhatsApp QR codes expire. The bridge sends a new QR via SSE event `code`. But if the user hasn't scanned in 60s, show a "QR code refreshed" subtle animation so they know to re-scan.
- [ ] **Timeout fallback.** If the bridge stays in "pairing" for >5 minutes, show a "Trouble scanning?" link with manual instructions (force close WhatsApp, ensure same WiFi, etc.).
- [ ] **Logout flow.** The "Log out & start over" button calls `/api/setup/reset` which runs `pkill -f "server"` — this is destructive and kills other processes. Make the reset button scoped and add a secondary confirmation step.

### 2.3 Gate C — Group Whitelisting (`Whitelist.js`)
- [ ] **Loading skeleton.** Instead of a single spinner, show skeleton rows (gray placeholder bars) while chats load — feels faster.
- [ ] **Search/filter.** If the user has 100+ chats, scrolling to find the right groups is painful. Add a search bar at the top of the list.
- [ ] **Categorize on load.** Show category badges (Work/Personal) next to each chat name during whitelist, so the user can quickly identify groups. The backend already has this data from v1 classifications.
- [ ] **"Select All" / "Deselect All"** toggles in the action bar for power users.
- [ ] **Pre-select by category.** Add filter chips: "All", "Work", "Personal", "Groups only", "DMs only".

### 2.4 Post-onboarding — First Dashboard load
- [ ] **Auto-discover should show a clear interstitial.** When `autoDiscover: true`, the dashboard silently triggers `runDiscover()`. Show a prominent "Discovering your tasks…" overlay with a progress bar so the user isn't confused by an empty dashboard for 30+ seconds.
- [ ] **Empty state.** If no tasks found after discovery, show a helpful empty state: "No tasks found yet. Try whitelisting more groups or sending more messages in your chats." — not just a blank dashboard.
- [ ] **First-task tooltip.** When the first task card appears, show a subtle tooltip: "Click a task to deep-dive, or check the box to mark it complete."

---

## 3. Security & Bug Fixes

### 3.1 CRITICAL — Secret leaks (fix IMMEDIATELY)
- [ ] **Remove `_secrets/` directory entirely.** Contains `mynextbib_v2.pem` (AWS PEM private key, mode 0400) and `ec2_ssh_credentials.md` (EC2 IPs, instance IDs, AWS account number). If these have ever been in a git repo, rotate the keys.
- [ ] **Rotate your Gemini API key** if it was ever committed to version control.
- [ ] **Scan `_archive_2026_06/` for more secrets.** Explorer found Databricks tokens and Twenty CRM JWTs in archived code. Audit the entire archive before it's committed or shared.

### 3.2 CRITICAL — No auth on any v2 route
- [ ] **Apply `@token_required` decorator to ALL v2 endpoints.** Currently the decorator exists in `routes/auth.py` but is never used. All pipeline, dashboard, groups, and setup endpoints are unauthenticated. Anyone on the network can trigger Gemini API calls (which cost money) or delete data.
- [ ] **Protect `POST /api/setup/reset`.** This endpoint kills processes and deletes DBs with no auth. At minimum add `@token_required`, and ideally scope the `pkill -f "server"` command (it matches ANY process named "server").
- [ ] **Change default `SECRET_KEY`.** Both `app.py:13` and `routes/auth.py:12` use `'taskdog-secret-key-change-in-production'` as the fallback. Generate a random key or require the env var.

### 3.3 HIGH — CORS, debug mode, network exposure
- [ ] **Restrict CORS.** `CORS(app)` in `app.py:17` allows ANY origin. For dev, restrict to `http://localhost:5173`. For production, use the Electron app origin.
- [ ] **Disable `debug=True` in production.** `app.py:69` has `debug=True` which exposes the Werkzeug interactive debugger (RCE risk if an error is triggered). Set via env var: `debug=os.environ.get('FLASK_DEBUG', '0') == '1'`.
- [ ] **Don't bind to `0.0.0.0` by default.** `app.py:69` binds to all interfaces. In dev this is convenient (access from phone on same WiFi), but it means anyone on the LAN can hit the unauthenticated API. Bind to `127.0.0.1` by default, make `0.0.0.0` opt-in.

### 3.4 MEDIUM — Input validation, rate limiting, API exposure
- [ ] **Validate JIDs in `POST /api/groups/whitelist`.** Currently passes any string array to DB queries. Add a regex check: valid JIDs match `\d+@(g\.us|s\.whatsapp\.net)`.
- [ ] **Add rate limiting to pipeline endpoints.** `POST /api/pipeline/discover` calls Gemini for every group. A script could rack up $100s in API costs. Add Flask-Limiter (already in requirements? check) with a per-session cap.
- [ ] **Don't expose `gemini_key_preview` in `/api/health`.** Showing 7 of ~39 characters of the API key is a partial leak. Remove `gemini_key_preview` from the health response, or replace with `"gemini_key_set": true` only.
- [ ] **Validate `task_id` in `POST /api/pipeline/deep-dive`.** Ensure the task_id exists before calling Gemini.

### 3.5 BUGS — Code quality
- [ ] **Fix empty `GEMINI_API_KEY` in `.env`.** The key is currently empty. The backend will fail all Gemini calls. Either restore the key or guide the user through the onboarding flow.
- [ ] **Deduplicate `_is_port_open` / `_is_bridge_process_running`.** Identical functions in `routes/tasks.py` and `routes/setup.py`. Move to a shared `utils/bridge.py`.
- [ ] **Deduplicate `escapeHtml`.** Defined independently in `ApiKey.js`, `Whitelist.js`, `Dashboard.js`, `DeepDive.js`. Move to a shared `utils.js`.
- [ ] **Deduplicate SSE parsing.** `api.js` has 3 separate SSE parsers (classify, extract, and `_streamSSE`). Refactor v1 classify/extract streams to use `_streamSSE` instead of copy-pasted inline parsers.
- [ ] **Remove dead import of `renderDeepDive` in `app.js:9`.** The import exists but `PHASE.DEEPDIVE` is never defined and the switch has no deep-dive case. Either wire it up or remove the import.
- [ ] **Fix `DeepDive.js` — it has a `renderMarkdown` that's duplicated in `Dashboard.js`.** Consolidate into a shared markdown renderer.
- [ ] **Fix `setLastSynced` no-op in `Header.js:81`.** Either implement the function or remove the import in `app.js:7`.
- [ ] **Fix duplicate `/health` vs `/api/health`.** `app.py:55` has a `/health` endpoint, `routes/setup.py:60` has `/api/health`. They return different data. Consolidate.
- [ ] **Race condition in `Dashboard.js` auto-discover.** Lines 123-128 check `tasks.length === 0` and trigger `runDiscover()` — if the user navigates away during the discover, state is stale. Add a `discoverInProgress` flag to prevent double-triggers.
- [ ] **Refactor v1 SSE parsers to use `_streamSSE`.** `classifyChatsStream` (lines 120-154) and `extractTasksStream` (lines 192-225) are copy-pasted stream parsers — the shared `_streamSSE` function already exists and is used by v2 endpoints.
- [ ] **`renderDeepDive` imported in `app.js:9` but never rendered.** Either add a `PHASE.DEEPDIVE` case in the switch, or remove the import.

---

## Priority Order

1. **Secrets cleanup** (3.1) — do this before anything else
2. **Auth + debug mode** (3.2, 3.3) — critical for any shared use
3. **Gemini key persistence** (2.1) — blocks the entire onboarding flow if key is empty
4. **Rebranding** (1.1–1.5) — one sweep across all files
5. **UX improvements** (2.2–2.4) — polish the first-time flow
6. **Code quality bugs** (3.5) — dedup, dead code, refactors