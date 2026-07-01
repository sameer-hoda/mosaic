# Pipelines

- [Discover](discover.md) — Stage 1: 30-day message scan, Gemini extracts all tasks per group. Parallel with ThreadPoolExecutor(3).
- [Refresh](refresh.md) — Stage 2: Incremental update since last refresh. Processes status changes, progress notes, new tasks with dedup.
- [Deep-Dive](deep_dive.md) — Stage 3: Full 365-day transcript → Gemini → wiki, people, progress_log, blockers, decisions, importance.
- [Dashboard View](dashboard_view.md) — Stage 4: Pure DB read, no Gemini. Enriched with message count, assignee names, deep-dive status.
