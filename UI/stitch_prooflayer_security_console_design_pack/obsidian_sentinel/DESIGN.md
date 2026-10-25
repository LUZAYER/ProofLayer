---
name: Obsidian Sentinel
colors:
  surface: '#0e1323'
  surface-dim: '#0e1323'
  surface-bright: '#34394a'
  surface-container-lowest: '#080d1d'
  surface-container-low: '#161b2b'
  surface-container: '#1a1f30'
  surface-container-high: '#25293a'
  surface-container-highest: '#2f3446'
  on-surface: '#dee1f9'
  on-surface-variant: '#bacac5'
  inverse-surface: '#dee1f9'
  inverse-on-surface: '#2b3041'
  outline: '#859490'
  outline-variant: '#3c4a46'
  surface-tint: '#3cddc7'
  primary: '#57f1db'
  on-primary: '#003731'
  primary-container: '#2dd4bf'
  on-primary-container: '#00574d'
  inverse-primary: '#006b5f'
  secondary: '#adc6ff'
  on-secondary: '#002e6a'
  secondary-container: '#0566d9'
  on-secondary-container: '#e6ecff'
  tertiary: '#66f3b6'
  on-tertiary: '#003824'
  tertiary-container: '#44d69b'
  on-tertiary-container: '#00593b'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#62fae3'
  primary-fixed-dim: '#3cddc7'
  on-primary-fixed: '#00201c'
  on-primary-fixed-variant: '#005047'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#0e1323'
  on-background: '#dee1f9'
  surface-variant: '#2f3446'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 2rem
    fontWeight: '600'
    lineHeight: 2.5rem
    letterSpacing: -0.025em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 2rem
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 2rem
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 1.125rem
    fontWeight: '600'
    lineHeight: 1.5rem
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '600'
    lineHeight: 1.25rem
    letterSpacing: 0em
  body-lg:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.5rem
  body-md:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.375rem
  body-sm:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '400'
    lineHeight: 1.125rem
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 0.8125rem
    fontWeight: '500'
    lineHeight: 1.25rem
    letterSpacing: -0.01em
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 0.6875rem
    fontWeight: '500'
    lineHeight: 1rem
    letterSpacing: 0em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 0.6875rem
    fontWeight: '600'
    lineHeight: 0.875rem
    letterSpacing: 0.06em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system delivers a calm, high-trust, and hyper-precise security cockpit tailored for SecOps leads, compliance auditors, and engineering architects defending enterprise AI infrastructure. 

The aesthetic is precision-engineered minimalism layered over deep terminal-grade surfaces. It balances modern fintech rigor with defense-grade technical fidelity:
- **Atmosphere:** Dark, controlled, forensic, low-fatigue. High-density information architecture designed for sustained incident response and zero-error telemetry.
- **Visual Stance:** Utilitarian structural framing, refined technical typography, low-luminance canvas backgrounds, and surgical pops of signal illumination.
- **Trust Anchors:** Every action, validation gate, and model intervention is backed by cryptographic audit indicators, explicit state labels, and double-verified semantic cues.

## Colors

The palette leverages an ink-navy visual hierarchy designed to preserve night-vision comfort in dark operations centers while directing cognitive focus via high-contrast accent tiers.

### Canvas & Surface Architecture
- **Canvas Base:** `#0B1020` (Deep Ink-Navy) — primary canvas backdrop.
- **Surface Level 1:** `#121A30` (Raised Surface) — containment cards, telemetry panels, table modules.
- **Surface Level 2:** `#1A233D` (Secondary Surface) — inner wells, inspection drawouts, nested panels, code blocks.
- **Surface Interactive / Hover:** `#222E50` — hover states for list rows, table rows, and interactive buttons.
- **Hairline Structural Borders:** `#232C48` — 1px crisp separation grid line across panels, headers, and split views.

### Signal Accents & Semantic Tiers
Color is treated strictly as an informative signal, never purely decorative, and **never used in isolation without an accompanying shape, icon, or explicit text string**:
- **Primary / Active Safe:** `#2DD4BF` (Electric Teal) — cryptographic proof verified, primary safe actions, terminal focus rings.
- **Informational / Telemetry:** `#3B82F6` (Electric Azure) — model routing indicators, protocol logs, runtime metadata.
- **Allowed / Enforced Pass:** `#10B981` (Verification Emerald) — firewall allow rules, benign payload classifications.
- **Needs Approval / Warning:** `#F59E0B` (Amber Protocol) — threshold anomalies, human-in-the-loop intervention gates.
- **Blocked / Threat / Breach:** `#EF4444` / `#F43F5E` (High-Criticality Red) — prompt injection detected, agent token revoked, policy breach.

## Typography

The typography structure enforces strict semantic roles across analytical telemetry, standard UI navigation, and foreign script contexts:

- **Primary Interface (Inter):** Applied across global UI framing, page headers, navigational items, form controls, and body documentation. Uses subtle negative tracking on larger headline scales to maintain typographic tension.
- **Evidence & Machine Telemetry (JetBrains Mono):** Dedicated to cryptographic hashes, transaction signatures, agent IDs, latency metrics, log outputs, and raw JSON payloads. Its tabular spacing ensures data alignment in high-density tables.
- **Multilingual Support (Noto Sans Bengali):** Explicitly mapped for secondary locale operations (`বাংলা`). Ensure consistent font rendering for institutional users in regional financial centers with a minimum line height of `1.5` to accommodate conjunct vertical glyphs.

## Layout & Spacing

