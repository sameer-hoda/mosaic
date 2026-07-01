---
okf_version: "0.2"
title: TaskDog v2 — WhatsApp Task Tracker
description: A WhatsApp-based task tracker that scans group/DM messages via a Go bridge, uses Gemini to discover tasks, refreshes them incrementally, produces deep-dive knowledge pages per task, and generates AI-powered nudge messages.
tags: [whatsapp, task-tracking, gemini, flask, react, sqlite]
timestamp: 2026-06-24T17:42:00Z
---

# TaskDog v2

TaskDog v2 is a WhatsApp-based task tracker. It scans WhatsApp group/DM messages via a Go bridge, uses Gemini to discover tasks, refreshes them incrementally, produces deep-dive knowledge pages per task, and generates AI-powered nudge messages. The user views everything in a web dashboard.

## Subdirectories

- [Architecture](architecture/index.md) — System architecture, dev setup, and data flow.
- [Components](components/index.md) — Individual component docs (Go bridge, Flask backend, Vite frontend, database, contact resolver).
- [Database](database/index.md) — v2 database schema and CRUD operations (4 tables with DDL).
- [API](api/index.md) — All v2 API endpoints and contracts (setup, groups, pipeline, dashboard, nudge/persona).
- [Pipelines](pipelines/index.md) — The 4-stage pipeline (discover, refresh, deep-dive, dashboard).
- [Frontend](frontend/index.md) — React frontend components, phase router (7 phases), SSE streaming API client, card design.
- [Onboarding](onboarding/index.md) — The 3-gate onboarding flow (API Key, Bridge, Whitelist).
- [Prompts](prompts/index.md) — Gemini AI prompts used for task extraction, refresh, and deep-dive (gemini-3.1-flash-lite-preview).
- [Playbooks](playbooks/index.md) — Runbook, reset guide, and troubleshooting.
- [References](references/index.md) — External references, spec docs, bug fixes, and distribution plans.
