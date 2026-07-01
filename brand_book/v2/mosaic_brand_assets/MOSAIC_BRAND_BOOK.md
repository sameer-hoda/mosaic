# Mosaic Brand Book

**Version:** 1.0  
**Direction finalized:** Mosaic M  
**Product:** A life-organizing layer that turns WhatsApp conversations into commitments, decisions, blockers, and next steps.

---

## 1. Brand Summary

### Brand name

**Mosaic**

### Master tagline

**Your life, pieced together.**

### One-line objective

**Organize your life automatically from your WhatsApp conversations.**

### Brand promise

Mosaic turns scattered WhatsApp conversations into a clear picture of what matters — surfacing commitments, decisions, blockers, and next steps automatically.

### Core metaphor

Every conversation contains fragments. A message, a voice note, a promise, a decision, a blocker, a follow-up — each is a small tile. Alone, each tile is noisy and incomplete. Mosaic assembles those fragments into a clear picture.

### What the brand should feel like

- Clear, not clever for its own sake.
- Calm, not hyper-productive.
- Intelligent, but invisible.
- Personal, not corporate.
- Premium, but not cold.
- App-first, scalable, and instantly recognizable.

---

## 2. Strategic Positioning

### What Mosaic is

Mosaic is a **life organizing layer** that sits on top of WhatsApp. It reads the chaos of daily conversations — group chats, work threads, personal DMs, random voice notes — and surfaces what actually matters.

It helps the user see:

- What they committed to.
- What others committed to.
- What decisions were taken.
- What is blocked.
- What needs follow-up.
- What is happening next.

### What Mosaic is not

Mosaic is not:

- A task manager.
- A project management tool.
- A CRM.
- A notes app.
- A habit tracker.
- A manual productivity system.

The user should never feel like they are maintaining another system. The system should feel like it is maintaining itself.

### Core product belief

Your life is already inside WhatsApp. The problem is not that you are disorganized. The problem is that the organization is buried across thousands of messages. Mosaic finds the pattern and shows the picture.

### Positioning line

**Mosaic is the invisible organizer for your WhatsApp life.**

---

## 3. Brand Essence

| Attribute | Meaning |
|---|---|
| **Clear** | We cut through noise and show what matters. |
| **Composed** | We bring calm structure to messy conversations. |
| **Intelligent** | We understand context, not just keywords. |
| **Effortless** | The user does not create tasks; tasks discover themselves. |
| **Human** | We support real life, real people, and real commitments. |

---

## 4. Final Logo Direction

### Selected direction

**The Mosaic M**

The primary logo is a geometric **M** built from rounded mosaic tiles. It communicates the central brand story: scattered fragments coming together into a recognizable picture.

### Why this direction wins

1. **Ownable**  
   A tile-built M is more distinctive than a generic chat bubble or checklist.

2. **Scalable**  
   It works as an app icon, favicon, dashboard logo, social avatar, and presentation mark.

3. **Metaphorical**  
   It tells the Mosaic story without needing explanation.

4. **Premium**  
   The mark feels modern and structured, not playful or childish.

5. **Flexible**  
   It can be used as a solid mark, outline mark, app icon, tile pattern, loading animation, and illustration system.

### Logo files included

- `mosaic-logo-mark.svg` — transparent vector mark.
- `mosaic-logo-final.svg` — horizontal logo with wordmark.
- `mosaic-app-icon.svg` — app icon / launcher icon direction.
- `favicon.svg` — browser favicon.
- `favicon.ico` — browser favicon for broad compatibility.
- PNG versions for quick preview and implementation.

---

## 5. Logo System

### Primary logo

Use the full horizontal lockup when space allows:

**[Mosaic M mark] Mosaic**

Recommended use cases:

- Website header.
- Landing page hero.
- Login screen.
- Product dashboard sidebar.
- Pitch decks.
- Social banners.

### Logo mark

Use the standalone Mosaic M when space is constrained.

Recommended use cases:

- Favicon.
- App icon.
- Mobile navigation.
- Dashboard collapsed sidebar.
- Social avatar.
- Loading state.

### App icon

The app icon uses a violet rounded-square background with the white Mosaic M centered inside it.

Use this for:

- Mobile home screen.
- PWA icon.
- App launcher.
- Social profile image when the full wordmark is not needed.

### Monochrome logo

Use monochrome dark on light backgrounds and monochrome light on dark backgrounds.

Recommended colors:

- Dark mark: `#15163A`
- Light mark: `#FFFFFF`
- Subtle light mark: `#E5E7EB`

### Clear space

