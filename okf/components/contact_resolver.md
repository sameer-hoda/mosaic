---
type: Component
title: Contact Resolver
description: Utility module that resolves raw WhatsApp JID/LID identifiers to human-readable names.
resource: file://taskdog-backend/utils/contact_resolver.py
tags: [python, utility, contacts]
---

# Contact Resolver

The contact resolver at `utils/contact_resolver.py` normalizes WhatsApp identifiers (JIDs and LIDs) to human-readable names. It's used in the pipeline, dashboard, and nudge routes.

## Functions

- `resolve_contact(identifier: str) -> str` — Resolves a JID (ending in `@s.whatsapp.net`), LID (ending in `@lid`), or raw phone number to a human-readable name. Queries the bridge's `whatsapp.db` for the most recent display name via the `whatsmeow_contacts`, `whatsmeow_device`, `whatsmeow_lid_map`, and `chats` tables.
- `get_user_identity() -> dict` — Returns the connected WhatsApp user's jid, push_name, and lid from `whatsmeow_device`.
- `get_user_name() -> str` — Returns the connected user's display name.
- `resolve_task_assignees(task: dict) -> dict` — Adds an `assignee_name` field (human-readable) to the task dict.

## Usage

Used in:
- `routes/pipeline.py` — resolves people names after deep-dive
- `routes/dashboard.py` — resolves assignee names in dashboard and task detail responses
- `routes/nudge.py` — resolves assignee names for nudge generation context

## Storage

The module queries the bridge's `whatsapp.db` at `whatsapp-mcp/whatsapp-bridge/store/whatsapp.db` for contact resolution (relative to `taskdog-backend/`). It reads the `whatsmeow_contacts`, `whatsmeow_device`, `whatsmeow_lid_map`, and `chats` tables — not the `messages.db`. If no match is found, the original JID/LID is returned unchanged.
