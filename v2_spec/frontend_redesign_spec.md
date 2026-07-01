# TaskDog v2 — Frontend Redesign Spec

**Status:** Spec for AI-assisted build  
**Date:** Sat Jun 20, 2026  
**Goal:** Replace the current basic dashboard with a polished, minimalistic, data-dense task tracker UI.

---

## 1. What Exists vs. What's New

### What's staying (reused as-is)
- **Onboarding flow** — 3 gates (ApiKey → Bridge pairing → Group whitelist) already works, does not change.
- **`api.js`** — All 12 v2 endpoint functions + `_streamSSE()` helper are implemented and working.
- **`app.js` phase router** — Handles APIKEY → PAIRING → WHITELIST → DASHBOARD routing. No changes needed.
- **Pipeline buttons** — Discover and Refresh trigger SSE streaming; deep-dive triggers single-task analysis. The API calls work.
- **Header.js** — Top bar with title, nav tabs, bridge status. Keep but restyle.

### What's new (building from scratch)
The **Dashboard phase** is rebuilt. The current `Dashboard.js` is functional but plain. The new design is a card-based task tracker grouped by WhatsApp group, with rich visual hierarchy, priority-based styling, and a detail modal.

---

## 2. Data Available (What the Backend Sends)

Every piece of UI must map to real data from these endpoints. Do NOT invent fields.

### `GET /api/dashboard` — Main data feed

**Request:** (optional `?group_jid=...` filter)  
**Response shape:**

```json
{
  "tasks": [
    {
      "id": "10fcd89b-5ef7-48c3-bbb9-1f5f16cc4128",
      "group_jid": "120363409785935773@g.us",
      "group_name": "Bio auth <> edu",
      "title": "Define cohort for low propensity education model",
      "status": "active",
      "importance": 5,
      "assignee": "13743945691279@lid",
      "context": "Need to define...",
      "has_deep_dive": false,
      "latest_progress": null,
      "days_since_refresh": 14,
      "created_at": "2026-06-20 08:23:23"
    }
  ],
  "stats": {
    "total": 13,
    "active": 13,
    "completed": 0,
    "archived": 0,
    "importance_5": 5,
    "importance_4": 5,
    "importance_3": 2,
    "importance_2": 1,
    "importance_1": 0
  }
}
```

**Key fields per task card:**
| Field | Type | Description |
|---|---|---|
| `id` | UUID string | Unique task ID |
| `group_jid` | string | WhatsApp group identifier |
| `group_name` | string | Human-readable group name |
| `title` | string | Task title (1-line summary) |
| `status` | `active` / `completed` / `archived` | Current state |
| `importance` | integer 1–5 | AI-assessed, user-overridable |
| `assignee` | string | Person assigned (may be a JID like `13743945691279@lid` or a name) |
| `context` | string | Short description of what the task is about |
| `has_deep_dive` | boolean | Whether wiki/people/etc exist |
| `latest_progress` | string or null | Most recent progress note from refresh |
| `days_since_refresh` | integer | Days since last pipeline refresh |
| `created_at` | ISO timestamp | When task was discovered |

### `GET /api/tasks/{id}` — Full task detail (for the modal)

All dashboard fields PLUS deep-dive fields:

| Field | Type | Description |
|---|---|---|
| `wiki` | Markdown string | Full knowledge page (4-6 paragraphs) |
| `people` | JSON array | `[{name, role}]` — people involved |
| `progress_log` | JSON array | `[{date, event, source}]` — timeline entries |
| `blockers` | JSON array | `[{description, status (open/resolved), raised_by, date}]` |
| `decisions` | JSON array | `[{description, decided_by, date}]` |

### `GET /api/tasks/{id}/messages` — Evidence trail (for the modal)

```json
{
  "messages": [
    {
      "id": 1,
      "message_content": "@141613795922153 How do we solve this?",
      "sender_name": "272318140051549@lid",
      "message_time": "2026-06-05 13:17:55+05:30",
      "relevance": "high"
    }
  ]
}
```

### `GET /api/groups` — Group list with task counts

