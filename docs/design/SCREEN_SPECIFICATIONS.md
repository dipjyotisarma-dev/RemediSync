# RemediSync: Screen-by-Screen UI Specifications

This document defines the exact layout composition, API bindings, interaction flows, and clinical copywriting for every route in the Next.js Management Dashboard.

---

## 1. Persistent Application Shell (`AppShell`)

All 4 routes share one calm, fixed-frame workspace layout:

```text
+--------------------+--------------------------------------------------------------------+
| RemediSync         | Page Title (e.g. Shelf inventory)      [Branch: BR001 v] [Refresh] | <- 56px TopBar
+--------------------+--------------------------------------------------------------------+
|                    |                                                                    |
|  Overview          |   Main Scrollable Canvas (max-w-[1440px] mx-auto px-6 py-6)        |
|  Shelf inventory   |                                                                    |
|  Replenishment     |   • Strict 4px grid rhythm                                         |
|  Expiry audit      |   • Asymmetric composition (KPI strip -> primary table/chart)      |
|                    |   • Zero horizontal page scroll (overflow-x: clip)                 |
|                    |                                                                    |
|                    |                                                                    |
| ------------------ |                                                                    |
| API Connected      |                                                                    |
| HGB Forecaster v1.2|                                                                    |
+--------------------+--------------------------------------------------------------------+
     240px Rail                                  Fluid Content
```

### Shell Behaviors
- **Branch Selector (`TopBar`):**
  - On `/overview` and `/expiry`: supports `All branches (Assam network)` plus `BR001` (Kamakhya Gate), `BR002` (Dharapur), `BR003` (Azara), and `BR004` (Rani Gate).
  - On `/inventory` and `/replenishment`: always scoped to a specific branch (defaults to `BR001` if switched from `All branches`).
- **System Health Badge (`Sidebar` footer):**
  - Calls `GET /api/v1/health`.
  - Displays a quiet status dot (emerald when `database === "CONNECTED"`, crimson when degraded/offline) plus the active forecaster name (`HistGradientBoosting v1.2.0`).
- **Responsive Collapse (`< 1024px`):**
  - Sidebar collapses cleanly into an accessible slide-out drawer toggled by a single top-left menu button.

---

## 2. Route 1: Executive Network Overview (`/overview`)

- **Primary Audience:** Regional Procurement Director / Pharmacy Owner
- **API Bindings:** `GET /api/v1/analytics/overview?branch_id=<opt>&days=30` and `GET /api/v1/inventory/batches/expiry-risk`

### Layout Wireframe
```text
+----------------------+----------------------+----------------------+----------------------+
| Daily gross revenue  | Network stockout     | Critical stockouts   | Near-expiry exposure |
| ₹2,26,534            | 1.8%                 | 3 SKUs               | ₹48,200              |
| +2.9% vs ₹2,20,000   | Across 30-day window | 4 branches tracked   | 12 lots <= 90 days   |
+----------------------+----------------------+----------------------+----------------------+

+----------------------------------------------------+  +-----------------------------------+
| Branch performance vs daily target                 |  | Immediate operational actions     |
|                                                    |  |                                   |
| Branch           Type         Target     Action    |  | Critical stockouts                |
| -------------------------------------------------- |  | Review urgent PO queue   [Open]   |
| Kamakhya Gate    Transit      ₹58,000    Inspect   |  |                                   |
| Dharapur         Suburban     ₹52,000    Inspect   |  | 90-day distributor returns        |
| Azara            Hospital     ₹64,000    Inspect   |  | 12 lots eligible credit  [Audit]  |
| Rani Gate        Residential  ₹48,000    Inspect   |  |                                   |
+----------------------------------------------------+  +-----------------------------------+
```

### Design Rules
- **Pure numeric KPI cards:** Label + tabular monospace figure + explicit comparison context (`+2.9% vs target`). No decorative icons or mini sparklines.
- **Asymmetric 2-column split below KPIs** (`lg:grid-cols-12`: 8 cols branch table + 4 cols operational action panel) to avoid repetitive equal-width card rows.

---

## 3. Route 2: Branch Shelf Telemetry (`/inventory`)

- **Primary Audience:** Floor Pharmacist
- **API Bindings:**
  - `GET /api/v1/inventory/branches/{branch_id}?category=&abc_class=&limit=50&offset=0`
  - `GET /api/v1/sales/history?branch_id={id}&medicine_id={med_id}&days=30` (on row click)

### Layout Wireframe
```text
[ Search brand or generic salt ]   [ Category: All v ]   [ All | Class A | Class B | Class C ]

+---------------------------------------------------------------------------------------------+
| Medicine               Category        ABC   On hand  Pending  7d fcst   Cover      Status  |
| ------------------------------------------------------------------------------------------- |
| Dolo 650               Analgesic       [A]     45.0      0.0     56.4    5.6d [== ] Below ROP|
| Paracetamol                                                                                 |
| Telma 40               Cardiovascular  [A]     15.0      0.0     70.0    1.5d [=  ] Below ROP|
| Telmisartan                                                                                 |
| Augmentin 625 Duo      Antibiotic      [A]    120.0     30.0     49.1   17.1d [===] Healthy  |
| Amoxicillin + Clav.                                                                         |
+---------------------------------------------------------------------------------------------+
Showing 1–50 of 129 items                                                [ Previous ] [ Next ]
```

