---
type: Playbook
title: Dev Setup — 3-Terminal Development
description: How to run all three services for local development.
tags: [setup, development]
---

# Dev Setup

Three terminals are needed for local development:

## Terminal 1 — Go WhatsApp Bridge (port 8080)

```bash
cd whatsapp-mcp/whatsapp-bridge
./wa-bridge
```

Scan the QR code from WhatsApp → Settings → Linked Devices → Link a Device. If already paired, the bridge auto-connects on startup.

Bridge stores session data in `store/` (project root — `store/messages.db` and `store/whatsapp.db`).

## Terminal 2 — Flask Backend (port 3001)

```bash
cd taskdog-backend
venv/bin/python app.py
```

Uses the virtual environment at `taskdog-backend/venv/`. Always use `venv/bin/python`, never system Python (system Python is mambaforge and broken with `no module named 'encodings'`).

## Terminal 3 — Vite Frontend (port 5173)

```bash
cd taskdog-frontend
npm run dev
```

Open **http://localhost:5173/** in your browser.

## Service Status Check

```bash
lsof -ti:3001   # Flask
lsof -ti:8080   # Bridge
lsof -ti:5173   # Vite
```

All three should return PIDs if running.

## Environment Variables

Set in `taskdog-backend/.env`:

```env
GEMINI_API_KEY="AIzaSy..."
DATABASE_PATH="taskdog.db"
DATABASE_PATH_V2="taskdog_v2.db"
```
