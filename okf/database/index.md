# Database

- [Schema Overview](schema_overview.md) — ERD, key design decisions, DDL, and table relationships.
- [Groups Table](groups.md) — Whitelisted WhatsApp groups with category, TLDR, and refresh timestamps.
- [Tasks Table](tasks.md) — Discovered tasks with status, importance, dedup logic, and deep-dive columns.
- [Task Messages Table](task_messages.md) — Messages tagged to specific tasks (no message_id, uses relevance scoring).
- [Followup History Table](followup_history.md) — Sent nudge/followup messages with recipient tracking.