Maintain clear space around the logo equal to the height of one tile from the Mosaic M.

Rule:

```text
Minimum clear space = 1 tile height on all sides
```

Do not place text, icons, borders, or other visual elements inside this area.

### Minimum size

| Use case | Minimum size |
|---|---:|
| Digital logo mark | 20px wide |
| Digital horizontal logo | 96px wide |
| Print logo mark | 6mm wide |
| App icon | 32px minimum, 1024px source |

### Logo misuse

Do not:

- Stretch or distort the logo.
- Rotate the logo.
- Add heavy shadows, outlines, bevels, or 3D effects.
- Change tile spacing.
- Recolor individual tiles randomly.
- Place the logo on low-contrast backgrounds.
- Use a WhatsApp logo or WhatsApp green as the dominant brand mark.

---

## 6. Color System

### Primary colors

| Token | Hex | Usage |
|---|---|---|
| `brand.violet` | `#5B21FF` | Primary actions, logo, active states, focus elements. |
| `brand.violet.light` | `#8B5CF6` | Gradient start, highlights, hover states. |
| `brand.ink` | `#15163A` | Primary text, icons, high-contrast base. |
| `brand.neutral` | `#F3F4F6` | Light backgrounds, surfaces, subtle dividers. |
| `brand.white` | `#FFFFFF` | Cards, app surfaces, logo grout lines. |

### Accent colors

| Token | Hex | Usage |
|---|---|---|
| `accent.green` | `#22C55E` | Success, completion, confirmations, positive status. |
| `accent.amber` | `#F59E0B` | Attention, pending state, important info. |
| `accent.teal` | `#14B8A6` | Calm secondary accent, source chips, trust moments. |
| `accent.coral` | `#FF6B6B` | Alerts, overdue, critical states. |

### Primary gradient

Use this gradient for logo fills, hero moments, and elevated UI surfaces.

```css
background: linear-gradient(135deg, #8B5CF6 0%, #5B21FF 100%);
```

### Color usage rules

- Violet should own the brand.
- Green should be used sparingly to hint at WhatsApp and completion, not to copy WhatsApp.
- Accent colors should appear as small “tiles,” chips, badges, or state indicators.
- Avoid rainbow usage. Mosaic can have many pieces without becoming visually noisy.
- Keep most surfaces white or near-white; reserve rich color for meaning.

### Suggested semantic tokens

```css
:root {
  --mosaic-violet: #5B21FF;
  --mosaic-violet-light: #8B5CF6;
  --mosaic-ink: #15163A;
  --mosaic-neutral: #F3F4F6;
  --mosaic-white: #FFFFFF;

  --mosaic-success: #22C55E;
  --mosaic-warning: #F59E0B;
  --mosaic-calm: #14B8A6;
  --mosaic-danger: #FF6B6B;

  --mosaic-gradient: linear-gradient(135deg, #8B5CF6 0%, #5B21FF 100%);
}
```

---

## 7. Typography

### Recommended type direction

Use a modern geometric sans-serif that feels clean, premium, and digital.

Preferred:

- **Satoshi** for display and body.

Fallback stack:

```css
font-family: Satoshi, Inter, Avenir Next, Helvetica Neue, Arial, sans-serif;
```

### Type scale

| Style | Size / Line height | Weight | Usage |
|---|---:|---:|---|
| H1 | 56 / 64 | 800 | Landing page hero, major product statements. |
| H2 | 36 / 44 | 700 | Section headers, dashboard titles. |
| H3 | 24 / 32 | 600 | Card titles, feature blocks. |
| Body | 16 / 24 | 400 | Standard paragraph and UI copy. |
| Body small | 14 / 20 | 400 | Metadata, descriptions. |
| Caption | 12 / 16 | 400 | Labels, timestamps, helper text. |

### Typography rules

- Use short lines and generous spacing.
- Avoid dense productivity-tool copy.
- Prefer sentence case over title case in UI.
- Use bold sparingly for emphasis.
- Let whitespace do the work.

---

## 8. Visual Language

### Core visual building block

The core visual building block is the **rounded tile**.

Tiles can represent:

- Messages.
- Tasks.
- Commitments.
- Decisions.
- Blockers.
- People.
- Sources.
- Fragments of a larger picture.

### Tile style

Recommended tile rules:

```css
.tile {
  border-radius: 12px;
  background: var(--mosaic-gradient);
}
```

Use tiles in:

- Logo mark.
- Background patterns.
- Loading states.
- Empty states.
- Onboarding illustrations.
- Dashboard modules.
- Category chips.

### Grout lines