The layout is structured around an uncompromising 8px baseline rhythm (with a 4px sub-grid for badges, metrics, and nested controls) to enforce visual predictability across mission-critical consoles.

### Shell Architecture
- **Global Top Navigation:** Fixed 56px height. Accommodates the Global Search (`Cmd/Ctrl + K`), dynamic Shield Active Indicator (`ON` / `OFF`), Proof Chain validation badge, locale switch (`EN | বাংলা`), system alert bells, and profile dropdown.
- **Collapsible Sidebar:** Fixed 240px expanded width; collapses down to 64px icon-only rail to maximize operational monitoring width for telemetry and live-stream logs.
- **Operational Viewport:** Fluid layout bounded between `1280px` min-width for full desk operations and standard 12-column dynamic flex behavior. Tables occupy full panel widths with internal horizontal scroll capability for audit records.

### Breakpoint Strategy
- **Desktop (>= 1280px):** Permanent or expandable 240px navigation sidebar, split-view panels for deep log inspection, full 12-column grid.
- **Tablet / Compact Operations (768px - 1279px):** Sidebar collapses to a 64px icon-rail by default. Audit inspection panels switch to overlay slide-out sheets.
- **Mobile Handheld (320px - 767px):** Single-column stacked cards, off-canvas navigation drawer, horizontal scroll on data tables with fixed left identifier column.

## Elevation & Depth

This design system rejects deep, diffuse drop shadows in favor of crisp tonal stacking and dark-mode structural containment:

- **Base Layer (Canvas `#0B1020`):** Receded backplane for background operational canvas and global margins.
- **Tier 1 (Surface `#121A30`):** Cards, primary data grids, and dashboards. Demarcated by a 1px solid hairline border (`#232C48`) and a low-opacity ambient drop (`0 2px 8px rgba(0, 0, 0, 0.4)`).
- **Tier 2 (Surface `#1A233D`):** Modals, flyout inspection drawers, code blocks, and active dropdown panels. Bordered by `#2E3A5E` with an elevation shadow of `0 12px 32px -4px rgba(0, 0, 0, 0.6)`.
- **Focus & Selection Luminescence:** When elements transition to focused or active states, a subtle primary glow is cast: `0 0 0 1px #2DD4BF, 0 0 16px -2px rgba(45, 212, 191, 0.25)`.

## Shapes

The geometric architecture uses an intentional 12px corner radius (`rounded-lg`, value: `2`) on standard cards and operational modules, contrasting sharp technical contents with balanced exterior containment.

- **Panels, Modals & Inspection Cards:** `12px` (`0.75rem` / `rounded-lg`). Creates a modern, contained cockpit without feeling playful.
- **Input Fields & Action Buttons:** `8px` (`0.5rem` / default). Balances ergonomics with structural stability.
- **Badges, Status Pills & Verification Chips:** `9999px` (Pill-shaped) to distinguish transient status indicators from static layout framing.
- **Telemetry Hash Containers:** `4px` (`0.25rem` / `rounded-sm`) for terminal code chunks, keys, and token snippets.

## Components

### Buttons
- **Primary Action (Verified / Safe):** Solid electric teal (`#2DD4BF`) background, `#0B1020` heavy contrast text, weight 600, rounded 8px. Hover: `#26b8a5`. Focus: 2px offset border with teal glow.
- **Secondary / Tactical:** `#1A233D` surface background, 1px `#232C48` border, `#E2E8F0` text. Hover: `#222E50` with `#2DD4BF` border tint.
- **Destructive / Emergency Stop:** Deep crimson `#450A0A` background, 1px `#EF4444` border, `#FCA5A5` text. Used for revoking active agent sessions or blocking endpoints.

### Telemetry & Status Badges
- Every status indicator must consist of an icon + label + semantic background tint:
  - **Verified / Allowed:** `#064E3B` background (20% opacity), `#10B981` text & stroke, check-circle icon.
  - **Needs Approval:** `#78350F` background (25% opacity), `#F59E0B` text & stroke, alert-triangle icon.
  - **Blocked / Threat:** `#7F1D1D` background (25% opacity), `#EF4444` text & stroke, shield-x icon.
  - **Informational:** `#1E3A8A` background (25% opacity), `#3B82F6` text & stroke, info icon.

### Form Inputs & Global Search
- Background `#121A30`, 1px border `#232C48`, text `#F8FAFC`. 
- Placeholder styled in muted slate `#64748B`.
- Integrated monospace keyboard badge indicator (e.g., `⌘K`) using `#1A233D` fill and `#475569` text.

### Cryptographic Audit Tables
- Compact headers in `label-caps` (`JetBrains Mono`, uppercase, tracking `0.06em`, color `#64748B`).
- Alternating subtle rows on `#121A30` with hover state `#222E50`.
- Cells containing hashes (tx ids, agent proof signatures) use `code-sm`, truncated to 8...8 characters with a 1-click copy action.
- Table separators are strict 1px hairlines in `#232C48`.

### Specialized Domain Components
- **Shield Status Switch:** Top-level toggle. Active state emits a subtle green/teal signal ping (`#10B981`) with label `SHIELD: ACTIVE`. Disengaged state turns warning amber (`#F59E0B`) with prompt verification modal.
- **Audit Chain Badge:** Visual verification pill anchored in the top header displaying `CHAIN: VERIFIED [BLOCK #94821]` with a lock icon.
- **Language Switcher (`EN | বাংলা`):** Segmented pill control allowing instant localization flip while ensuring line-height auto-expands to prevent Bengali character clipping.