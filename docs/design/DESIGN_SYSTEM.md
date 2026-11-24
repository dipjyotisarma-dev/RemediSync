# RemediSync: Clinical Enterprise Design System

## 1. Surface Mode & Product Direction

RemediSync's dashboard operates in **Operate Mode** (per Impeccable surface classification). Floor pharmacists and procurement directors use this interface for hours during active dispensary shifts. Scanability, numeric precision, predictable keyboard/mouse affordances, and visual calm outrank decorative expression.

### Five-Line Product Direction
- **Product:** Predictive inventory control, FEFO expiry auditing, and purchase order approval workbench for multi-branch retail pharmacies.
- **Character:** Clinical, exacting, calm under rush hours.
- **World:** Dispensary counter ledgers, calibrated apothecary instruments, and clean prescription slips.
- **Moments:** Two focal craft surfaces carry visual richness while chrome stays quiet: (1) the 30-day SKU demand-vs-stockout velocity chart in the shelf drawer, and (2) the transparent pharmacist calculation proof block on replenishment approvals.
- **Signature:** The calibrated **Days-of-Cover ($DoC$) horizon bar** paired with tabular numeric telemetry (`5.6d` vs `1.5d` supplier lead time).

---

## 2. Three-Layer Token Architecture

Every color, font, radius, and spacing value must flow through CSS custom properties declared at `:root` in `frontend/src/app/globals.css`. Raw hex values or ad-hoc font stacks inside `.tsx` components are prohibited.

### Layer 1: Primitive Tokens (Neutral Graphite-Slate + Clinical Accent Ramp)
```css
:root {
  /* Neutral surface & ink ramp */
  --raw-white: #FFFFFF;
  --raw-slate-50: #F8FAFC;
  --raw-slate-100: #F1F5F9;
  --raw-slate-200: #E2E8F0;
  --raw-slate-300: #CBD5E1;
  --raw-slate-500: #64748B;
  --raw-slate-600: #475569;
  --raw-slate-700: #334155;
  --raw-slate-900: #0F172A;

  /* Clinical accent (single chrome accent) */
  --raw-teal-50: #F0FDFA;
  --raw-teal-200: #99F6E4;
  --raw-teal-700: #0F766E;
  --raw-teal-800: #115E59;

  /* Semantic clinical status ramps (muted to sit cleanly on light surfaces) */
  --raw-emerald-50: #ECFDF5;
  --raw-emerald-200: #A7F3D0;
  --raw-emerald-700: #047857;

  --raw-amber-50: #FFFBEB;
  --raw-amber-200: #FDE68A;
  --raw-amber-700: #B45309;

  --raw-rose-50: #FFF1F2;
  --raw-rose-200: #FECDD3;
  --raw-rose-700: #BE123C;
}
```

### Layer 2: Semantic Tokens
| Semantic Token | Mapped Primitive | Purpose | Contrast Requirement |
| :--- | :--- | :--- | :--- |
| `--bg-canvas` | `--raw-slate-50` | Application viewport background | Base surface |
| `--bg-surface` | `--raw-white` | Cards, tables, drawers, top bar | Elevated surface |
| `--bg-subtle` | `--raw-slate-100` | Table headers, hover rows, inactive pills | Subtle surface step |
| `--border-hairline` | `--raw-slate-200` | Card borders, row dividers, input frames | Quiet `1px` separation |
| `--border-strong` | `--raw-slate-300` | Focused inputs, active segmented controls | Tactile control boundary |
| `--ink-primary` | `--raw-slate-900` | Page titles, metric figures, medicine brand names | `> 12:1` on white |
| `--ink-secondary` | `--raw-slate-600` | Generic salts, supplier names, body descriptions | `> 6.5:1` on white |
| `--ink-muted` | `--raw-slate-500` | Table column labels, timestamps, helper text | `>= 4.6:1` on white |
| `--accent-primary` | `--raw-teal-700` | Primary actions, active nav indicator, active tab | `> 5.4:1` with white text |
| `--accent-primary-hover` | `--raw-teal-800` | Primary button hover state | `> 7.2:1` with white text |
| `--status-critical-ink` | `--raw-rose-700` | `CRITICAL` stockout, expired/imminent write-off | `> 6.2:1` on `--status-critical-bg` |
| `--status-critical-bg` | `--raw-rose-50` | Critical status badge / subtle alert banner | Tinted surface |
| `--status-warning-ink` | `--raw-amber-700` | `REORDER`, Below ROP, $\le 90$-day return cutoff | `> 5.0:1` on `--status-warning-bg` |
| `--status-warning-bg` | `--raw-amber-50` | Warning status badge / expiry notice | Tinted surface |
| `--status-healthy-ink` | `--raw-emerald-700` | `HEALTHY` cover, connected DB, `APPROVED` PO | `> 5.2:1` on `--status-healthy-bg` |
| `--status-healthy-bg` | `--raw-emerald-50` | Healthy status badge / approval confirmation | Tinted surface |

