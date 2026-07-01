---
type: API Endpoint
title: Setup Endpoints
description: Health check and Gemini API key validation for v2 onboarding.
tags: [api, setup, health]
---

# Setup Endpoints

## GET /api/health

Combined health check for the v2 system. Also checks bridge status by testing port 8080 and process existence.

**Response**:
```json
{
    "ok": true,
    "gemini_key_set": true,
    "gemini_key_preview": "AIza…70k",
    "bridge_status": "connected"
}
```

`bridge_status` can be: `"connected"` (port 8080 open), `"pairing"` (wa-bridge process running but port not open), or `"offline"` (no process found).

## POST /api/setup/validate-key

Validate a Gemini API key by calling the models list endpoint. Does NOT persist the key — that's the shell's job (Keychain).

**Request**:
```json
{
    "key": "AIzaSy..."
}
```

**Response (valid)**:
```json
{
    "ok": true,
    "preview": "AIza…70k"
}
```

**Response (invalid)**:
```json
{
    "ok": false,
    "error": "Invalid key (rejected by Gemini: 403)"
}
```

Possible errors: `400` (no key provided), `504` (Gemini timeout), `502` (request failed).
