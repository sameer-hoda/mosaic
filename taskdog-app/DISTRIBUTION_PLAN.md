# TaskDog — Distribution Plan

This document is the locked specification for turning the current three-process
local stack (Go bridge + Flask backend + Vite frontend) into a single
Apple-Silicon `.dmg` that a non-developer can install and run on macOS without
opening a terminal.

---

## 1. Locked Decisions

| # | Question | Decision |
|---|---|---|
| D1 | Shell framework | **SwiftUI + WKWebView** |
| D2 | API key storage | **macOS Keychain** (user brings their own key) |
| D3 | Go bridge packaging | **Pre-built arm64 binary, bundled verbatim** |
| D4 | Architecture target | **Apple Silicon only (aarch64)** |
| D5 | Code signing | **Ad-hoc sign only, no notarization** |
| D6 | Backend freeze tool | **PyInstaller `--onefile`** |
| D7 | WebView load mode | **`loadFileURL` against `Contents/Resources/ui/`** |
| D8 | First-run flow | **ApiKey → Pairing → Classifier** |
| D9 | "Switch API Key" flow | **Yes — Header menu item** |

If any of these need to change, update this table first, then the affected
sections below.

---

## 2. What ships in the DMG

```
TaskDog-1.0.0-arm64.dmg           ← drag-to-/Applications volume
└── TaskDog.app/                  ← ad-hoc codesigned
    └── Contents/
        ├── MacOS/TaskDog         ← SwiftUI executable
        ├── Resources/
        │   ├── ui/               ← Vite build (dist/) — static
        │   ├── bridge/wa-bridge  ← pre-built arm64 Go binary, verbatim
        │   └── backend/TaskDogBackend ← PyInstaller --onefile Flask binary
        ├── Info.plist
        └── _CodeSignature/       ← ad-hoc signature
```

Total uncompressed size target: **< 60 MB** (Go binary is ~23 MB, PyInstaller
binary ~25 MB, UI ~0.5 MB, shell ~5 MB).

---

## 3. Source-level module structure (proposed)

```
taskdog-app/                          ← NEW top-level folder
├── README.md                          ← pointer doc (see README.md)
├── DISTRIBUTION_PLAN.md               ← this file
├── scripts/
│   ├── build_backend.sh               # PyInstaller --onefile app.py
│   ├── build_frontend.sh              # npm ci && npm run build
│   ├── assemble_app.sh                # xcodebuild + ad-hoc codesign
│   └── make_dmg.sh                    # hdiutil create + codesign DMG
├── TaskDog.xcodeproj                  # Xcode project (or xcodegen spec)
└── TaskDog/                           # SwiftUI source
    ├── Info.plist
    ├── TaskDog.entitlements
    └── Sources/
        ├── App/
        │   ├── TaskDogApp.swift       # @main, single WindowGroup
        │   └── AppDelegate.swift      # child-process lifecycle, dock menu
        ├── ProcessManager/
        │   ├── BridgeProcess.swift    # spawns/kills wa-bridge, watches :8080
        │   ├── BackendProcess.swift   # spawns/kills TaskDogBackend, exports GEMINI_API_KEY
        │   └── Supervisor.swift       # restart on crash, log to ~/Library/Logs/TaskDog/
        ├── Keychain/
        │   ├── KeychainStore.swift    # SecItemAdd / SecItemUpdate
        │   └── KeychainPrompt.swift   # why-we-need-it explainer
        ├── WebView/
        │   ├── MainWebView.swift      # WKWebView, loadFileURL into Resources/ui/
        │   ├── URLSchemeHandler.swift # taskdog:// IPC: save-key, clear-key, goto
        │   └── HealthGate.swift       # GET /api/health → decide first screen
        └── Resources/                 # populated by build scripts (gitignored)
            ├── ui/                    # ← taskdog-frontend/dist/
            ├── bridge/wa-bridge       # ← whatsapp-mcp/whatsapp-bridge/wa-bridge
            └── backend/TaskDogBackend # ← PyInstaller output
```

The SwiftUI shell is intentionally thin. **Only the API-key entry "first run"
gate** is shell-owned. All other screens stay in React.

---

## 4. Backend changes (`taskdog-backend/`)

All additive. No existing files change behavior.

### 4.1 New file: `taskdog-backend/routes/setup.py`

