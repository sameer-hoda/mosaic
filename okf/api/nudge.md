---
type: API Endpoint
title: Nudge & Persona Endpoints
description: Generate AI-powered nudge messages and manage communication persona for task followups.
tags: [api, nudge, persona]
---

# Nudge & Persona Endpoints

## POST /api/nudge/generate

Generate 3 nudge variants for a task (gentle, passive-aggressive, aggressive). Uses Gemini styled by the saved persona.

**Request**:
```json
{
    "task_id": "10fcd89b-..."
}
```

**Response**:
```json
{
    "ok": true,
    "nudges": [
        {"tone": "gentle", "text": "Hey, just checking in on this — any updates when you get a chance?"},
        {"tone": "passive", "text": "Not sure if this slipped, but circling back on the budget plan..."},
        {"tone": "aggressive", "text": "This needs resolution ASAP — the June budget deadline is this week."}
    ],
    "recipient": "120363123456@g.us"
}
```

Recipient is resolved from the task's group JID or assignee JID.

## GET /api/persona

Read the current persona text.

**Response**: `{"ok": true, "persona": "The user's persona text..."}`

## POST /api/persona

Save a persona text.

**Request**: `{"persona": "Communication style: direct and concise..."}`

**Response**: `{"ok": true}`

## POST /api/persona/generate

Auto-generate a persona from the user's last 50 outgoing WhatsApp messages. Analyzes tone, style, vocabulary, and communication patterns via Gemini.

**Response**: `{"ok": true, "persona": "Auto-generated persona text..."}`