### Layer 3: Component & Layout Tokens
| Token | Value | Rule |
| :--- | :--- | :--- |
| `--sidebar-width` | `240px` | Fixed left navigation rail on desktop (`>= 1024px`) |
| `--topbar-height` | `56px` | Sticky contextual top header |
| `--content-max-width` | `1440px` | Capped fluid workspace width (gutters grow on ultrawide) |
| `--table-row-height` | `42px` | Uniform compact density across all data tables |
| `--radius-panel` | `12px` | Cards, drawers, modals |
| `--radius-control` | `8px` | Buttons, inputs, dropdowns, segmented controls (`inner = outer - padding`) |
| `--radius-badge` | `6px` | Status pills and Pareto class tags (never overly bubbly full pills on every tag) |

---

## 3. Typography & Numeric Precision

### Font Pairing (Loaded via `next/font/google`)
1. **Interface Sans — `Figtree`** (`--font-sans`):
   - Selected via UI/UX Pro Max healthcare domain intelligence for high legibility, warm clinical neutrality, and crisp low-weight rendering.
   - Weights loaded: `400` (regular), `500` (medium), `600` (semibold — restricted to primary KPI numerals and active tab labels). **Weights `700`–`900` are banned.**
2. **Telemetry Mono — `JetBrains Mono`** (`--font-mono`):
   - Applied exclusively to quantitative and coded clinical data: Indian currency (`₹`), SKU IDs (`MED001`), Batch numbers (`TL-2025-099`), Days of Cover (`5.6d`), ROP, and timestamps.
   - Always enforces `font-variant-numeric: tabular-nums;` so vertical columns align down to the decimal point.

### Type Scale & Case Discipline
| Role | Size / Line-Height | Weight | Case | Tracking |
| :--- | :--- | :---: | :--- | :--- |
| Page Title (`h1`) | `20px / 28px` | `500` | Sentence case | `-0.015em` |
| Section Heading (`h2`) | `15px / 22px` | `500` | Sentence case | `-0.01em` |
| KPI Figure | `26px / 32px` (`mono`) | `600` | Tabular numerals | `-0.02em` |
| Body / Table Cell | `13.5px / 20px` | `400` | Sentence case | `0` |
| Column Header / Label | `12px / 16px` | `500` | **Sentence case** (no ALL-CAPS eyebrows) | `0` |
| Micro Meta / Helper | `12px / 16px` | `400` | Sentence case | `0` |

### Formatting Consistency
- **Currency (INR):** Always formatted via `Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })` (e.g., `₹2,26,534.59` or whole-rupee `₹51,550` consistently within the same strip).
- **Days of Cover:** Single decimal place with compact unit (`5.6d`, `1.2d`, or `99+ d` when demand is zero).
- **Percentages:** Consistent single decimal (`1.8%`, `+2.9% vs target`).

---

## 4. Spacing, Elevation & Motion Rules

