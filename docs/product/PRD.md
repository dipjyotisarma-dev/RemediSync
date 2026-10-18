# RemediSync: Product Requirements Document (PRD)

## 1. Executive Summary
**RemediSync** is an enterprise-grade predictive demand forecasting and automated replenishment intelligence platform designed specifically for multi-branch retail pharmacy chains. 

Independent and regional pharmacy chains operate on razor-thin margins (typically 12%–18% gross margin) while balancing two conflicting operational threats:
1. **Prescription Stockouts:** Failing to fulfill a customer's prescription drives them to a competitor and destroys customer lifetime value (LTV), especially for chronic disease treatments (diabetes, cardiovascular, hypertension).
2. **Dead Working Capital & Expiry Write-Offs:** Over-ordering ties up limited cash flow in slow-moving inventory and leads to catastrophic expired stock losses.

RemediSync bridges probabilistic machine learning demand forecasts with deterministic inventory replenishment equations to deliver automated, transparent, batch-aware purchasing recommendations to store pharmacists and procurement directors.

---

## 2. Problem Statement & Market Reality

### 2.1 The Traditional Pharmacy Operational Dilemma
Most independent pharmacy chains in India and emerging markets rely on manual, intuitive "eyeball" inventory ordering:
- Store floor pharmacists walk the aisles in the evening, check shelf levels by hand, and scribble distributor orders into a notepad or WhatsApp chat.
- Order quantities are based on gut feeling rather than demand velocity, seasonal illness patterns, or distributor lead times.
- Payday refill waves (the 1st through 7th of every month, where chronic patients purchase 30-day supplies) consistently catch stores understocked.
- Near-expiry medicines sit unnoticed at the back of shelves until they cross the distributor return cutoff (typically 90 days prior to expiration), turning into a 100% financial write-off.

### 2.2 Quantified Business Pain Points
- **Uncaptured Demand:** 6%–11% of daily customer footfalls experience partial prescription fulfillment due to stockouts.
- **Working Capital Inefficiency:** 20%–30% of working capital is trapped in slow-moving (Pareto Class C) medications.
- **Expiry Losses:** 2.5%–4.0% of total annual inventory purchasing cost is lost to unsold expired stock.

---

## 3. Product Vision & Success Metrics (KPIs)

### 3.1 Vision
To give independent retail pharmacy chains the same predictive inventory intelligence and algorithmic procurement precision utilized by multi-billion-dollar national pharmaceutical retail networks.

### 3.2 Target Success Metrics
| Metric | Industry Baseline (Manual) | RemediSync Target | Measurement Method |
| :--- | :--- | :--- | :--- |
| **Prescription Stockout Rate** | 8.5% of demand events | **< 2.5%** | Percentage of customer transaction requests unfulfilled |
| **Inventory Turnover Ratio** | 5.2 turns/year | **> 8.0 turns/year** | Annual Cost of Goods Sold (COGS) / Average Inventory |
| **Predictive Expiry Losses** | 3.2% of purchasing cost | **< 0.8%** | Total value of expired stock written off per annum |
| **Forecast Accuracy (WAPE)** | ~45% (Intuitive guesswork) | **< 22.0%** | Weighted Absolute Percentage Error on 7-day cumulative demand |
| **Procurement Time** | 2.5 hours / branch / day | **< 15 minutes / day** | Time spent generating, reviewing, and approving distributor POs |

---

## 4. User Personas & Core Journeys

### Persona A: Floor Pharmacist (In-Store Operator)
- **Role:** Handles counter sales, receives distributor shipments, and oversees daily shelf stock.
- **Pain Point:** Frustrated when turning away loyal chronic patients due to out-of-stock Dolo 650, Telma 40, or Glycomet; stressed by manual stock audits.
- **User Journey in RemediSync:**
  1. Opens RemediSync Store Dashboard at morning opening.
  2. Reviews the **Daily Replenishment Alert Feed** (highlighting critical stockouts and reorder thresholds).
  3. Reviews one-click pre-calculated purchase orders sorted by urgency (`CRITICAL`, `WARNING`, `OPTIMAL`).
  4. Approves or adjusts order quantities with transparent reasoning displayed (e.g., *"Recommended: 20 strips. Reason: 7-day predicted demand is 18.5 strips + 4 strips safety stock - 2 strips on hand"*).

### Persona B: Regional Procurement Director (Chain Executive)
- **Role:** Manages master distributor relationships, negotiates bulk credit terms, and allocates capital across all network branches.
- **Pain Point:** Lacks centralized visibility into cross-branch stock velocity; cannot identify which branch has excess stock that another branch desperately needs.
- **User Journey in RemediSync:**
  1. Opens the **Executive Network Overview**.
  2. Inspects network-wide revenue velocity, aggregate stockout risks, and working capital allocation.
  3. Reviews the **Predictive Expiry Risk Queue** across all 4 branches to identify batches nearing the 90-day return window.
  4. Dispatches consolidated purchase orders directly to primary suppliers.

---

## 5. Scope & Feature Boundaries

### 5.1 Version 1 (MVP Scope - Current Production Release)
- [x] **Data Ingestion & Integrity Engine:** Validation of multi-branch transactions, relational referential integrity, and time-series grid continuity.
- [x] **Syntetos-Boylan Demand Profiling:** Automated Croston matrix categorization (Smooth, Intermittent, Erratic, Lumpy) and Pareto ABC revenue segmentation.
- [x] **Leakage-Free Feature Store:** Multi-horizon lags (7, 14, 21, 28 days), rolling demand statistics, and cyclical calendar signals stored in Parquet format.
- [ ] **ML Forecasting Service:** Classical machine learning demand forecaster predicting 7-day cumulative forward customer demand.
- [ ] **Deterministic Replenishment Engine:** Calculation of dynamic Reorder Points (ROP), Safety Stock, and Recommended Purchase Quantities with full human-readable audit rationale.
- [ ] **Batch Expiry & Waste Intelligence:** Automated tracking of lot numbers, manufacturing dates, expiry tiers, and predictive waste alerts for batches with demand insufficient to deplete stock prior to expiration.
- [ ] **FastAPI Backend:** Secure REST API serving operational inventory endpoints, replenishment feeds, and analytics.
- [ ] **React Management Dashboard:** Production web application with Executive Overview, Branch Inventory View, and Order Replenishment Manager.

### 5.2 Out-of-Scope for Version 1 (Deferred to Version 2)
- Multi-echelon inter-branch automated stock transfers (transferring stock between branches rather than ordering from distributor).
- Deep Learning temporal architectures (LSTM, Temporal Fusion Transformers — scheduled for subsequent R&D sprint).
- Direct WhatsApp / EDI automated API dispatch to distributor ERPs (Version 1 provides exportable PDF/CSV purchase orders).
- Direct point-of-sale (POS) hardware receipt printing.

---

## 6. Non-Functional Requirements (NFRs)

### 6.1 Performance & Latency
- Dashboard analytics and recommendation feeds must load in **< 400ms**.
- Model batch inference across all 516 series ($129 \text{ medicines} \times 4 \text{ branches}$) must execute in **< 15 seconds**.
- Database query execution time for time-series aggregation must remain **< 50ms**.

### 6.2 Reliability & Availability
- Service availability target: **99.9% uptime** during operational store hours (08:00 to 22:00 IST).
- Zero data loss: All transactional snapshots and historical model forecasts backed up daily.

### 6.3 Security & Regulatory Standards
- Compliance with the Indian **Drugs and Cosmetics Act (1940)** for statutory Schedule H/H1 audit trails.
- Environment secrets, database credentials, and API tokens strictly isolated from source code.
