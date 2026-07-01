---
type: Reference
title: Distribution Plan
description: Two production packaging approaches — SwiftUI + WKWebView (primary) and Electron (alternative).
tags: [distribution, swift, electron, production]
---

# Distribution Plan

Two production packaging approaches exist:

## Primary: SwiftUI + WKWebView

The primary packaging plan for TaskDog v2 follows the same approach as v1: a SwiftUI macOS app that wraps the Vite-built frontend in a WKWebView.

**Location**: [`taskdog-app/DISTRIBUTION_PLAN.md`](../../taskdog-app/DISTRIBUTION_PLAN.md)

**Key Points**:
- The Vite frontend is built with `npx vite build` — output goes to `taskdog-frontend/dist/`
- A SwiftUI shell loads the built HTML/JS/CSS into a WKWebView
- Flask backend is frozen via PyInstaller `--onefile` into a binary
- The Go bridge is bundled as a pre-built arm64 binary
- All three tiers packaged into a single `.app` bundle
- API key stored in macOS Keychain
- Apple Silicon only (aarch64), ad-hoc signed, no notarization

## Alternative: Electron

An Electron-based packaging exists at [`deployment/taskdog-electron/`](../../deployment/taskdog-electron/).

**Key Points**:
- Cross-platform (not limited to Apple Silicon)
- The Vite frontend is loaded inside an Electron BrowserWindow
- Backend and bridge are bundled as subprocesses
- Node.js main process manages lifecycle of subprocesses

## Current Status

The distribution plan docs are valid starting points but may need updating to reflect the v2 file structure. This update is a TODO.