```json
{
  "groups": [
    {
      "jid": "120363409785935773@g.us",
      "name": "Bio auth <> edu",
      "category": "Work",
      "task_count": 2,
      "active_count": 2
    }
  ]
}
```

### `PATCH /api/tasks/{id}` — Update task (status/importance)

Accepts `{"status": "completed"}` or `{"importance": 4}` or both.

---

## 3. Real Current Data (For Reference)

These are the actual 13 tasks in the database. Use these for realistic mockup proportions and grouping.

### Groups and their tasks (sorted by importance within group):

**Product Team Invoice Payouts** (Work) — 3 tasks:
- Importance 5: "Process pending Mastercard and Visa invoices"
- Importance 5: "Confirm impact of tokenization costs on future budget"
- Importance 4: "Finalize Applus invoice uploads to Zapro"

**Comms way of working** (Work) — 2 tasks:
- Importance 5: "Finalize June communications budget plan"
- Importance 4: "Resolve Lending communications budget discrepancy"

**Bio auth <> edu** (Work) — 2 tasks:
- Importance 5: "Define cohort for low propensity education model"
- Importance 4: "Share data on low propensity education cohort"

**Alert on comms** (Work) — 1 task:
- Importance 4: "Implement daily report delivery via WhatsApp"

**Founder's office x growth threads** (Work) — 1 task:
- Importance 4: "Review and provide feedback on growth thread"

**Loss in ₹₹ due to ops errors / delays** (Work) — 1 task:
- Importance 5: "Achieve zero operational loss for June"

**AD-tech revenue from BFSI** (Work) — 1 task:
- Importance 3: "Check with RA on Visa card dormant base identification"

**Arnav Anand** (Personal) — 1 task:
- Importance 3: "Coordinate Ironman 70.3 participation with RH"

**Pensioners** (Work) — 0 tasks (group whitelisted but no tasks discovered)

**Ayesha** (Personal) — 1 task:
- Importance 2: "Retrieve Shrikanth Sreeram's phone number"

### Stats:
- 13 total, 13 active, 0 completed, 0 archived
- By importance: 5× Imp-5, 5× Imp-4, 2× Imp-3, 1× Imp-2, 0× Imp-1
- 72 tagged messages across all tasks
- 0 deep-dives performed (no wiki data yet)

---

## 4. New UI Design — Dashboard Page

### 4.1 Overall Layout

A single scrollable page. No tabs, no complex navigation. Everything lives on one surface.

