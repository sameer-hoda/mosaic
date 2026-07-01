---
type: Component
title: Deep-Dive Viewer (DeepDive.js)
description: A drawer/side panel that renders the deep-dive knowledge page for a task — wiki, people, timeline, blockers, decisions.
resource: file://taskdog-frontend/src/components/DeepDive.js
tags: [react, deep-dive, wiki]
---

# Deep-Dive Viewer

The `DeepDive.js` component is a slide-in drawer that opens when a user clicks a task card or the deep-dive button on the dashboard.

## Sections

1. **Wiki** — Renders the Markdown `wiki` field using a simple Markdown renderer. Contains the full knowledge page for the task.
2. **People** — Displays the people list (from the `people` JSON column) as a grid of name + role cards. Roles: assignee, requestor, reviewer, stakeholder.
3. **Timeline** — Renders the `progress_log` as a vertical timeline with dates and events.
4. **Blockers** — Lists blockers with `description`, `raised_by`, and `date`.
5. **Decisions** — Lists key decisions with `description`, `made_by`, and `date`.

## States

- **Not yet deep-dived**: Shows a prompt to run deep-dive on this task. Includes a "Run Deep Dive" button.
- **Loading**: Shows a spinner during deep-dive API call.
- **Loaded**: Renders all sections from the deep-dive data.

## Current State

As of June 20, 2026: Deep-dive hasn't been tested yet. The viewer logic is implemented but no real deep-dive data exists in the DB for verification.
