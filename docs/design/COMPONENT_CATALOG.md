# RemediSync: Component-Wise Architecture & Registry Catalog

## 1. Component-Wise Coding Philosophy

The Next.js frontend in `frontend/src/` follows a strict **4-layer component hierarchy**. Each file owns a single responsibility, accepts strictly typed TypeScript props, and never mixes data-fetching logic with pure visual rendering.

```text
Layer 4: App Router Pages (src/app/*/page.tsx)
   └── Thin route controllers (URL state, data loading, composing features)
          │
Layer 3: Domain Feature Components (src/components/features/*)
   └── Pharmacy-specific modules (InventoryTable, ReplenishmentTable, SkuSalesDrawer)
          │
Layer 2: Application Chrome (src/components/layout/*)
   └── Persistent shell (AppShell, Sidebar, TopBar, BranchSelector, SystemHealthBadge)
          │
Layer 1: Design System Primitives (src/components/ui/*)
   └── Pure, reusable UI building blocks powered by CVA + Tailwind tokens
```

### Strict Coding Conventions
1. **One component per file** (`PascalCase.tsx`), accompanied by explicit prop interfaces (`export interface ButtonProps`).
2. **Variant-driven styling via `cva` (`class-variance-authority`)** combined with `cn()` (`clsx` + `tailwind-merge`). No inline conditional spaghetti strings.
3. **Server Components by default in App Router:** Keep `layout.tsx` and static shells as Server Components; add `'use client'` strictly at interactive leaf or feature boundaries (`BranchSelector`, `InventoryTable`, `OrderApprovalBar`, charts).
4. **Zero raw API calls inside UI primitives:** Layer 1 (`ui/`) never imports `apiClient`. Only Layer 3/4 components or custom hooks invoke `src/services/apiClient.ts`.

---

## 2. External Component Sourcing: `21st.dev` & `reactbits.dev`

To accelerate high-craft interactive primitives without reinventing accessible overlays or subtle micro-interactions, we integrate curated source-owned components from **`21st.dev`** and **`reactbits.dev`** via the **shadcn registry CLI** (`npx shadcn@latest add ...`).