```
┌─────────────────────────────────────────────────┐
│  HEADER: TaskDog | [Groups] [Dashboard]   ⚙️    │
├─────────────────────────────────────────────────┤
│  STATS ROW: 13 Tasks · 5 Critical · 0 Blocked   │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─ GROUP: Product Team Invoice Payouts ──────┐ │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐    │ │
│  │ │ CARD     │ │ CARD     │ │ CARD     │    │ │
│  │ │ Imp 5    │ │ Imp 5    │ │ Imp 4    │    │ │
│  │ └──────────┘ └──────────┘ └──────────┘    │ │
│  └─────────────────────────────────────────────┘ │
│                                                 │
│  ┌─ GROUP: Comms way of working ──────────────┐ │
│  │ ┌──────────┐ ┌──────────┐                  │ │
│  │ │ CARD     │ │ CARD     │                  │ │
│  │ └──────────┘ └──────────┘                  │ │
│  └─────────────────────────────────────────────┘ │
│                                                 │
│  ... more groups ...                            │
│                                                 │
│  ┌─ GROUP: Pensioners ────────────────────────┐ │
│  │  No active tasks                           │ │
│  └─────────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Key layout principles:**
- Groups with tasks first (sorted by: has highest-importance tasks → most tasks → alphabetical)
- Groups with 0 tasks at the bottom, collapsed by default
- Cards flow horizontally within each group section, wrapping naturally
- Mobile: cards stack vertically

### 4.2 Stats Row

A thin bar below the header. Minimal, numbers-only, no heavy charts.

```
13 Tasks  ·  5 Critical  ·  3 Deep-dived  ·  Last refreshed 2h ago
```

Or condensed to just key metrics. Use small muted text. The stats row is from `stats` in the dashboard response.

Include a subtle **"Discover Tasks"** and **"Refresh"** button pair on the right side. Small, outlined, low prominence. When clicked, show SSE progress in a small toast or collapsing progress bar (not a full blocking modal — keep the page usable).

### 4.3 Group Sections

Each group gets a section header:

```
Product Team Invoice Payouts                   3 tasks ▸
```

- Group name in a clean, slightly larger font
- Task count on the right
- Clicking the header collapses/expands the group's cards
- Section has a subtle left-border accent color (same for all work groups, different for personal)

### 4.4 Task Cards — The Core UI Element

Each card is a rectangle (~280px × 200px on desktop, full width on mobile).

**Card structure:**

```
┌──────────────────────────────────┐
│  🔴 Imp 5                    ⚡  │  ← top row: importance dot + action icon
│                                  │
│  Process pending Mastercard      │  ← title (1-2 lines, bold)
│  and Visa invoices               │
│                                  │
│  Need to process pending invoices│  ← context (2 lines max, muted)
│  for Mastercard and Visa...      │
│                                  │
│  👤 Arnav A.    📅 Jun 5         │  ← bottom metadata: assignee + date
│  💬 6 messages     Deep dive →   │  ← message count + deep-dive link
└──────────────────────────────────┘
```

**Card data mapping:**

| Card element | Data source |
|---|---|
| Importance dot + gradient | `importance` (1-5) |
| Title | `title` |
| Context preview | `context` (truncated to ~120 chars) |
| Assignee | `assignee` (if it's a JID like `1374...@lid`, use the first name or show as "Unknown"; if it's a name, show as-is) |
| Date | `created_at` formatted as "Jun 5" |
| Message count | Fetch via `GET /api/tasks/{id}/messages` and count, OR show from `task_messages` count (backend doesn't currently include count in dashboard response — either batch fetch on load or add a `message_count` field to dashboard response — **recommend adding to backend**) |
| Deep-dive status | `has_deep_dive` — if true, show "View wiki →" ; if false, show "Analyze →" |
| Status indicator | `status` — active: subtle pulse, completed: checkmark, archived: greyed out |

### 4.5 Priority-Based Card Styling

This is the visual heart of the design. Cards should feel alive and scannable.

**Imp 5 (Critical) — Reddish Gradient with Floating Animation:**
- Background: subtle linear gradient from `#fff5f5` to `#ffe0e0` or similar warm red/pink
- Left border: 3px solid red/crimson (`#ef4444`)
- Floating animation: subtle vertical float (translateY ±4px, 3s ease-in-out infinite). Very gentle, not distracting.
- Top-right corner: a small pulsing dot (red, `animate-pulse`)
- Slight elevation: `box-shadow: 0 4px 12px rgba(239, 68, 68, 0.12)`

**Imp 4 (High) — Amber/Orange Gradient:**
- Background: gradient from `#fffbf0` to `#ffedd5`
- Left border: 3px solid amber (`#f59e0b`)
- No float animation, but a subtle shimmer on hover
- Top-right dot: amber

**Imp 3 (Medium) — Blue/Cool Gradient:**
- Background: gradient from `#f0f9ff` to `#e0f2fe`
- Left border: 3px solid blue (`#3b82f6`)
- Standard card, no animation

**Imp 2 (Low) — Slate/Grey:**
- Background: gradient from `#f8fafc` to `#f1f5f9`
- Left border: 3px solid slate (`#64748b`)
- Muted, lower visual weight

**Imp 1 (Trivial) — Very muted, almost greyed out**

**Completed tasks:** Replace left accent with green (`#22c55e`), slightly desaturated card. No urgency cues.

**Archived tasks:** Greyscale filter, lower opacity, moved to bottom.

**Animation notes:**
- The Imp 5 float animation should be a CSS keyframe animation, no JS animation library needed
- On hover, all cards lift slightly (translateY(-2px), enhanced shadow, 200ms ease)
- Cards should have `border-radius: 12px` for a modern soft look
- Transitions: all 200ms ease for status changes, hover effects