The negative space between tiles is part of the identity. It represents separation, structure, and clarity.

Rules:

- Keep tile gaps consistent.
- Use white or background-colored gaps.
- Do not overcrowd the composition.
- Fewer, larger tiles are better than many tiny tiles.

### Illustration style

Illustrations should show fragments assembling into clarity.

Useful patterns:

- Scattered tiles becoming the Mosaic M.
- Chat bubbles breaking into tiles.
- Tiles snapping into a grid.
- A messy conversation becoming a clean list.
- A missing tile completing a picture.

Avoid:

- Cartoon mascots.
- Overly literal WhatsApp clones.
- Generic productivity illustrations.
- Busy dashboards with too many colors.

### Motion principle

**Pieces come together.**

Motion should feel calm and inevitable, not flashy.

Suggested motion pattern:

1. Tiles float in softly.
2. Tiles align to a grid.
3. The Mosaic M forms.
4. A clear task or decision appears.

Timing:

- Fast enough to feel intelligent.
- Slow enough to feel composed.
- Recommended duration: 400–900ms.

---

## 9. Product UI Direction

### Product experience statement

**Scattered chats become a clear picture.**

### Dashboard language

Avoid generic task-manager language where possible.

Recommended language:

| Generic | Mosaic alternative |
|---|---|
| Inbox | Pieces |
| Tasks | Next steps |
| Projects | Pictures / Areas |
| Activity | Conversation signals |
| Summary | Clear picture |
| AI detected | Found in conversation |
| Create task | Add to my day |
| Mark complete | Piece resolved |

Use selectively. Do not over-metaphorize the product to the point where it becomes confusing.

### Core navigation

Recommended nav labels:

- Home
- Next steps
- Commitments
- Decisions
- Blockers
- Sources
- Insights

### Card design

Task/action cards should feel like clean tiles.

Recommended card structure:

```text
[Source icon] Title                         [Type chip]
Context / source line
Due time or status                          People involved
```

Example:

```text
Send deck to Riya                           Task
Found in Work Chat · Today 9:00 AM          You
```

### Chips

Use chips to distinguish item type:

| Chip | Suggested color |
|---|---|
| Task | Violet |
| Commitment | Blue / Teal |
| Decision | Purple / Lavender |
| Blocker | Coral |
| Waiting | Amber |
| Completed | Green |

### Empty state copy

```text
Mosaic is reading the pieces.
Your next steps will appear here as conversations unfold.
```

Alternative:

```text
No loose pieces right now.
When a conversation creates a commitment, decision, or follow-up, Mosaic will surface it here.
```

### Loading copy

```text
Finding the picture inside your chats…
```

### Confirmation copy

```text
Added to your day.
```

```text
This piece is resolved.
```

---

## 10. Voice and Tone

### Voice principles

#### Clear

We say what matters without making the user decode product language.

Example:

```text
You have 5 commitments waiting for a response.
```

Avoid:

```text
AI has detected unresolved entities in your conversational graph.
```

#### Composed

We do not create panic. We help the user feel in control.

Example:

```text
Three items may need your attention today.
```

Avoid:

```text
Urgent! You are falling behind.
```

#### Intelligent

We explain the reasoning when useful.

Example:

```text
Marked as a commitment because you said “I’ll send this tonight.”
```

#### Effortless

We minimize user work.

Example:

```text
We found this in your Family chat and added the context automatically.
```

#### Human

We write like a helpful assistant, not enterprise software.

Example:

```text
Looks like this is waiting on Rahul.
```

Avoid:

```text
Ownership appears to be externally dependent.
```

### Writing style

- Short sentences.
- Calm confidence.
- No hype.
- No corporate jargon.
- No exaggerated AI claims.
- Explain only when it helps trust.

### Words to use

- Clear
- Pieces
- Picture
- Conversation
- Found
- Organized
- Next steps
- Commitments
- Decisions
- Blockers
- Context
- Resolved

### Words to avoid

- Productivity hack
- Supercharge
- 10x
- Workflow automation platform
- Conversational intelligence fabric
- AI-powered everything
- Synergy
- Pipeline
- Sprint

---

## 11. Tagline and Messaging System

### Master tagline

**Your life, pieced together.**

### Supporting lines

- **Scattered chats become a clear picture.**
- **From conversation to clarity.**
- **The picture inside your chats.**
- **All the pieces, finally in place.**
- **Your chats already know. Mosaic helps you see.**

### Landing page hero options

#### Option A — Most emotional

```text
Your life, pieced together.

Mosaic turns scattered WhatsApp conversations into organized next steps, commitments, and decisions — so nothing slips through.
```

