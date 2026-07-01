---
type: Onboarding
title: Gate B — WhatsApp Bridge
description: Second onboarding gate — waits until the WhatsApp bridge is connected and paired.
tags: [onboarding, bridge, whatsapp]
---

# Gate B — WhatsApp Bridge

## Purpose

Ensure the Go bridge is running and connected to WhatsApp before proceeding to group selection.

## Check

`GET /api/bridge/status` returns (via v1 `routes/tasks.py`):
- `connected` — bridge is paired and ready
- `pairing` — bridge is running, waiting for QR scan
- `offline` — bridge is not running

The v2 setup route also has its own bridge status check that tests:
1. Port 8080 open → `"connected"`
2. `pgrep -f wa-bridge` matches → `"pairing"`
3. Otherwise → `"offline"`

## Flow

1. App polls `/api/bridge/status` every 2 seconds
2. Shows a spinner with "Waiting for WhatsApp connection..."
3. When status is `connected`, auto-advances to Gate C
4. If `pairing`, prompts to scan QR from WhatsApp → Settings → Linked Devices
5. If `offline`, prompts to start `./wa-bridge` in Terminal 1

## Current State

Bridge is already paired and connects automatically on startup. Gate B auto-advances within seconds.
