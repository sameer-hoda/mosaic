---
type: Onboarding
title: Gate A — Gemini API Key
description: First onboarding gate — validates that a Gemini API key is configured and working.
tags: [onboarding, gemini, api-key]
---

# Gate A — Gemini API Key

## Purpose

Ensure a valid Gemini API key is available before proceeding. All pipeline stages (discover, refresh, deep-dive) depend on Gemini calls.

## Check

`GET /api/health` returns `gemini_key_set: true` if a key is in the `.env` file.

## Flow

1. App starts on the API Key screen
2. If key is already set (checked via health endpoint), show a "Continue" button → Gate B
3. If key is not set, show a text input + "Validate" button
4. `POST /api/setup/validate-key` with `{"key": "AIzaSy..."}` — calls Gemini models list endpoint
5. Note: The key is **not persisted** by this endpoint — the shell (Keychain) manages persistence
6. On success → Gate B. On failure → show error message.

## Configuration

The key lives in `taskdog-backend/.env`:

```env
GEMINI_API_KEY="AIzaSy..."
```

## Gemini Model

All v2 stages use `gemini-3.1-flash-lite-preview` (default) or `gemini-3.1-pro-preview` for the REST API. Temperature varies by stage (0.2-0.4).

## Current State

The key is already set in `.env`. The Gate A screen shows "Continue" and the user can skip directly to Gate B.