### 2.1 `21st.dev` — Enterprise Interactive Primitives
Components on [21st.dev](https://21st.dev) install directly as editable TypeScript + Tailwind source files into `frontend/src/components/ui/`.

| UI Need in RemediSync | Recommended `21st.dev` Component Category | Install Pattern |
| :--- | :--- | :--- |
| Dense sortable/filterable SKU & PO tables | Minimalist Enterprise Data Table (`@tanstack/react-table` backed) | `npx shadcn@latest add https://21st.dev/r/<author>/<slug>` |
| Quick Branch / Category / Urgency filtering | Accessible Combobox / Select & Segmented Tab Switcher | `npx shadcn@latest add https://21st.dev/r/<author>/<slug>` |
| SKU 30-day Sales Inspector | Right-side Slide-Over Sheet / Drawer (`radix-ui` dialog backed) | `npx shadcn@latest add https://21st.dev/r/<author>/<slug>` |
| PO Approval Confirmation Feedback | Clean Non-Intrusive Toast Notification Stack | `npx shadcn@latest add https://21st.dev/r/<author>/<slug>` |
| Numeric Stepper for Approved Order Units | Compact Inline Number Input with Step Controls | `npx shadcn@latest add https://21st.dev/r/<author>/<slug>` |

### 2.2 `reactbits.dev` — Restrained Micro-Interactions (`-TS-TW` Variants)
Components on [reactbits.dev](https://reactbits.dev) ship in TypeScript + Tailwind flavors using the `-TS-TW` suffix (`npx shadcn@latest add @react-bits/<Component>-TS-TW`).

Because RemediSync is an **Operate-mode clinical workbench** (not a flashy gaming/marketing landing page), React Bits usage is **deliberately restrained** to quiet, meaningful moments:

| UI Moment in RemediSync | React Bits Component | Usage & Restraint Rule |
| :--- | :--- | :--- |
| Initial KPI Hydration on `/overview` | `CountUp-TS-TW` | Fast (`400ms`) tabular-nums count-up once on initial data load; disabled under `prefers-reduced-motion`. |
| Subtle List Row / Drawer Reveal | `AnimatedContent-TS-TW` (or CSS transform transition) | Short `180ms` opacity + `4px` reveal for the SKU sales drawer; never applied to every scrolling table row. |
| Interactive Quick-Filter Bar | `ClickSpark` / flashy shaders / 3D tilts / aurora blobs | **Explicitly banned** on pharmacy dashboards (violates Operate mode & Anti-Slop floor). |

### 2.3 Mandatory Unslop Adaptation Checklist for Pulled Registry Components
Every component pulled from `21st.dev` or `reactbits.dev` **must** pass these 4 cleanup steps before being imported into any page:
1. **Rewire all colors to `:root` semantic tokens** (`bg-[var(--bg-surface)]`, `border-[var(--border-hairline)]`, `text-[var(--ink-primary)]`). Strip any hardcoded hex, violet/blue gradients, or dark-mode neon glows.
2. **Strip `transition-all`** and replace with explicit property transitions (`transition-colors duration-150`).
3. **Verify `:focus-visible` ring & keyboard navigation** (`Tab`, `Enter`, `Escape` on drawers/modals).
4. **Enforce `tabular-nums` (`font-mono`)** on any component displaying currency, quantities, dates, or SKU IDs.

---

## 3. Layer 1: Design System Primitives Specification (`src/components/ui/`)

| Component | Variants / Props | State Matrix (Default / Hover / Focus / Disabled) |
| :--- | :--- | :--- |
| **`Button`** | `variant`: `primary` \| `secondary` \| `danger` \| `ghost`<br>`size`: `sm` (`32px`) \| `md` (`36px`)<br>`loading`: `boolean` | **Primary:** Teal-700 bg, white ink → Hover Teal-800 → Focus 2px Teal-700 ring offset 2px → Disabled 50% opacity, `cursor-not-allowed`.<br>**Secondary:** White bg, `1px` slate-200 border, slate-900 ink → Hover slate-50 bg, slate-300 border. |
| **`Badge`** | `tone`: `critical` \| `warning` \| `healthy` \| `neutral`<br>`size`: `sm` \| `md` | Soft tinted surface (`--status-*-bg`), `1px` matching border, `4.5:1+` dark semantic ink, `6px` border-radius, sentence case. No loud solid neon fills. |
| **`Card`** | `Card`, `CardHeader`, `CardTitle`, `CardContent`, `CardFooter` | Pure white surface (`--bg-surface`), `1px solid var(--border-hairline)`, `12px` radius, `20px` padding, zero shadow. Never nest a `Card` inside another `Card`. |
| **`DataTable`** | Generic `<T>`: `columns`, `data`, `onRowClick`, `isLoading`, `emptyState`, `rowKey` | Sticky `slate-50` header (`36px`), uniform `42px` rows, `1px` bottom hairlines, right-aligned numeric columns with `font-mono tabular-nums`, subtle `slate-50` row hover. |
| **`Input`** | `type`, `label`, `error`, `prefixIcon` | `36px` height, `8px` radius, `1px` slate-200 border, visible label above (never placeholder-only), crisp inline error message directly below on validation failure. |
| **`SegmentedControl`** | `options: { value, label, count? }[]`, `value`, `onChange` | `slate-100` track (`34px` height, `8px` radius), active option elevated to white surface with `1px` hairline border and `6px` nested radius. |
| **`SlideOver`** | `open`, `onClose`, `title`, `subtitle`, `children` | Fixed right drawer (`480px` desktop, `100%` mobile), muted backdrop (`rgba(15, 23, 42, 0.28)`), `Escape` key closes, focus trapped inside while open. |
| **`Skeleton`** | `width`, `height`, `className` | Neutral `slate-100` / `slate-200` subtle pulse reserving exact target geometry (`CLS < 0.1`). |
| **`EmptyState`** | `title`, `description`, `action?` | Direct, calm guidance inviting action (e.g., *"No batches expiring within 90 days for this branch"*). |

---

## 4. Layer 2 & 3: Domain Feature Modules (`src/components/features/`)

| Feature Directory | Components | Primary Backend Endpoint |
| :--- | :--- | :--- |
| **`layout/`** | `AppShell`, `Sidebar`, `TopBar`, `BranchSelector`, `SystemHealthBadge` | `GET /api/v1/health` |
| **`overview/`** | `OverviewKpiGrid`, `BranchComparisonTable`, `OperationalRiskPanel` | `GET /api/v1/analytics/overview` |
| **`inventory/`** | `InventoryToolbar`, `InventoryTable`, `DaysOfCoverBar`, `SkuSalesDrawer` | `GET /api/v1/inventory/branches/{branch_id}`<br>`GET /api/v1/sales/history` |
| **`replenishment/`** | `ReplenishmentSummaryStrip`, `ReplenishmentTable`, `RationaleProofBox`, `OrderApprovalBar` | `GET /api/v1/recommendations/replenish`<br>`POST /api/v1/orders/approve` |
| **`expiry/`** | `ExpirySummaryStrip`, `BatchExpiryTable`, `ReturnCutoffTag` | `GET /api/v1/inventory/batches/expiry-risk` |
