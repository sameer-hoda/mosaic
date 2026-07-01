---
type: Component
title: Header (Header.js)
description: Navigation bar at the top of the app with Dashboard/Groups tabs and category filter sharing.
resource: file://taskdog-frontend/src/components/Header.js
tags: [react, navigation]
---

# Header

The `Header.js` component provides the top navigation bar.

## Elements

- **App title**: "TaskDog"
- **Navigation tabs**: Dashboard (primary), Groups (whitelist view)
- **Category filter**: Shares `activeCategory` state with the app via a custom event (`taskdog:setCategory`)
- **Status indicator**: Shows last synced time from bridge status

## Behavior

- The header is visible on all phases except pairing and API key entry
- Tabs use `setPhase()` to switch the main content area
- Header receives the global `state` object and reads `state.activeCategory` and `state.lastSynced`
- Category changes in the header dispatch a custom DOM event that the dashboard listens to

## Tab Navigation

```javascript
const NAV_TABS = [
  { phase: PHASE.DASHBOARD, label: 'Dashboard' },
  { phase: PHASE.WHITELIST,  label: 'Groups' },
];
```