#### Option B — Most product-clear

```text
Scattered chats become a clear picture.

Mosaic automatically finds commitments, decisions, blockers, and follow-ups from your WhatsApp conversations.
```

#### Option C — Most premium

```text
From conversation to clarity.

Mosaic quietly organizes what matters from the chats that run your life.
```

### Onboarding flow copy

#### Step 1: Capture

```text
Connect your conversations.
Mosaic reads your chats with care and finds the pieces that matter.
```

#### Step 2: Organize

```text
See what matters.
Tasks, commitments, decisions, and blockers are grouped automatically.
```

#### Step 3: Connect

```text
Keep the context.
Every item stays linked to the people, dates, and messages behind it.
```

#### Step 4: Clarity

```text
Move forward clearly.
Know what is on your plate, what is waiting, and what happens next.
```

---

## 12. Marketing Applications

### Website hero

Use a large Mosaic M on the right, with soft tile patterns behind it.

Recommended hero:

```text
Your life, pieced together.

Mosaic turns scattered WhatsApp conversations into organized next steps, commitments, and decisions — so life stays clear and nothing slips through.
```

CTA options:

- Get started
- See how it works
- Connect WhatsApp
- View your picture

### Social post template

Headline:

```text
See the whole picture.
```

Subtext:

```text
From conversation to clarity.
```

Visual:

- Large text on left.
- Soft mosaic tile pattern on right.
- Small Mosaic mark top-left.

### Presentation title slide

```text
From conversation to clarity.

Product overview
```

### Sticker / badge lines

- See the whole picture.
- From conversation to clarity.
- Your life, pieced together.
- All pieces in place.
- Found in conversation.

---

## 13. Implementation Snippets

### HTML favicon setup

```html
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/mosaic-app-icon.png">
```

### CSS brand tokens

```css
:root {
  --mosaic-violet: #5B21FF;
  --mosaic-violet-light: #8B5CF6;
  --mosaic-ink: #15163A;
  --mosaic-neutral: #F3F4F6;
  --mosaic-white: #FFFFFF;
  --mosaic-success: #22C55E;
  --mosaic-warning: #F59E0B;
  --mosaic-calm: #14B8A6;
  --mosaic-danger: #FF6B6B;
  --mosaic-gradient: linear-gradient(135deg, #8B5CF6 0%, #5B21FF 100%);

  --radius-tile: 12px;
  --radius-card: 16px;
  --radius-panel: 24px;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
}
```

### React logo usage

```jsx
<img src="/mosaic-logo-final.svg" alt="Mosaic" width="140" height="32" />
```

### React favicon/app mark usage

```jsx
<img src="/mosaic-logo-mark.svg" alt="" aria-hidden="true" className="h-8 w-8" />
```

---

## 14. Designer / LLM Prompt

Use this prompt when asking an LLM, designer, or design agent to apply the brand.

```text
Apply the Mosaic brand system to this product interface.

Brand context:
Mosaic organizes your life automatically from WhatsApp conversations. It turns scattered chats into a clear picture of commitments, decisions, blockers, and next steps.

Brand metaphor:
Every message is a tile. Mosaic assembles the pieces into a clear picture.

Visual direction:
Use the finalized Mosaic M logo direction: a geometric M built from rounded tiles. The brand should feel clear, composed, intelligent, effortless, and human.

Color system:
Primary violet #5B21FF, violet-light #8B5CF6, ink #15163A, neutral #F3F4F6, white #FFFFFF. Use green #22C55E sparingly for success/completion, amber #F59E0B for waiting/attention, teal #14B8A6 for calm/source states, coral #FF6B6B for blockers/overdue.

Typography:
Use Satoshi if available, otherwise Inter or a clean geometric sans-serif. Use strong H1s, generous spacing, and short clear sentences.

UI style:
Clean white cards, rounded corners, subtle dividers, generous whitespace, tile-inspired chips and modules. Avoid generic task-manager visuals, heavy shadows, clutter, or excessive gradients.

Voice:
Clear, calm, human. No hype, no corporate jargon. Use phrases like “Scattered chats become a clear picture,” “Found in conversation,” and “Your life, pieced together.”
```

---

## 15. Final Brand Decision

The finalized direction is:

```text
Name: Mosaic
Logo: Mosaic M built from rounded tiles
Tagline: Your life, pieced together.
Primary color: Violet #5B21FF
Accent philosophy: Small colored tiles, not rainbow branding
Core message: Scattered chats become a clear picture.
```

This direction should be used consistently across product, landing page, favicon, app icon, decks, and marketing material.
