# Pharmacy Replenishment Playbook: Operational Policies & Inventory Mathematics

## 1. Domain Overview
In retail pharmacy operations, inventory management is not simply an exercise in minimizing holding cost—it is a critical public health and regulatory discipline. Unlike standard FMCG retail, pharmacy inventory carries strict shelf-life deadlines (batch expiration), statutory storage restrictions (cold-chain), legally mandated distribution schedules, and severe penalties for stocking out of life-saving therapeutics.

This document formalizes the mathematical models, regional distributor dynamics, and dispensing rules embedded in the RemediSync decision engine.

---

## 2. Inventory Replenishment Mathematics

RemediSync strictly separates **customer demand prediction** (handled by Machine Learning) from **purchase order generation** (handled by deterministic inventory balancing equations).

```
[ Current Stock on Hand (S) ]  +  [ Pending Orders in Transit (P) ]  vs  [ Reorder Point (ROP) ]
                                          │
                                 Is (S + P) <= ROP?
                                    ├── YES ──> Trigger Purchase Order (Q)
                                    └── NO  ──> Do Not Reorder (Optimal Cover)
```

### 2.1 Daily Effective Demand ($\mu_D$) and Volatility ($\sigma_D$)
Let $\hat{Y}_{m,b}^{(7)}$ denote the ML model's forecasted 7-day cumulative customer demand for medicine $m$ at branch $b$.
- Average forecasted daily demand:
  $$\hat{D}_{m,b} = \frac{\hat{Y}_{m,b}^{(7)}}{7}$$
- Demand standard deviation: $\sigma_D$ is estimated from the historical rolling standard deviation (`rolling_std_7` or `rolling_std_28`).

### 2.2 Safety Stock Formulation ($SS$)
Safety stock protects against two simultaneous stochastic variables: demand surges and distributor lead-time variance.

$$SS = Z \times \sqrt{L \cdot \sigma_D^2 + \hat{D}^2 \cdot \sigma_L^2}$$

Where:
- $Z$: Service factor corresponding to desired cycle service level ($CSL$).
- $L$: Distributor expected lead time in days.
- $\sigma_L$: Standard deviation of distributor lead time in days.
- $\hat{D}$: Expected daily demand.
- $\sigma_D$: Daily demand volatility.

#### Service Level Targets by Therapeutic Importance
| Category Type | Description | Target Service Level ($CSL$) | $Z$-Score |
| :--- | :--- | :--- | :--- |
| **Life-Saving / Critical Chronic** | Cardiovascular (Telmisartan), Antidiabetic (Metformin), Respiratory (Montelukast) | **98.0%** | **2.05** |
| **Acute Prescription** | Antibiotics (Augmentin, Azithromycin), Analgesics (Dolo 650) | **95.0%** | **1.65** |
| **Discretionary OTC & Supplements** | Multivitamins (Shelcal, Becosules), Antacids, Topical Creams | **90.0%** | **1.28** |

### 2.3 Reorder Point Formulation ($ROP$)
The Reorder Point is the threshold inventory level that triggers an immediate purchase order:

$$ROP = (\hat{D} \times L) + SS$$

Where:
- $(\hat{D} \times L)$: Expected customer demand during distributor replenishment lead time.
- $SS$: Calibrated safety stock buffer.

### 2.4 Recommended Order Quantity ($Q$)
When inventory on hand ($S$) plus pending orders in transit ($P$) falls below the $ROP$:

$$Q_{\text{raw}} = \max\left(0, (\hat{D} \times T) + SS - (S + P)\right)$$

Where $T$ is the review cycle horizon (standard 7 days in RemediSync).

#### Pack Size & Minimum Order Quantity (MOQ) Rounding:
Suppliers do not sell loose tablets; they sell full strips or manufacturer shipper boxes. 
Let $B_{\text{size}}$ be the supplier pack size (e.g., 10 strips per box, or 100 tablets per bottle):

$$Q = \left\lceil \frac{Q_{\text{raw}}}{B_{\text{size}}} \right\rceil \times B_{\text{size}}$$

---

## 3. Packaging & Dispensing Mechanics: The Loose Tablet Dilemma

