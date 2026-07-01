---
type: API Endpoint
title: Groups Endpoints
description: Whitelist WhatsApp groups and list whitelisted groups for v2.
tags: [api, groups, whitelist]
---

# Groups Endpoints

## POST /api/groups/whitelist

Save selected groups to the v2 `groups` table. For each JID, resolves the display name from the WhatsApp DB and looks up cached classification (category + tldr) from v1. Also removes groups the user deselected (not in the provided list).

**Request**:
```json
{
    "jids": ["120363123456@g.us", "919967151186@s.whatsapp.net"]
}
```

**Response**:
```json
{
    "ok": true,
    "count": 2
}
```

## GET /api/groups

List all whitelisted groups with task counts and active task counts.

**Response**:
```json
{
    "ok": true,
    "groups": [
        {
            "jid": "120363123456@g.us",
            "name": "Product Team Invoice Payouts",
            "category": "Work",
            "tldr": "Invoice processing and payout discussions",
            "whitelisted_at": "2026-06-15T10:30:00",
            "task_count": 3,
            "active_count": 3,
            "last_refreshed_at": null
        }
    ]
}
```

This endpoint reads from the v2 `groups` table. v1's version of this endpoint was removed to avoid conflict.
