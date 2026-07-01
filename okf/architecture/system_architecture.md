---
type: Architecture
title: System Architecture
description: TaskDog v2 uses a 3-tier architecture — WhatsApp phone, Go bridge (port 8080), Flask backend (port 3001), and Vite frontend (port 5173).
tags: [architecture, topology]
---

# System Architecture

```
WhatsApp phone ──► wa-bridge (Go, :8080) ──► Flask app (Python, :3001) ──► Vite frontend (:5173)
                                                       │
                                            ┌──────────┴──────────┐
                                        taskdog.db (v1)     taskdog_v2.db (v2)
```

## Tiers

1. **WhatsApp Phone** — The user's phone, connected via WhatsApp Web protocol. No server-side component.
2. **wa-bridge** — A Go binary using the [`whatsmeow`](https://github.com/tulir/whatsmeow) library. Serves chat list, messages, and send endpoints on port 8080. Pre-built binary; no Go compilation needed. Stored at `whatsapp-mcp/whatsapp-bridge/wa-bridge`. Session DB and message cache stored in `store/` at the project root.
3. **Flask Backend** — A Python Flask app on port 3001. Registers **6 blueprints** covering v1 and v2 routes. Both `taskdog.db` (v1) and `taskdog_v2.db` (v2) auto-initialize on startup.
4. **Vite Frontend** — A React single-page application on port 5173. For production packaging, see [taskdog-app/DISTRIBUTION_PLAN.md](../../taskdog-app/DISTRIBUTION_PLAN.md) (SwiftUI) and [deployment/taskdog-electron/](../../deployment/taskdog-electron/) (Electron).

## Coexistence of v1 and v2

- v1 DB (`taskdog.db`) continues to serve chat reads via `models/database.py`.
- v2 DB (`taskdog_v2.db`) is new, fresh, and not migrated from v1.
- Users re-whitelist groups in v2.
- v1 routes (bridge status, classify, send, history) are unchanged and reused by v2 onboarding gates.
- The v1 `GET /api/groups` route was **removed** — v2's `routes/groups.py` now owns this endpoint.
- A new `routes/nudge.py` blueprint handles persona management and nudge generation (v2 addition).

## Production Packaging

Two approaches exist side-by-side:
- **SwiftUI + WKWebView** — `taskdog-app/` bundles all 3 tiers into a macOS `.app` (Apple Silicon only).
- **Electron** — `deployment/taskdog-electron/` wraps the frontend in Electron for cross-platform.

See [Components](../components/index.md) for detailed breakdowns of each tier.
