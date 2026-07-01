---
type: Playbook
title: Reset Guide
description: How to wipe data and start fresh for first-time-user testing.
tags: [reset, operations]
---

# Reset Guide

## Quick Reset (v2 only — keeps pairing + v1)

```bash
lsof -ti:3001 | xargs kill -9
rm -f taskdog-backend/taskdog_v2.db taskdog-backend/taskdog_v2.db-wal taskdog-backend/taskdog_v2.db-shm
cd taskdog-backend && venv/bin/python app.py
```

## Full Reset (first-time-user experience)

Two scripts exist for full factory reset:

```bash
bash scripts/reset_first_time.sh            # primary — full factory reset with options
bash scripts/reset_first_time.sh --keep-key # preserve Gemini key
bash scripts/reset_first_time.sh --dry-run  # preview what would be deleted
```

Or the legacy alternative:
```bash
bash scripts/reset_all.sh                   # kills all services, deletes all DBs, clears key
```

This single command:
- Kills all services (bridge, Flask, Vite)
- Deletes all databases (v1, v2, bridge whatsapp.db + messages.db)
- Clears the Gemini API key from `.env`

## After Reset

Restart the 3 services and open http://localhost:5173/:

```bash
# Terminal 1
cd whatsapp-mcp/whatsapp-bridge && ./wa-bridge

# Terminal 2
cd taskdog-backend && venv/bin/python app.py

# Terminal 3
cd taskdog-frontend && npm run dev
```

You'll go through the full first-time flow:
1. **Gate A** — Enter Gemini API key
2. **Gate B** — QR code appears on-screen (no terminal needed). Scan with WhatsApp.
3. **Gate C** — Whitelist groups from classified chats
4. **Dashboard** — Run discovery to find tasks