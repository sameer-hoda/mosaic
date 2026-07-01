# Components

- [WhatsApp Bridge](wa_bridge.md) — Go binary using whatsmeow library, serves WhatsApp data on port 8080.
- [Flask Backend](flask_backend.md) — Python Flask app on port 3001, registers 6 blueprints (v1 + v2 + nudge/persona).
- [Vite Frontend](vite_frontend.md) — React SPA with phase router, 15+ v2 API endpoints, SSE streaming, 11 components.
- [Database v2 Module](database_v2.md) — SQLite schema + CRUD with thread-safe write lock, WAL mode, dedup logic.
- [Contact Resolver](contact_resolver.md) — JID/LID-to-human-name resolution utility.