### 4.6 Empty State (Per Group)

When a group has 0 active tasks:

```
Pensioners
  No active tasks. All clear!
```

Minimal, positive, not an error state. Grey text on a very light background.

---

## 5. Task Detail Modal

When a user clicks anywhere on a card, a modal/slide-over opens showing everything.

### 5.1 Modal Layout

A right-side slide-over panel (drawer) or a centered modal. **Recommend: centered modal** (600px–720px wide on desktop, full-screen on mobile) for better readability.

```
┌─────────────────────────────────────────┐
│  ← Back to dashboard                ✕   │
├─────────────────────────────────────────┤
│                                         │
│  🔴 Imp 5 · Active                      │
│                                         │
│  Process pending Mastercard             │
│  and Visa invoices                      │
│                                         │
│  ───────────────────────────────────── │
│                                         │
│  OVERVIEW                               │
│  Need to process pending invoices for   │
│  Mastercard and Visa that have been...  │
│                                         │
│  ───────────────────────────────────── │
│                                         │
│  PEOPLE          ASSIGNEE               │
│  Arnav Anand (Owner)                    │
│  Priya Sharma (Stakeholder)             │
│                                         │
│  ───────────────────────────────────── │
│                                         │
│  TIMELINE                               │
│  Jun 5 — Task identified                │
│  Jun 8 — Invoices sent to finance       │
│  Jun 12 — Awaiting approval             │
│                                         │
│  ───────────────────────────────────── │
│                                         │
│  BLOCKERS                                │
│  ⚠️ Pending vendor confirmation (open)  │
│  ✅ Invoice numbers received (resolved)  │
│                                         │
│  ───────────────────────────────────── │
│                                         │
│  DECISIONS                               │
│  Jun 8 — Use new Zapro flow for uploads │
│                                         │
│  ───────────────────────────────────── │
│                                         │
│  WIKI (DEEP-DIVE)                        │
│  ┌─────────────────────────────────┐   │
│  │  Rendered Markdown content      │   │
│  │  with headings, bullets, quotes │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ───────────────────────────────────── │
│                                         │
│  EVIDENCE (6 messages)                  │
│  ┌─────────────────────────────────┐   │
│  │  Arnav: "Please process these"  │   │
│  │  Jun 5, 2:17 PM                 │   │
│  │  ───────────────────────────── │   │
│  │  Priya: "Sent to finance team"  │   │
│  │  Jun 8, 10:30 AM                │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ───────────────────────────────────── │
│                                         │
│  ACTIONS                                │
│  [Mark Complete]  [Archive]  [Nudge →] │
│  [Run Deep Dive]  [Change Priority ▾]   │
│                                         │
└─────────────────────────────────────────┘
```

### 5.2 Modal Data Mapping

| Section | Data source | Render as |
|---|---|---|
| Title bar | `importance`, `status` | Dot + importance number + status badge |
| Overview | `context` | Paragraph text |
| People | `people` (JSON array from deep-dive) | Name + role list. If null/empty, show only `assignee` as "Assignee" |
| Timeline | `progress_log` (JSON array) | Vertical timeline: date → event. If null/empty, show "Created: {created_at}" as single entry |
| Blockers | `blockers` (JSON array) | List with open/resolved icons. If null/empty, show "No blockers" |
| Decisions | `decisions` (JSON array) | Bulleted list with dates. If null/empty, omit section |
| Wiki | `wiki` (Markdown string) | Rendered Markdown. If null/empty, show "Run Deep Dive to generate a knowledge page" |
| Evidence | `GET /api/tasks/{id}/messages` | Chat-bubble style message list, newest first |
| Actions | N/A (UI controls) | Buttons that call `PATCH` or `POST /api/pipeline/deep-dive` |

### 5.3 Modal States

**State 1: No deep-dive yet** (current reality for all 13 tasks)
- People, Timeline, Blockers, Decisions, Wiki sections are either hidden or show a placeholder
- Wiki section shows: "Run a deep-dive to generate a comprehensive knowledge page for this task" with a prominent "Run Deep Dive" button
- Other deep-dive sections show "Available after deep-dive"