```python
"""
/api/health and /api/setup/api-key — owned by the SwiftUI shell, not the
Flask app's own .env. The shell exports GEMINI_API_KEY into the backend's
process env on every spawn, sourced from the macOS Keychain.
"""
import os
import requests
from flask import Blueprint, request, jsonify

bp = Blueprint("setup", __name__, url_prefix="/api")

GEMINI_LIST_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _preview(key: str) -> str:
    """Return a non-sensitive preview of the key, e.g. 'AIza…xyz'."""
    if not key or len(key) < 8:
        return ""
    return f"{key[:4]}…{key[-3:]}"


@bp.route("/health", methods=["GET"])
def health():
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    return jsonify({
        "ok": True,
        "gemini_key_set": bool(key),
        "gemini_key_preview": _preview(key),
    })


@bp.route("/setup/api-key", methods=["POST"])
def setup_api_key():
    """Validate a candidate key. Does NOT persist; persistence is the shell's job."""
    body = request.get_json(silent=True) or {}
    key = (body.get("key") or "").strip()
    if not key:
        return jsonify({"ok": False, "error": "Empty key"}), 400

    try:
        r = requests.get(GEMINI_LIST_URL, params={"key": key}, timeout=10)
    except requests.RequestException as e:
        return jsonify({"ok": False, "error": f"Network error: {e}"}), 502

    if r.status_code == 200:
        return jsonify({"ok": True, "preview": _preview(key)})
    if r.status_code in (400, 403):
        return jsonify({"ok": False, "error": "Invalid key (rejected by Gemini)"}), 400
    return jsonify({"ok": False, "error": f"Gemini returned {r.status_code}"}), 502


@bp.route("/setup/api-key/clear", methods=["POST"])
def clear_api_key():
    """For the 'Switch API Key' flow. Shell clears the Keychain entry."""
    return jsonify({"ok": True})
```

### 4.2 `taskdog-backend/app.py` — register the blueprint

Add one line inside the existing `app.py`:

```python
from routes.setup import bp as setup_bp
app.register_blueprint(setup_bp)
```

### 4.3 `taskdog-backend/utils/gemini_client.py` — no change

Already reads `os.environ["GEMINI_API_KEY"]`. The shell sets this env var on
every backend spawn, so no code change here.

---

## 5. Frontend changes (`taskdog-frontend/`)

### 5.1 `src/app.js` — add `PHASE.APIKEY` and gate the first screen

```diff
 export const PHASE = {
+  APIKEY: 'apikey',
   PAIRING: 'pairing',
   CLASSIFY: 'classify',
   EXTRACT: 'extract',
   KANBAN: 'kanban',
 };
```

In the `renderApp` function, replace the `api.bridgeStatus()` boot probe with
a health probe that decides the first phase:

```js
api.health().then((res) => {
  if (res && res.gemini_key_set === false) {
    setPhase(PHASE.APIKEY);
  }
  // else fall through to current default (PAIRING)
}).catch(() => { /* keep default */ });
```

### 5.2 `src/api.js` — implement `health()` and `saveApiKey()`

```js
health: () => request('/health'),
saveApiKey: (key) => request('/setup/api-key', {
  method: 'POST',
  body: JSON.stringify({ key }),
}),
```

### 5.3 New file: `src/components/ApiKey.js`

A single centered card. Key behaviors:

- States: `idle` / `validating` / `valid` / `invalid`
- On submit, calls `api.saveApiKey(key)`.
- On `{ok: true}`, posts `window.location = 'taskdog://save-key?value=' + encodeURIComponent(key)`
  to hand the key to the shell (which writes it to Keychain), then
  `setPhase(PHASE.PAIRING)`.
- On `{ok: false}`, shows the backend's `error` string inline.
- A "Where do I get a key?" link opens
  `https://aistudio.google.com/apikey` in the user's default browser.

### 5.4 `src/components/Header.js` — add "Switch API Key"

Add a new button in `topbar-right`, before Logout:

```js
const switchKeyBtn = document.createElement('button');
switchKeyBtn.className = 'topbar-icon';
switchKeyBtn.title = 'Switch API Key';
switchKeyBtn.innerHTML = `<span class="material-symbols-outlined">key</span>`;
switchKeyBtn.addEventListener('click', () => setPhase(PHASE.APIKEY));
right.appendChild(switchKeyBtn);
```

When the user lands on `ApiKey.js` from this button, pre-fill the input with
the current preview if available, but never reveal the full key.

### 5.5 `src/components/Pairing.js` — no change

Becomes phase 2 in the user journey.

---

## 6. SwiftUI shell — contracts

### 6.1 `ProcessManager/BackendProcess.swift`