### 3.1 The Indian Retail Counter Phenomenon
In Indian retail pharmacies, customers routinely request fractional quantities of a package:
- Customer A buys a full strip of Paracetamol (15 tablets).
- Customer B requests only 4 tablets because their prescription is for 2 days.
- The pharmacist cuts the blister strip with scissors and sells 4 loose tablets.

### 3.2 RemediSync Standard Accounting Unit
To prevent inventory accounting drift and negative stock states:
1. **Internal Atomic Unit:** All inventory balances ($S$, $P$) and historical sales transactions are converted to **Atomic Units** (Individual Tablets / Capsules / Milliliters).
   $$\text{Atomic Units} = \text{Packs Sold} \times \text{units\_per\_pack}$$
2. **Dispensing Layer:** Loose dispensing is tracked as fractional packs or raw atomic units.
3. **Purchasing Layer:** Procurement recommendations are converted back to full commercial blister packs or boxes using ceiling integer division.

---

## 4. Guwahati / Assam Distribution Dynamics

RemediSync is modeled against authentic retail logistics in Assam:

### 4.1 Supplier Fulfillment Tiers
1. **Tier 1: Express Hub Stockists (Panbazar / Paltanbazar, Guwahati):**
   - **Lead Time:** 0.25 to 0.5 days (2 to 6 hours).
   - **Logistics Mode:** Pharmacy sends two-wheeler runner for counter pickup.
   - **Cost Structure:** Net zero freight, slightly tighter credit terms (14-day cycle).
   - **SKUs:** Fast-moving acute items (Dolo 650, Augmentin, Pantoprazole).
2. **Tier 2: Regional Delivery Stockists (Paltanbazar / Jalukbari / Dispur):**
   - **Lead Time:** 1 to 2 days.
   - **Logistics Mode:** Distributor delivery van delivery route.
   - **Credit Terms:** Standard 21 to 30 days credit.
   - **SKUs:** High-value chronic, specialty dermatological, and bulk nutritional supplements.

### 4.2 Calendar Cyclicality & The Payday Refill Wave
- **The Payday Surge (1st to 7th of Every Month):**
  Salaried government employees, tea estate workers, and corporate staff in Guwahati receive monthly pay on the 1st. Chronic patients purchase their entire month's prescription in a single visit.
  - **Empirical Factor:** **+28% to +30% surge** in Cardiovascular, Antidiabetic, and Endocrine demand during days 1–7.
  - **Operational Rule:** Safety stock buffers for chronic medicines automatically expand by 25% on the 26th of the prior month to prevent stockouts on the 1st.
- **The Weekend Divergence:**
  - **Monday:** Doctor clinic consultation surge produces a **+20.4% surge** in acute prescriptions.
  - **Sunday:** Specialist OPD closures produce an **-18.0% drop** in customer footfalls.

---

## 5. Batch Expiry & Waste Mitigation: The FEFO Standard

### 5.1 First-Expired, First-Out (FEFO) Protocol
Retail pharmacies must never practice FIFO (First-In, First-Out). If a newly delivered shipment has a shorter shelf life than existing stock, the newly arrived stock must be dispensed first.

### 5.2 Expiry Risk Stratification
RemediSync classifies every stock lot into three operational urgency tiers:
1. **Critical Expiry (< 90 Days):**
   - **Action:** Triggers **Immediate Distributor Return Alert**. Under Indian pharma trade agreements, stockists accept returns for full credit or replacement if notified prior to the 90-day expiry threshold.
   - **Dispensing Action:** Displayed with high priority in counter dispensing view.
2. **Medium-Term Expiry (90 to 365 Days):**
   - **Action:** Monitored against predicted demand velocity. If $\text{Predicted Demand over Remaining Days} < \text{Batch Quantity}$, flag as **Predictive Waste Risk**.
3. **Long-Term Stable (> 365 Days):**
   - **Action:** Healthy inventory reserve.

### 5.3 Cold-Chain Storage Protocols
- **Insulins and Vaccines (e.g., Human Mixtard, Lantus):**
  Must maintain strictly between $2^\circ\text{C}$ and $8^\circ\text{C}$.
  - Stockout penalty is critical: Missing temperature logs or power failures require immediate batch quarantine.
  - Cold-chain SKUs carry a minimum 3-day lead time buffer to avoid expedited emergency shipments without verified cold-storage packaging.