**State 2: Deep-dive in progress**
- The "Run Deep Dive" button turns into a loading spinner
- API call takes 5-20 seconds (synchronous, no SSE)
- Show a skeleton loader or pulsing placeholder blocks

**State 3: Deep-dive complete**
- All sections populate with real data
- Wiki renders as styled Markdown
- Timeline shows day-by-day progress
- People show as avatar cards or name badges

**State 4: Task completed/archived**
- People, Timeline, Blockers, Decisions, Wiki sections still visible (read-only history)
- Actions limited to "Reopen" or "Archive"

### 5.4 Quick Actions (Inline, No Modal Required)

Some actions should work directly from the card without opening the modal:

- **Mark Complete**: A checkmark button on the card (right side). Calls `PATCH /api/tasks/{id}` with `{"status": "completed"}`. Card animates to completed state.
- **Nudge**: Send button calls `POST /api/send` (v1 endpoint). Opens tiny inline confirmation.
- **Deep Dive**: Link text at bottom of card. Opens modal to the "Run Deep Dive" state if not yet done, or directly to wiki if already done.

---

## 6. UI Polish & Micro-interactions

### 6.1 Card Animations
- **Entry animation**: When page loads, cards stagger in from below (translateY(20px) → 0, opacity 0 → 1). Each card delayed by 50ms × its index. Use CSS `@keyframes` or a simple JS staggered render.
- **Status change**: When a card is marked complete, it slides slightly right, fades, then moves to a "Recently Completed" row at the top (auto-disappears after 3 seconds).
- **Hover**: Cards lift 2px, shadow deepens. Smooth 200ms transition.
- **Imp 5 float**: Gentle continuous float as described in 4.5.

### 6.2 Group Expansion
- Click group header to collapse/expand. Cards animate height (max-height transition or similar).
- Chevron icon rotates 90° on expand.

### 6.3 Deep-Dive Progress
- Since deep-dive is synchronous (5-20s), show a progress indicator in the modal
- A pulsing "Analyzing with Gemini..." message with a skeleton layout that fills in as data arrives

### 6.4 Empty Dashboard
- If no groups are whitelisted: redirect to onboarding
- If groups exist but 0 tasks: show a hero message "No tasks discovered yet. Click Discover Tasks to scan your WhatsApp chats." with a large CTA button.

### 6.5 Colors & Typography
- **Background**: Very light grey or off-white (`#fafafa` or `#f8f9fa`)
- **Card backgrounds**: White with the colored left border and subtle top-to-bottom gradient
- **Text**: Dark (`#1a1a2e` or similar), not pure black
- **Font**: System font stack (Inter, SF Pro, Segoe UI). No custom web fonts needed.
- **Border radius**: 12px cards, 8px buttons, 16px modal
- **Shadows**: Layered, subtle. `0 1px 3px rgba(0,0,0,0.08)` for cards, deeper for hover and modal.

---

## 7. Responsive Behavior

- **Desktop (≥1024px)**: Cards in horizontal rows, 3-4 per row within each group section
- **Tablet (768–1023px)**: 2 cards per row
- **Mobile (<768px)**: Single column, full-width cards, modal goes full-screen
- **Stats row**: Wraps into 2 lines on mobile
- **Group headers**: Full width, sticky on mobile when scrolling through that group's cards

---

## 8. Implementation Notes

### 8.1 API Calls
- Use the existing `api.js` functions as-is. The file already exports:
  - `fetchDashboard()`, `fetchTask(taskId)`, `fetchTaskMessages(taskId)`
  - `patchTask(taskId, data)`, `runDeepDive(taskId)`
  - `runDiscover()`, `runDiscoverStream(onEvent)`, `runRefresh()`, `runRefreshStream(onEvent)`
  - `fetchGroups()`, `healthCheck()`, etc.
- Do NOT rewrite `api.js`. Import and use it.