```swift
import Foundation

final class BackendProcess {
    static let shared = BackendProcess()
    private var proc: Process?

    func start(apiKey: String) throws {
        let bundle = Bundle.main
        let exec   = bundle.url(forAuxiliaryExecutable: "TaskDogBackend")!
        let work   = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("TaskDog", isDirectory: true)
        try? FileManager.default.createDirectory(at: work, withIntermediateDirectories: true)

        let p = Process()
        p.executableURL = exec
        p.arguments = ["--port", "3001"]
        p.environment = [
            "GEMINI_API_KEY": apiKey,
            "TASKDOG_DATA_DIR": work.path,
        ]
        p.currentDirectoryURL = work
        p.standardOutput = FileHandle(forWritingAtPath: logPath("backend.log"))!
        p.standardError  = p.standardOutput
        try p.run()
        proc = p
    }

    func stop() { proc?.terminate(); proc = nil }
}
```

### 6.2 `ProcessManager/BridgeProcess.swift`

Spawns `Contents/Resources/bridge/wa-bridge` with `cwd` =
`Contents/Resources/bridge/store/`. Stdout/stderr to `~/Library/Logs/TaskDog/bridge.log`.

### 6.3 `Keychain/KeychainStore.swift`

```swift
import Security

enum KeychainStore {
    static let service = "com.taskdog.app"
    static let account = "GeminiAPIKey"

    static func save(_ key: String) {
        let data = Data(key.utf8)
        let base: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        SecItemDelete(base as CFDictionary)
        var add = base
        add[kSecValueData as String] = data
        add[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock
        SecItemAdd(add as CFDictionary, nil)
    }

    static func read() -> String? {
        let q: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var item: CFTypeRef?
        guard SecItemCopyMatching(q as CFDictionary, &item) == errSecSuccess,
              let data = item as? Data,
              let s = String(data: data, encoding: .utf8) else { return nil }
        return s
    }

    static func clear() {
        let q: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        SecItemDelete(q as CFDictionary)
    }
}
```

### 6.4 `WebView/MainWebView.swift`

```swift
import WebKit

final class MainWebView: NSObject, WKNavigationDelegate {
    let webView: WKWebView
    private let scheme: URLSchemeHandler

    override init() {
        let cfg = WKWebViewConfiguration
            .with(schemeHandler: URLSchemeHandler(),
                  apiOrigin: "http://127.0.0.1:3001")
        webView = WKWebView(frame: .zero, configuration: cfg)
        super.init()
        webView.navigationDelegate = self
        loadUI()
    }

    private func loadUI() {
        let ui = Bundle.main.url(forResource: "ui/index", withExtension: "html")!
        webView.loadFileURL(ui, allowingReadAccessTo: ui.deletingLastPathComponent())
    }
}
```

`WKWebViewConfiguration.with(schemeHandler:apiOrigin:)` registers:

- A custom scheme `taskdog://` for IPC (see §6.5).
- A `WKURLSchemeHandler` that intercepts `/api/*` and proxies to
  `http://127.0.0.1:3001` using `URLSession`.

### 6.5 `WebView/URLSchemeHandler.swift`

| URL | Direction | Effect |
|---|---|---|
| `taskdog://save-key?value=…` | WebView → Shell | `KeychainStore.save(value)`; restart `BackendProcess`; reply `taskdog://key-saved` |
| `taskdog://clear-key` | WebView → Shell | `KeychainStore.clear()`; restart `BackendProcess` |
| `taskdog://goto/apikey` | Shell → WebView | JS hook `window.dispatchEvent(new CustomEvent('taskdog:goto', {detail:'apikey'}))` |
| `taskdog://goto/pairing` | Shell → WebView | Same shape |
| `taskdog://ready` | WebView → Shell | First WebView load complete; safe to call `HealthGate` |

### 6.6 `WebView/HealthGate.swift`

On shell start and on `taskdog://ready`:

1. Poll `http://127.0.0.1:3001/api/health` every 2 s, up to 30 s.
2. On first success, if `gemini_key_set === false`:
   - `webView.evaluateJavaScript("window.location='taskdog://goto/apikey'")`
