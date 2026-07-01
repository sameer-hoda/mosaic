---
type: Playbook
title: Troubleshooting
description: Common issues encountered during development and their solutions.
tags: [troubleshooting, operations]
---

# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Bridge is offline | wa-bridge not started | Start `./wa-bridge` in Terminal 1 |
| Bridge shows "pairing" | Not yet QR-scanned | WhatsApp → Settings → Linked Devices |
| `gemini_key_set: false` | No API key in `.env` | Set `GEMINI_API_KEY` in `taskdog-backend/.env` |
| `FOREIGN KEY constraint failed` | Group not in v2 `groups` table | Pipeline auto-inserts now via `_ensure_group_exists()` — restart backend |
| `database is locked` | Concurrent write contention | WAL mode + write lock should prevent this. Reduce MAX_WORKERS if persisting. |
| Gateway timeout on discover/refresh | Gemini call >120s | Reduce transcript window or group message volume |
| `Address already in use: 3001` | Old Flask process | `lsof -ti:3001 \| xargs kill -9` |
| `Address already in use: 8080` | Old bridge process | `pkill -f wa-bridge` |
| `no module named 'encodings'` | Using system Python (mambaforge) | Use `venv/bin/python` instead |
| Deep-dive returns empty wiki | Transcript has no relevant messages | Check the task was correctly identified during discovery |
| Gemini returns error | API key invalid or quota exceeded | Check key validity, retry |
| Dashboard shows 0 tasks | Discovery not yet run | Run "Discover Tasks" first |
| Legacy groups in dashboard | `/api/groups` was reading from v1 | Fixed — now reads from v2 table. Re-whitelist groups. |
| Duplicate tasks after refresh | Token-overlap dedup threshold too low | Check `_title_exists()` logic in `database_v2.py` |
| JID/LID showing instead of name | Contact resolver couldn't find match | Run `backfill_resolve_names()` in DB or send messages first |

## Known Issues

- `_ensure_group_exists()` inserts groups with default category "Personal" — groups whitelisted via v2 `/api/groups/whitelist` get correct categories from v1 cached classifications. Only affects groups that bypass the whitelist flow.
- `database is locked` can still theoretically occur if a user runs discover and refresh simultaneously. The write lock prevents this within a single stage, but two concurrent stages could contend. Low priority — users typically run one stage at a time.
- `persona.txt` is read/written to the backend root directory — not configurable. Ensure the process has write access.
