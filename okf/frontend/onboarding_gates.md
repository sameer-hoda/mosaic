---
type: Component
title: Onboarding Gate Components
description: Three onboarding components — ApiKey (Gate A), Pairing (Gate B), Whitelist (Gate C) — that form the phased onboarding flow.
tags: [react, onboarding]
---

# Onboarding Gates

## Gate A — ApiKey.js

Displays when no valid Gemini API key is detected. Shows a key input field and a "Continue" button that calls `POST /api/setup/validate-key`. On success, advances to Gate B.

If the key is already set (detected via `GET /api/health`), a "Continue" button skips directly to Gate B.

The validate-key endpoint calls the Gemini models list; it does NOT persist the key (that's the shell's job via Keychain).

## Gate B — Pairing.js

Displays when the WhatsApp bridge is not connected. Polls `GET /api/bridge/status` every 2 seconds. Shows a spinner with "Waiting for WhatsApp connection..." text. Auto-advances to Gate C when the bridge connects.

The bridge auto-connects if already paired — no QR scan is needed on subsequent launches.

## Gate C — Whitelist.js

Displays a list of up to 100 classified chats (via the v1 `POST /api/chats/classify` endpoint). Each chat shows:
- **Name** (group name or contact name)
- **Category** (Work/Personal)
- **TLDR** (one-line summary from v1 classifier)

The user selects groups by checking a checkbox, then clicks "Whitelist Selected". The component POSTs to `/api/groups/whitelist` with the selected JIDs. On success, advances to the Dashboard.
