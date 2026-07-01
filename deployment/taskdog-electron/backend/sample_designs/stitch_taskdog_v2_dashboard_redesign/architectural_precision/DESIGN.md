---
name: Architectural Precision
colors:
  surface: '#131315'
  surface-dim: '#131315'
  surface-bright: '#39393b'
  surface-container-lowest: '#0e0e10'
  surface-container-low: '#1c1b1d'
  surface-container: '#201f22'
  surface-container-high: '#2a2a2c'
  surface-container-highest: '#353437'
  on-surface: '#e5e1e4'
  on-surface-variant: '#ccc3d8'
  inverse-surface: '#e5e1e4'
  inverse-on-surface: '#313032'
  outline: '#958da1'
  outline-variant: '#4a4455'
  surface-tint: '#d2bbff'
  primary: '#d2bbff'
  on-primary: '#3f008e'
  primary-container: '#7c3aed'
  on-primary-container: '#ede0ff'
  inverse-primary: '#732ee4'
  secondary: '#c0c1ff'
  on-secondary: '#1000a9'
  secondary-container: '#3131c0'
  on-secondary-container: '#b0b2ff'
  tertiary: '#4edea3'
  on-tertiary: '#003824'
  tertiary-container: '#007650'
  on-tertiary-container: '#76ffc2'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#eaddff'
  primary-fixed-dim: '#d2bbff'
  on-primary-fixed: '#25005a'
  on-primary-fixed-variant: '#5a00c6'
  secondary-fixed: '#e1e0ff'
  secondary-fixed-dim: '#c0c1ff'
  on-secondary-fixed: '#07006c'
  on-secondary-fixed-variant: '#2f2ebe'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#131315'
  on-background: '#e5e1e4'
  surface-variant: '#353437'
typography:
  display-lg:
    fontFamily: Geist
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.03em
  headline-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  stat-lg:
    fontFamily: Geist
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  body-base:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
    letterSpacing: -0.01em
  body-bold:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 22px
    letterSpacing: -0.01em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.08em
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
---

## Brand & Style

This design system is built on the principles of **Architectural Minimalism** and **Data-Dense Utility**. It is designed for high-performance SaaS environments where clarity, speed, and precision are paramount. The aesthetic is inspired by tool-first interfaces like Linear and Raycast, prioritizing functional density over decorative whitespace.

The emotional response should be one of **absolute control and professional authority**. By utilizing a "wireframe-plus" approach, the UI removes visual noise, allowing complex data structures to remain legible. The style leans into a modern Corporate/Minimalist hybrid, characterized by:
- **Geometric Rigor:** Every element aligns to a strict grid.
- **Subsurface Depth:** Hierarchy is established through layering and thin dividers rather than heavy shadows.
- **Interactive High-Lighting:** Vibrant accents are used sparingly to guide the eye to primary actions.
- **Precision Typography:** Tight tracking and monospaced accents for a technical, engineered feel.

## Colors

The palette is anchored by a **Zinc/Slate** foundation, optimized for a "Deep Charcoal" dark mode that reduces eye strain during prolonged professional use.

- **Primary (Veridian Violet):** Used for active states, primary buttons, and focus rings. It represents the "active" intent of the user.
- **Secondary (Aether Indigo):** Used for data visualization, secondary highlights, and brand-moments.
- **Neutral (Zinc/Slate):** 
    - `Base (#09090b)`: The ground-level canvas.
    - `Surface (#121214)`: For sidebars and nested panels.
    - `Border (#1f2024)`: The "Hairline" divider used for all structural separation.
- **Functional:** Standard Success (Emerald), Warning (Amber), and Error (Crimson) are used with high saturation but small footprints to maintain the minimalist aesthetic.

## Typography

Typography is the primary tool for hierarchy in this design system. We use a tri-font system to separate concerns:

1.  **Geist (Headlines/Stats):** A technical sans-serif used for high-level navigation and data points. It features tight tracking to create an "architectural" block feel.
2.  **Inter (UI/Body):** The workhorse for all interface elements, labels, and paragraphs. It is chosen for its exceptional legibility at small sizes.
3.  **JetBrains Mono (Metadata/Shortcuts):** Used for "Label Caps," keyboard shortcuts, and technical logs. It signals "utility" and "precision."

**Scaling:** On mobile devices, display sizes are reduced by approximately 20% to maintain density without overwhelming the viewport.

## Layout & Spacing

This design system uses a **Fluid Grid with Fixed Structural Anchors**. It prioritizes high information density, favoring compact margins over sprawling whitespace.

- **Grid Model:** 12-column layout for desktop with 16px gutters. For data-heavy tables, the grid can expand to fill the container.
- **Rhythm:** Based on a 4px baseline. Most UI gaps are 8px (small) or 16px (standard).
- **Dividers:** Layout sections are separated by 1px `Border (#1f2024)` lines rather than background color shifts. This maintains a "flat but layered" architectural look.
- **Responsive:**
    - **Desktop:** Multi-pane layouts (Sidebar + List + Detail).
    - **Tablet:** Collapsible sidebar; detail view becomes an overlay or full-screen.
    - **Mobile:** Single-column flow with 16px safe-area margins.

## Elevation & Depth

Depth is communicated through **Tonal Layering** and **Subtle Outlines** rather than physical shadows.

- **Structural Depth:** We use three primary layers:
    1. `Base (#09090b)`: The lowest level.
    2. `Surface (#121214)`: Floating panels, sidebars, or cards.
    3. `Overlay (#18181b)`: Menus, tooltips, and dialogs.
- **Borders:** Every interactive container must have a 1px border. Use `#1f2024` for inactive states and `#2e3036` for hovered/active containers.
- **Glassmorphism:** Reserved strictly for transient overlays (Command Palettes, Modals). Use a 16px-24px backdrop blur with an 85% opacity fill of the `Surface` color.
- **Shadows:** Shadows are used sparingly as "Ambient Glows." They should be high-blur (20px+), low-opacity (4%), and tinted with the neutral base color to feel integrated into the dark background.

## Shapes

The shape language is **Structured and Softened**. We avoid sharp 90-degree corners to ensure the UI feels modern and approachable, but we avoid "pill" shapes for primary containers to maintain a professional, grid-aligned feel.

- **Standard (8px):** Buttons, inputs, and small cards.
- **Large (12px):** Modals, command palettes, and main content areas.
- **XL (16px):** Outer application containers or large featured sections.
- **Full:** Used only for status dots or user avatars.

## Components

- **Buttons:** 
    - *Primary:* Solid `Veridian Violet` with a subtle 1px top-border highlight.
    - *Ghost:* Transparent background, transitioning to a `Violet Mist` (low-opacity violet) on hover.
    - *Action:* On click, buttons should scale to 98% for tactile feedback.
- **Inputs:** 
    - Background: `Base (#0f0f11)`. Border: 1px `#1f2024`.
    - Focus: Border color shifts to `Veridian Violet` with a 1px glow ring.
    - Include inline JetBrains Mono labels for keyboard shortcuts (e.g., `⌘K`).
- **Cards:** No heavy shadows. Use 1px borders and a slightly lighter surface color (`#121214`).
- **Lists:** High-density rows (32px-36px height). Use `Inter` 14px for primary text and `JetBrains Mono` 11px for secondary metadata.
- **Chips/Tags:** Monospaced text in `Label Caps` style. Backgrounds are low-contrast (subtle grey or muted violet).
- **Command Palette:** The centerpiece component. Centered, 640px wide, 12px rounded corners, with heavy backdrop blur and high density list items.