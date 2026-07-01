# taskdog-app

This folder is the new home for everything that turns the existing
three-process TaskDog stack into a single Apple-Silicon `.dmg` that a
non-developer can install and run on macOS.

**Start here:** [`DISTRIBUTION_PLAN.md`](./DISTRIBUTION_PLAN.md) — the
locked spec, including the file-by-file change list, the SwiftUI shell
contracts, the API-key flow, the build scripts, and the ready-to-execute
checklist.

## What's in this folder (when built)

```
taskdog-app/
├── README.md                ← this file
├── DISTRIBUTION_PLAN.md     ← the spec
├── scripts/                 ← build, assemble, dmg
├── TaskDog.xcodeproj/       ← Xcode project for the SwiftUI shell
└── TaskDog/                 ← SwiftUI source
    ├── Info.plist
    ├── TaskDog.entitlements
    └── Sources/             ← App / ProcessManager / Keychain / WebView
```

## What gets put in `Resources/` at build time (not in git)

```
TaskDog/Resources/
├── ui/                ← built from taskdog-frontend/  (Vite)
├── bridge/wa-bridge   ← copied from whatsapp-mcp/whatsapp-bridge/
└── backend/TaskDogBackend ← built from taskdog-backend/  (PyInstaller)
```

## Build & ship

```bash
cd taskdog-app
./scripts/build_backend.sh
./scripts/build_frontend.sh
./scripts/assemble_app.sh
./scripts/make_dmg.sh
# → TaskDog-1.0.0-arm64.dmg
```

The DMG is ad-hoc codesigned. Recipients will need to right-click → Open
the first time, or `xattr -dr com.apple.quarantine /Applications/TaskDog.app`.
Notarization is a v1.1 concern.

## Out of scope

See §10 of `DISTRIBUTION_PLAN.md`. The folders outside `taskdog-backend/`,
`taskdog-frontend/`, and the new `taskdog-app/` are not touched by the
DMG build.
