---
title: Data Sources
description: Database schemas and resolution logic.
---

# Data Sources

## `messages.db`

| Table | Rows | Key Columns |
|---|---|---|
| `chats` | ~2,400 | `jid`, `name`, `last_message_time` |
| `messages` | ~64,000 | `chat_jid`, `sender`, `content`, `timestamp`, `is_from_me` |

## `whatsapp.db`

| Table | Rows | Key Columns |
|---|---|---|
| `whatsmeow_device` | 1 | `jid`, `push_name`, `lid` |
| `whatsmeow_contacts` | ~3,200 | `their_jid`, `push_name`, `full_name` |
| `whatsmeow_chat_settings` | ~540 | `chat_jid`, `archived`, `pinned` |
| `whatsmeow_lid_map` | varies | `lid`, `pn` (phone) |

## Resolution Priority

1. `whatsmeow_contacts.push_name` → `full_name` → `first_name` → `business_name`
2. Group JIDs: `chats.name` from messages.db
3. LIDs: `whatsmeow_lid_map` → phone → contacts lookup
4. Own JID: `whatsmeow_device.push_name`
5. Phone: formatted as `+91 XXXXX XXXXX`