### 4px Spatial Grid
- All margins, paddings, gaps, and control heights sit on a strict `4px` base grid (`4`, `8`, `12`, `16`, `20`, `24`, `32`). No arbitrary values like `mt-[13px]` or `py-[11px]`.
- Sidebar navigation rows: `34px` height, `4px` gap between rows, `16px` horizontal padding.
- Cards: `20px` internal padding (`p-5`), `16px` gap between sibling cards (`gap-4`), `24px` vertical separation between distinct page sections (`space-y-6`).

### Elevation (Flat Clinical Restraint)
- Hierarchy is created through surface contrast (`#F8FAFC` canvas vs `#FFFFFF` elevated panel) and `1px` hairlines (`#E2E8F0`), **not** drop shadows.
- Only floating overlays (`SlideOver` drawer, dropdown menus, confirmation modals, toast alerts) carry a subtle neutral shadow (`0 8px 24px -4px rgba(15, 23, 42, 0.08)`).

### Icons
- Single icon library: **Lucide React** (`16px` in buttons/tables/nav, `18px` in section headers, `strokeWidth={1.5}`).
- Icons inherit `--ink-secondary` or `--ink-muted` (never rainbow icon boxes).
- Fixed `20px` icon container width in navigation and list rows so text labels align on an exact vertical axis.
- **Zero emojis** anywhere in the UI.

### Motion & Interaction Physics
- **Never** write `transition: all`. Explicitly transition `background-color`, `border-color`, `color`, `opacity`, or `transform`.
- **Never** animate `width`, `height`, `top`, or `left`.
- Fast, responsive timings: `150ms ease-out` for hover/focus state shifts; `220ms cubic-bezier(0.16, 1, 0.3, 1)` for drawer/modal entrances.
- Every motion primitive honors `@media (prefers-reduced-motion: reduce)`.
- `html, body { overflow-x: clip; }` (never `overflow-x: hidden` or `100vw`).

---

## 5. UX Copywriting Standards

1. **Sentence case everywhere:** `Daily revenue`, `Reorder point`, `Approve selected orders` (never `DAILY REVENUE` or `APPROVE ORDERS`).
2. **Active, operational verbs:** Button label matches confirmation toast (`Approve order` → `Order approved`, `Refresh data` → `Data updated`). Never generic `Submit`.
3. **Zero greeting fluff or hype:** Never `Welcome back! 👋`, never `AI-powered magic`, never exclamation marks (`!`). Page headers state the exact workspace context (`Network overview`, `Shelf inventory`).
4. **Actionable error & empty states:** Errors never apologize vaguely; they state what failed, display the backend `correlation_id`, and provide a direct retry control.
5. **No trailing periods** on headings, KPI labels, buttons, or table headers. Multi-sentence pharmacist rationales retain proper punctuation.

---

## 6. Anti-Slop Quality Floor (Pre-Delivery Audit Gate)

Before any Phase 15 PR or commit is considered ready, every screen must pass this non-negotiable checklist synthesized from **Impeccable**, **Unslop**, **Hallmark**, **Frontend Design**, and **UI/UX Pro Max**:

- [ ] Zero hardcoded hex colors or raw `font-family` declarations outside `:root` token definitions.
- [ ] Zero purple/cyan gradients, colored glows, glassmorphism blurs, or decorative floating blobs.
- [ ] Zero card-inside-card nesting; zero identical 4-card rows stacked without visual rhythm variation.
- [ ] Stat cards contain only label + tabular figure + comparison baseline (no decorative mini sparklines or rainbow icons).
- [ ] Zero ALL-CAPS wide-tracked eyebrow labels, zero middle-dot meta strings (`A · B · C`), zero arrows glued to button text (`View →`).
- [ ] Zero emojis in labels, headers, or badges.
- [ ] Visible `:focus-visible` ring on every button, link, input, and table row trigger.
- [ ] Minimum `4.5:1` contrast on all body/label text and status badges.
- [ ] All real metrics sourced from FastAPI endpoints; zero invented testimonials, fake counts, or placeholder `[X]` strings.
- [ ] Verified responsive layout with zero horizontal overflow at `1440px`, `1024px`, and `768px`.
