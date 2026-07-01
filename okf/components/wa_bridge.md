---
type: Component
title: WhatsApp Bridge (wa-bridge)
description: A Go binary that connects to WhatsApp via the whatsmeow library and serves chat/message/send endpoints on port 8080.
resource: file://whatsapp-mcp/whatsapp-bridge/wa-bridge
tags: [go, whatsapp, bridge]
---

# WhatsApp Bridge

The **wa-bridge** is a pre-built Go binary at `whatsapp-mcp/whatsapp-bridge/wa-bridge`. It uses the [`whatsmeow`](https://github.com/tulir/whatsmeow) library to connect to WhatsApp Web.

## Capabilities

- **Pairing**: QR code scan via WhatsApp → Settings → Linked Devices.
- **Auto-connect**: If already paired, connects on startup without QR scan.
- **Endpoints**: Serves chat list, message history, and send message on port 8080.
- **Persistence**: Stores session and messages in `store/` at the project root (`store/whatsapp.db` and `store/messages.db`).

## Lifecycle

```bash
# Start
cd whatsapp-mcp/whatsapp-bridge && ./wa-bridge

# Check status
curl http://localhost:8080/api/status

# Kill
pkill -f wa-bridge
```

## Interaction with Flask Backend

The Flask backend at port 3001 proxies bridge calls for the frontend. The frontend never talks to the bridge directly. Bridge status is polled via `GET /api/bridge/status`, messages are fetched through the Flask layer.

## Storage

Bridge stores its own session database (`whatsapp.db`) and message cache (`messages.db`) in `store/` at the project root. These are separate from the v1 and v2 SQLite databases managed by the Flask backend.