3. Else: do nothing (React's own boot logic in `app.js` will show Pairing).
4. If 30 s elapse with no success, show a native SwiftUI overlay
   "Backend not ready, retrying…" with a manual Retry button.

### 6.7 `Info.plist` keys

```xml
<key>CFBundleExecutable</key>          <string>TaskDog</string>
<key>CFBundleIdentifier</key>          <string>com.taskdog.app</string>
<key>CFBundleName</key>                <string>TaskDog</string>
<key>CFBundleDisplayName</key>         <string>TaskDog</string>
<key>CFBundleShortVersionString</key>  <string>1.0.0</string>
<key>CFBundleVersion</key>             <string>1</string>
<key>LSMinimumSystemVersion</key>      <string>13.0</string>
<key>NSHighResolutionCapable</key>     <true/>
<key>NSPrincipalClass</key>            <string>NSApplication</string>
<key>LSUIElement</key>                 <false/>
```

### 6.8 `TaskDog.entitlements`

```xml
<key>com.apple.security.app-sandbox</key> <false/>
<key>com.apple.security.cs.allow-jit</key> <true/>
<key>com.apple.security.cs.allow-unsigned-executable-memory</key> <true/>
<key>com.apple.security.network.client</key> <true/>
```

App sandbox is **off** so the shell can spawn child processes. We are not
distributing through the Mac App Store, so this is acceptable.

---

## 7. Build & DMG scripts

### 7.1 `scripts/build_backend.sh`

```bash
#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APP="$HERE/../TaskDog/Resources"
rm -rf "$APP/backend" && mkdir -p "$APP/backend"

pip install --quiet pyinstaller
pip install --quiet -r "$HERE/../../taskdog-backend/requirements.txt"

pyinstaller --onefile --name TaskDogBackend \
    --distpath "$APP/backend" \
    --workpath "$HERE/../build/pyi" \
    "$HERE/../../taskdog-backend/app.py"
```

### 7.2 `scripts/build_frontend.sh`

```bash
#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APP="$HERE/../TaskDog/Resources"
rm -rf "$APP/ui" && mkdir -p "$APP/ui"

cd "$HERE/../../taskdog-frontend"
npm ci
npm run build
cp -R dist/* "$APP/ui/"
```

### 7.3 `scripts/assemble_app.sh`

```bash
#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/.."

xcodebuild -scheme TaskDog -configuration Release \
    -derivedDataPath build clean build \
    -quiet

rm -rf TaskDog.app
cp -R build/Build/Products/Release/TaskDog.app ./TaskDog.app

cp ../../whatsapp-mcp/whatsapp-bridge/wa-bridge \
   TaskDog.app/Contents/Resources/bridge/wa-bridge
chmod +x TaskDog.app/Contents/Resources/bridge/wa-bridge
chmod +x TaskDog.app/Contents/Resources/backend/TaskDogBackend

codesign --force --deep --sign - TaskDog.app
```

### 7.4 `scripts/make_dmg.sh`

```bash
#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/.."
rm -f TaskDog-1.0.0-arm64.dmg

hdiutil create -volname "TaskDog 1.0.0" \
               -srcfolder TaskDog.app \
               -ov -format UDZO \
               TaskDog-1.0.0-arm64.dmg

codesign --force --sign - TaskDog-1.0.0-arm64.dmg
```

---

## 8. First-run user journey (locked)

1. User double-clicks `TaskDog.app` (or drags from DMG to `/Applications` first).
2. Shell spawns `wa-bridge` (port 8080) and `TaskDogBackend` (port 3001,
   `GEMINI_API_KEY` unset on first run).
3. WebView loads `dist/index.html` from `Contents/Resources/ui/`.
4. `ApiKey.js` shows — user pastes their Gemini key, clicks **Test & Save**.
5. Frontend `POST /api/setup/api-key` → backend validates against
   `generativelanguage.googleapis.com/v1beta/models?key=…` → returns
   `{ok: true, preview}`. Frontend posts
   `taskdog://save-key?value=…` to the shell.
6. Shell writes to Keychain (`kSecClassGenericPassword`, service
   `com.taskdog.app`, account `GeminiAPIKey`), restarts `BackendProcess` so
   the new env takes effect, and replies `taskdog://key-saved`.
7. Frontend calls `setPhase(PHASE.PAIRING)`.
8. `Pairing.js` polls `bridge/status`; shell has already spawned `wa-bridge`
   and is showing the QR in its own log file. User scans it from
   WhatsApp → Settings → Linked Devices on their phone.
9. `Classifier.js` takes over and the rest of the existing flow runs
   unchanged.
10. From any later phase, **Header → "Switch API Key"** returns to
    `ApiKey.js` with the input pre-filled with the preview. On save, shell
    updates Keychain and the supervisor restarts the backend so the new key
    takes effect.

---

## 9. Log & data locations

| What | Where |
|---|---|
| Backend stdout/stderr | `~/Library/Logs/TaskDog/backend.log` |
| Bridge stdout/stderr | `~/Library/Logs/TaskDog/bridge.log` |
| TaskDog data dir | `~/Library/Application Support/TaskDog/` |
| API key (sensitive) | macOS Keychain, service `com.taskdog.app`, account `GeminiAPIKey` |
| Bridge SQLite (whatsapp.db, messages.db) | `Contents/Resources/bridge/store/` (bundled, then per-user) |
| taskdog.db | `~/Library/Application Support/TaskDog/taskdog.db` |

The shell should symlink the bundled `store/` into the user's app-support dir
on first run, so the bridge has a writable, stable location.

---

## 10. Out of scope for v1

- Notarization (D5 — ad-hoc only).
- Intel x86_64 support (D4 — Apple Silicon only).
- Auto-update / Sparkle.
- Codesigning the inner `.app` with a Developer ID.
- Refactoring or moving any of:
  `_archive/`, `notion_integration/macos_app/`, `wa-slash-commands/`,
  `slash_commands/`, `wa_productivity/`, `channel_manager/`,
  `wa_kanban/`, `reports/`, `momentum_update/`, `llm_wiki_sandbox/`,
  `wiki_system/`, `notion_integration/`, `twenty/`, `whatsapp-mcp/` (other
  than reading its `wa-bridge` binary), `all_docs/`, `_secrets/`,
  `slash_cmd_cache/`, `.wheels/`, etc.
- `taskdog-backend/routes/auth.py`, `routes/summary.py`,
  `utils/markdown_parser.py` are stale and can be deleted as a cleanup
  pass but are not required for the DMG build.

---

## 11. Ready-to-execute checklist

- [ ] **A1** — Create `taskdog-backend/routes/setup.py` with the 3 endpoints
- [ ] **A2** — Register the `setup` blueprint in `taskdog-backend/app.py`
- [ ] **A3** — Verify `taskdog-backend/utils/gemini_client.py` still reads
  `os.environ["GEMINI_API_KEY"]` (no change expected)
- [ ] **B1** — Add `PHASE.APIKEY` and first-screen gate in
  `taskdog-frontend/src/app.js`
- [ ] **B2** — Implement `health()` and `saveApiKey()` in
  `taskdog-frontend/src/api.js`
- [ ] **B3** — Create `taskdog-frontend/src/components/ApiKey.js`
- [ ] **B4** — Add "Switch API Key" button to
  `taskdog-frontend/src/components/Header.js`
- [ ] **B5** — Confirm `Pairing.js` needs no change
- [ ] **C1** — Scaffold `taskdog-app/` with Xcode project (or `xcodegen`
  `project.yml`)
- [ ] **C2** — Implement `App/`, `ProcessManager/`, `Keychain/`, `WebView/`
  per §6
- [ ] **C3** — Add `Info.plist` and `TaskDog.entitlements`
- [ ] **D1** — `scripts/build_backend.sh` produces `TaskDogBackend`
- [ ] **D2** — `scripts/build_frontend.sh` refreshes `Resources/ui/`
- [ ] **D3** — `scripts/assemble_app.sh` produces a launchable `TaskDog.app`
- [ ] **D4** — `scripts/make_dmg.sh` produces `TaskDog-1.0.0-arm64.dmg`
- [ ] **E1** — Smoke test on a clean user account: drag from DMG, paste key,
  scan QR, classify, extract, send
- [ ] **E2** — Smoke test the "Switch API Key" flow from the Header

---

## 12. Open risks

| Risk | Mitigation |
|---|---|
| PyInstaller `--onefile` slow first launch (~3 s) | Documented; acceptable for v1 |
| Bridge store DBs shipped in bundle get read-only on macOS 14+ | Symlink `store/` to `~/Library/Application Support/TaskDog/store/` on first run; shell does this in `AppDelegate.applicationDidFinishLaunching` |
| Ad-hoc-signed DMG shows Gatekeeper warning on first open | Document the "right-click → Open" workaround in the DMG's `Read Me.rtf` |
| Keychain prompts the user twice (once for read, once for write) on macOS 14+ | Reuse an existing entry if present; only prompt for the first save |
| `wa-bridge` build is older than the latest whatsmeow | Bundle the most recent binary at build time; see `taskdog-handoff/05_existing_code_inventory.md` for the rebuild procedure if WhatsApp rejects |
