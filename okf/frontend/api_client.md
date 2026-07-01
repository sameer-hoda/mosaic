---
type: Component
title: API Client (api.js)
description: Central API client with 15+ v2 endpoints, all v1 endpoints, and SSE stream parser helpers for discover/refresh/classify.
resource: file://taskdog-frontend/src/api.js
tags: [javascript, api, sse]
---

# API Client

The `api.js` module bundles all API communication for the frontend.

## v2 Endpoints

| Function | HTTP | Endpoint |
|---|---|---|
| `healthV2()` | GET | `/api/health` |
| `validateKey(key)` | POST | `/api/setup/validate-key` |
| `whitelistGroups(jids)` | POST | `/api/groups/whitelist` |
| `getGroupsV2()` | GET | `/api/groups` |
| `discoverTasks(jids)` | POST | `/api/pipeline/discover` |
| `discoverTasksStream({jids, callbacks})` | POST (SSE) | `/api/pipeline/discover/stream` |
| `refreshTasks(jids)` | POST | `/api/pipeline/refresh` |
| `refreshTasksStream({jids, callbacks})` | POST (SSE) | `/api/pipeline/refresh/stream` |
| `deepDive(taskId)` | POST | `/api/pipeline/deep-dive` |
| `getDashboard(groupJid?)` | GET | `/api/dashboard` |
| `getTask(id)` | GET | `/api/tasks/{id}` |
| `getTaskMessages(id)` | GET | `/api/tasks/{id}/messages` |
| `updateTask(id, data)` | PATCH | `/api/tasks/{id}` |
| `generateNudges(taskId)` | POST | `/api/nudge/generate` |
| `getPersona()` | GET | `/api/persona` |
| `savePersona(text)` | POST | `/api/persona` |
| `generatePersona()` | POST | `/api/persona/generate` |

## SSE Stream Parser

The shared `_streamSSE(res, handlers)` helper reads a ReadableStream from `fetch()` and dispatches parsed JSON to named event handlers:

```javascript
// Used internally by discoverTasksStream, refreshTasksStream
async function _streamSSE(res, handlers = {}) {
  // ...
  // dispatches to handlers[eventName](data)
}
```

Discover stream events: `meta`, `group`, `done`, `error`
Refresh stream events: `meta`, `task`, `new_task`, `done`, `error`
Classify stream events: `meta`, `chat`, `done`, `error`

## v1 Endpoints (coexisting)

The API client also includes `getGroups`, `getHistory`, `sendNudge`, `getChats`, `classifyChats`, `classifyChatsStream`, `extractTasks`, `extractTasksStream`, `updateChatCategory`, `getTasks`, `updateTaskStatus`, and legacy v1 endpoints.
