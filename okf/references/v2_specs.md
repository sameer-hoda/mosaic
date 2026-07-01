---
type: Reference
title: v2 Spec Documents
description: The original 6 spec documents that guided the v2 implementation. Located in the v2_spec/ directory.
tags: [specs, documentation]
---

# v2 Spec Documents

The `v2_spec/` directory at the project root contains the original 6 spec documents. They were authored before implementation and followed faithfully, with three exceptions documented below.

## Files

| File | Description |
|---|---|
| [00_MASTER_SPEC.md](../v2_spec/00_MASTER_SPEC.md) | Master specification — overview, architecture, and implementation plan. |
| [01_database_schema.md](../v2_spec/01_database_schema.md) | Database schema design for v2. |
| [02_api_contracts.md](../v2_spec/02_api_contracts.md) | All v2 API endpoint contracts. |
| [03_gemini_prompts.md](../v2_spec/03_gemini_prompts.md) | Gemini prompt designs for discover, refresh, deep-dive. |
| [04_implementation_plan.md](../v2_spec/04_implementation_plan.md) | Detailed implementation plan (Stages A-I). |
| [05_runbook.md](../v2_spec/05_runbook.md) | Updated runbook with accurate commands and troubleshooting. |

## Deviations from Spec

1. **`_ensure_group_exists()`** — Not in the spec. Added to handle v1→v2 group table gap.
2. **Write lock + WAL mode** — Not in the spec. Added to fix concurrent write contention.
3. **v1 `GET /api/groups` removed** — The spec assumed v2 would cleanly own this endpoint, but didn't account for the v1 route still being registered.
4. **Nudge blueprint** — Not in the original spec. Added after implementation to support nudge generation and persona management.
5. **Contact resolver** — Not in the original spec. Added to handle JID/LID→human name resolution across pipeline results.
6. **Database schema divergences** — Actual schema uses `context` instead of `description`, adds `tldr`/`whitelisted_at` to groups, adds `relevance`/`message_time` to task_messages, uses `message_text`/`recipient_jid` in followup_history.
