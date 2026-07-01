---
type: Component
title: Phase Router (app.js)
description: State machine that routes the user through phases — APIKEY → PAIRING → WHITELIST → DASHBOARD, with v1 legacy phases also accessible.
resource: file://taskdog-frontend/src/app.js
tags: [react, routing, state-machine]
---

# Phase Router

The `app.js` component implements a phase-based state machine for the onboarding flow. It coexists with v1 legacy phases (CLASSIFY, EXTRACT, KANBAN) that remain accessible once in the dashboard.

## Phase Constants

```javascript
export const PHASE = {
  APIKEY: 'apikey',
  PAIRING: 'pairing',
  WHITELIST: 'whitelist',
  CLASSIFY: 'classify',    // v1 legacy
  EXTRACT: 'extract',      // v1 legacy
  KANBAN: 'kanban',        // v1 legacy
  DASHBOARD: 'dashboard',
};
```

## Auto-Routing (on health check)

```
Health check:
  gemini_key_set?    No  → APIKEY
  bridge connected?  No  → PAIRING
  groups exist?      No  → WHITELIST
  Yes                    → DASHBOARD
```

## Phase Transitions

| Phase | Gate Condition | Auto-advances |
|---|---|---|
| `APIKEY` | Gemini key is set (checked via `/api/health`) | Yes — if key is already valid |
| `PAIRING` | Bridge is connected (polled via `/api/bridge/status` every 2s) | Yes — if already connected |
| `WHITELIST` | Groups are selected and whitelisted | Yes — if groups are already whitelisted |
| `DASHBOARD` | N/A — terminal phase | No |

Each phase has a loading/checking state that auto-routes. The router is designed so returning users skip straight to the dashboard.

## State Rendering

```javascript
function renderInternal() {
  switch (state.phase) {
    case PHASE.APIKEY:     return renderApiKey(main, state);
    case PHASE.PAIRING:    return renderPairing(main, state);
    case PHASE.WHITELIST:  return renderWhitelist(main, state);
    case PHASE.CLASSIFY:   return renderClassifier(main, state);
    case PHASE.EXTRACT:    return renderExtracting(main, state);
    case PHASE.KANBAN:     return renderKanban(main, state);
    case PHASE.DASHBOARD:  return renderDashboard(main, state);
  }
}
```

## Shell Layout

The app shell renders a top bar (Header) in all phases except PAIRING and APIKEY. The header provides navigation to Dashboard, Groups (whitelist), and legacy v1 phases.
