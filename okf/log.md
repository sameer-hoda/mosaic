# Knowledge Update Log

## 2026-06-24
- **OKF Sync**: Full end-to-end audit and sync. Verified all 50+ OKF files against actual source code.
- **Fixes in OKF**:
  - `components/contact_resolver.md`: Fixed store path (was `store/messages.db`, now `whatsapp-mcp/whatsapp-bridge/store/whatsapp.db` + documents actual tables queried). Added missing `get_user_identity()` and `get_user_name()` functions.
  - `playbooks/reset_guide.md`: Updated to reference `reset_first_time.sh` as primary script (both `reset_first_time.sh` and `reset_all.sh` exist).
  - `playbooks/runbook.md`: Added single-command quick start section (`scripts/start.sh`).
  - `index.md`, `log.md`, `.last_sync`: Updated timestamps.

## 2026-06-21
- **OKF Sync**: Full end-to-end review and sync. Updated all 45+ OKF files to match actual codebase.
- **Fixes in OKF**:
  - Architecture: 6 blueprints (not 5), added nudge blueprint, updated store path.
  - Database: Updated DDL with actual columns (context, not description; tldr/whitelisted_at in groups; relevance/message_time in task_messages; jid/recipient_jid in followup_history).
  - API: Fixed all response schemas (groups uses `count` not `whitelisted`; pipeline has summary block; dashboard has enriched fields).
  - Prompts: Updated schemas to match actual Gemini output (context not description, suggested_responses not tags, progress_log not timeline).
  - Frontend: Updated file structure (11 components), added contact_resolver and nudge docs.
  - Distribution: Added Electron packaging alternative.
  - Playbooks: Updated runbook with nudge/persona commands and correct DB paths.

## 2026-06-20
- **Creation**: Established the full OKF bundle for TaskDog v2.
- **Update**: Discovery pipeline successfully run — 13 tasks from 10 groups in production DB.
- **Fix**: Resolved FK constraint failures (v1 route shadowing v2's `/api/groups`).
- **Fix**: Resolved "database is locked" errors (added WAL mode + write lock serialization).
- **Fix**: Added `_ensure_group_exists()` auto-insert in pipeline for missing groups.

## 2026-06-07
- **Build**: Implemented Stages A-I of v2 — full backend (DB, routes, Gemini), full frontend (components, API client, router), and 30 integration tests.

## 2026-06-06
- **Creation**: Started v2 build. Authored 6 spec documents in `v2_spec/`.
