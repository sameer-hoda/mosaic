---
type: Component
title: Vite Frontend
description: React single-page application served by Vite on port 5173, with a phase router, SSE streaming API client, and 11 components.
resource: file://taskdog-frontend/src
tags: [react, vite, frontend]
---

# Vite Frontend

The React frontend at `taskdog-frontend/` provides the user interface for onboarding and the dashboard. For production packaging, see [taskdog-app/DISTRIBUTION_PLAN.md](../../taskdog-app/DISTRIBUTION_PLAN.md) (SwiftUI) and [deployment/taskdog-electron/](../../deployment/taskdog-electron/) (Electron).

## File Structure

```
taskdog-frontend/src/
├── app.js                         # Phase router (7 phases: APIKEY/PAIRING/WHITELIST/CLASSIFY/EXTRACT/KANBAN/DASHBOARD)
├── api.js                         # API client (v1 + v2 endpoints, SSE stream parsers)
├── main.js                        # Entry point, mounts to #app
├── styles.css                     # Global styles
├── layout.css                     # Layout-specific styles
└── components/
    ├── ApiKey.js                  # Gate A: Gemini key entry
    ├── Pairing.js                 # Gate B: WhatsApp bridge pairing
    ├── Whitelist.js               # Gate C: group selection (uses Classifier)
    ├── Dashboard.js               # v2 task list with stats + pipeline controls + nudge panel
    ├── DeepDive.js                # Task knowledge page drawer
    ├── Header.js                  # Top bar with Dashboard/Groups nav
    ├── Classifier.js              # v1 classifier (reused in Gate C)
    ├── Kanban.js                  # v1 Kanban board (legacy, co-exists)
    ├── TaskDrawer.js              # v1 task detail drawer (legacy)
    ├── HistoryDrawer.js           # v1 history drawer (legacy)
    └── Extracting.js              # v1 extraction progress (legacy)
```

## Phase Router

`app.js` manages the onboarding flow via a state machine:

```
APIKEY → PAIRING → WHITELIST → DASHBOARD
                                       ├── CLASSIFY (v1, accessible via tab)
                                       ├── EXTRACT  (v1, accessible via tab)
                                       └── KANBAN   (v1, accessible via tab)
```

On health check: if key not set → APIKEY; bridge not connected → PAIRING; no whitelisted groups → WHITELIST; otherwise → DASHBOARD. v1 legacy phases (CLASSIFY, EXTRACT, KANBAN) remain accessible once in the dashboard.

## API Client

`api.js` provides:
- 15+ v2 endpoint wrappers (health, groups, pipeline, dashboard, tasks, nudge, persona)
- `_streamSSE()` helper for processing Server-Sent Events
- Streaming variants for discover/refresh/classify
- All v1 endpoint wrappers (bridge status, classify, send, history)
- Persona and nudge generation endpoints

## Key UI Features

- **Light + Dark mode** support via CSS variables
- **Star emojis** for importance (⭐/⭐⭐/⭐⭐⭐ for IMP 1-3/4/5)
- **Status pills** (Active/Completed/Archived as clickable pills in modal)
- **Checkbox** for quick status toggling with completion animation
- **SSE streaming** modal for discover/refresh progress

## Build

```bash
cd taskdog-frontend
npm run dev       # Dev server with hot reload
npx vite build    # Production build
```
