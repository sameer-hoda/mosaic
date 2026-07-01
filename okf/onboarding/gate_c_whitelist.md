---
type: Onboarding
title: Gate C — Group Whitelisting
description: Third onboarding gate — user selects which WhatsApp groups to track via a classified chat list. Groups saved to v2 groups table.
tags: [onboarding, groups, whitelist]
---

# Gate C — Group Whitelisting

## Purpose

Let the user pick which WhatsApp groups/chats to track tasks from. Selected groups are saved to the v2 `groups` table with their category and TLDR.

## Flow

1. App calls `POST /api/chats/classify` (v1 endpoint) to get up to 100 chats
2. Each chat displays: name, category (Work/Personal), and TLDR summary
3. User checks the checkbox for groups they want to track
4. User clicks "Whitelist Selected"
5. App POSTs to `/api/groups/whitelist` with the array of selected JIDs
6. v2 groups route resolves display names from WhatsApp DB, looks up cached classifications (category + tldr), inserts into v2 `groups` table
7. Also removes groups the user deselected (not in the provided list) via `delete_groups_not_in()`
8. On success, routes to the Dashboard

## Key Detail

Groups whitelisted via this flow get correct categories from v1 cached classifications. Groups auto-inserted via `_ensure_group_exists()` in the pipeline get category "Personal" by default.

## Current State

10 groups are whitelisted (8 Work, 2 Personal), including group chats like "Product Team Invoice Payouts", "Bio auth <> edu", and DMs with "Ayesha" and "Arnav Anand".