### Signature Detail: Days-of-Cover ($DoC$) Indicator
- Compact `48px` horizontal calibrated track next to the monospace value (`1.5d`, `5.6d`, `17.1d`):
  - `<= 2.0d`: Crimson bar (`--status-critical-ink`)
  - `2.1d – 6.9d`: Amber bar (`--status-warning-ink`)
  - `>= 7.0d`: Emerald bar (`--status-healthy-ink`)

### Interactive Slide-Over: `SkuSalesDrawer`
- Clicking any table row opens a `480px` right-hand `SlideOver` without losing table scroll position.
- Displays:
  - Medicine header (`brand_name`, `generic_salt`, `dosage_form`, `medicine_id`).
  - Compact 3-metric strip: `Current stock`, `Reorder point`, `7-day demand forecast`.
  - **Focal Craft Moment 1:** 30-day Recharts area/line chart of `units_sold` on a muted hairline grid (`--border-hairline`), single clinical teal stroke (`#0F766E`), with red point markers highlighting any day where `is_stockout_flag === true`.

---

## 4. Route 3: Purchase Order Approval Workbench (`/replenishment`)

- **Primary Audience:** Floor Pharmacist / Store Manager
- **API Bindings:**
  - `GET /api/v1/recommendations/replenish?branch_id={id}&urgency=&supplier_id=`
  - `POST /api/v1/orders/approve`

### Layout Wireframe
```text
[ All (8) | Critical (2) | Reorder (6) ]        Recommended spend: ₹34,520.00   [Approve 2 selected]

+---------------------------------------------------------------------------------------------+
| [x] Medicine / Supplier         Stock / ROP    7d fcst   Order qty (edit)   Est. cost  Tier |
| ------------------------------------------------------------------------------------------- |
| [x] Augmentin 625 Duo             8 / 28         49.1    [  60  ] units     ₹8,520.00  Crit |
|     Guwahati Medico · 0.5d lead                          Rounded: 6 boxes of 10             |
|     └─ Rationale: Current stock (8) covers 1.1 days; supplier takes 0.5 days...             |
|                                                                                             |
| [x] Telma 40                     15 / 38         70.0    [  90  ] units    ₹14,400.00  Crit |
|     Assam Drug Dist. · 1.5d lead                         Rounded: 3 packs of 30             |
|     └─ Rationale: Effective stock breached ROP (38). Forecasted 7-day demand is 70.0...     |
+---------------------------------------------------------------------------------------------+
```

### Interaction & Safety Rules
- **Focal Craft Moment 2:** Each item includes a crisp, subdued `RationaleProofBox` showing the deterministic math and pack-size rounding note in plain English—building pharmacist trust without hiding formulas.
- **Inline Quantity Editing:** Input validates strictly `approved_quantity_units > 0`. Entering `0` or a negative number disables approval and displays an inline validation message (`Quantity must be greater than zero`).
- **One-Click & Bulk Approval:** Clicking `Approve selected orders` sends `POST /api/v1/orders/approve`, receives `201 Created` with generated PO IDs (`PO-BR001-...`), displays a clean confirmation toast listing the PO number(s), and automatically refreshes the replenishment queue and inventory pending quantities.

---

## 5. Route 4: FEFO Batch Expiry & Return Audit (`/expiry`)

- **Primary Audience:** Store Manager / Regional Procurement Director
- **API Bindings:** `GET /api/v1/inventory/batches/expiry-risk?branch_id=<opt>&max_days_to_expiry=90`

### Layout Wireframe
```text
+--------------------------+--------------------------+--------------------------+
| Lots within return cutoff| Projected unsold units   | Write-off exposure       |
| 12 batches               | 340 units                | ₹48,200.00               |
| Expiry <= 90 days        | Based on 7d ML velocity  | Recoverable via credit   |
+--------------------------+--------------------------+--------------------------+

Horizon filter: [ <= 30 days | <= 60 days | <= 90 days (statutory) | <= 180 days ]

+---------------------------------------------------------------------------------------------+
| Batch / Medicine       Branch   Expiry date  Days left   Qty / Sold   Proj. loss  Action    |
| ------------------------------------------------------------------------------------------- |
| MLC-2024-8891          BR002    2026-12-15      58d      120 / 45      ₹9,750.00  Return    |
| Montair-LC                                                                                  |
| TL-2025-099            BR001    2027-01-08      45d      180 / 90     ₹14,400.00  Return    |
| Telma 40                                                                                    |
+---------------------------------------------------------------------------------------------+
```

### Action Labeling
- `IMMEDIATE_DISTRIBUTOR_RETURN` → Warning/Critical badge: `Distributor return`
- `FEFO_EXPEDITE` → Neutral/Amber badge: `FEFO front-row`
- Hovering or expanding a batch row reveals the full `action_rationale` returned by the FastAPI expiry audit engine.

---

## 6. Error, Offline & Empty State Contracts

| State | Visual Treatment | Copy Example |
| :--- | :--- | :--- |
| **FastAPI Unreachable** | Top inline alert banner (`--status-critical-bg`) with retry button | `Cannot reach RemediSync API at localhost:8000. Verify the backend server is running.` `[Retry connection]` |
| **API 404 / 422 Error** | Parses FastAPI uniform envelope and surfaces `code`, `message`, and `correlation_id` | `Branch BR999 does not exist in master records. Reference: req-98fbc12e` |
| **Empty Filter Result** | Centered quiet `EmptyState` inside table container | `No medicines match "xyz" in Cardiovascular.` `[Clear filters]` |
| **Zero Pending Reorders** | Calm healthy confirmation state | `All SKUs at Kamakhya Gate Branch are above reorder points.` |