### 8.2 Suggested Backend Enhancement
The `GET /api/dashboard` response does not currently include `message_count` per task or `deep_dive_summary` (a short preview). If you want to avoid N+1 API calls per card render:
- **Option A (recommended)**: Add `message_count` and `wiki_preview` (first 100 chars of wiki) to the dashboard response. Update `routes/dashboard.py` `GET /api/dashboard` to join with task_messages count and wiki substring.
- **Option B**: Batch-fetch message counts on frontend load (fetch all tasks, then one `Promise.all` for messages). Works but slower for large task counts.

### 8.3 Dependencies
- Use the existing project setup. No new packages unless absolutely needed.
- For Markdown rendering in the modal wiki section, use a lightweight library like `marked` or `react-markdown` (check if already in `package.json`, if not, add one).
- For date formatting, use `Intl.DateTimeFormat` or the existing date utilities. No `moment.js`.

### 8.4 Component Structure (Suggested)
```
src/
  components/
    DashboardNew.js        ← Main dashboard page (replaces current Dashboard.js)
    TaskCard.js            ← Individual task card
    TaskModal.js           ← Detail modal/slide-over
    GroupSection.js        ← Group header + card row
    StatsBar.js            ← Top stats row
    PriorityBadge.js       ← Importance dot/badge (reusable)
    DeepDiveSection.js     ← Wiki + people + timeline renderer (replaces DeepDive.js)
    EvidenceTrail.js       ← Message list in modal
    PipelineProgress.js    ← SSE streaming progress indicator
```

### 8.5 State Management
- Keep it simple. React `useState` + `useEffect` is sufficient.
- Dashboard state: `{ tasks, stats, groups, loading, error }`
- Modal state: `{ selectedTask, taskDetail, messages, deepDiveLoading }`
- Group collapse state: `{ collapsedGroups: Set }` or similar
- No Redux or external state library needed for this scope.

### 8.6 What NOT to Change
- `app.js` — the phase router stays
- `api.js` — all exports stay (can add wrapper functions if needed)
- `ApiKey.js`, `Pairing.js`, `Whitelist.js` — onboarding stays untouched
- `Header.js` — update styling but keep structure and functionality
- Backend routes — no changes to API contracts

---

## 9. Visual Reference (Mood Board)

**Design inspiration keywords:**
- Linear.app task list (clean, minimal, colored priority indicators)
- Notion database cards (grouped, scannable)
- Apple Reminders (soft gradients, gentle animations)
- Stripe dashboard (data-dense but airy, strong typography hierarchy)

**What to avoid:**
- Heavy borders or boxed-in layouts
- Bright saturated backgrounds (pastel/washed gradients only for cards)
- Complex data visualizations (charts, graphs) — this is a task list, not an analytics dashboard
- Overly playful animations (bounce, spin, scale) — keep it professional
- Dark mode (for now — light mode only; can be added later)

---

## 10. Acceptance Criteria (For the Builder)

1. Dashboard loads from `GET /api/dashboard` and renders all groups with their tasks
2. Groups are sorted: those with Imp 5 tasks first, then by total task count
3. Each group section shows group name + task count + collapsible card row
4. Task cards show: importance dot, title, context preview, assignee, date, message count
5. Imp 5 cards have reddish gradient + floating animation
6. Imp 4 cards have amber gradient
7. Imp 3 cards have blue gradient
8. Imp 2 cards have slate gradient
9. Completed tasks turn green, archived tasks grey out
10. Clicking a card opens the detail modal
11. Modal shows all available data (overview, people, timeline, blockers, decisions, wiki, evidence)
12. Modal handles both "no deep-dive yet" and "deep-dive complete" states
13. "Mark Complete" and "Nudge" work inline from the card
14. "Run Deep Dive" button in modal triggers the API and shows loading state
15. Discover/Refresh buttons work (SSE progress shown)
16. Empty groups show a neutral empty state
17. 0-tasks-total shows the hero CTA state
18. Responsive: desktop 3-4 cards/row, tablet 2, mobile 1
19. All animations are smooth, no jank or layout shift
20. No changes to onboarding flow or `api.js` exports