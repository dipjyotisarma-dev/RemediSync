# Architecture Decision Records (ADR Ledger)

This document records the key architectural and design decisions made for **RemediSync**, following the standard MADR (Markdown Architectural Decision Records) structure: **Context, Alternatives Considered, Decision Outcome, and Trade-Offs**.

---

## ADR-001: Monorepo Structure with Direct Module Ingestion

- **Status:** ACCEPTED
- **Date:** September 24, 2026
- **Deciders:** Principal Systems Architect, Lead Backend Engineer

### Context
RemediSync requires tight cohesion between the quantitative machine learning pipeline (`src/features`, `src/models`), the deterministic inventory decision engine (`src/decision`), the REST API layer (`src/api`), and the management user interface (`frontend/`). We considered splitting the ML pipeline and web application into separate GitHub repositories.

### Alternatives Considered
1. **Multi-Repo Architecture:** A repository for the ML model/feature pipelines and a separate repository for FastAPI + React.
2. **Monorepo Architecture:** A single unified repository housing `src/` (ML + Backend) and `frontend/` (React/Vite).

### Decision Outcome
We selected a **Monorepo Architecture**. 
This enables the FastAPI backend service to import feature transformers, demand profilers, and decision engine modules directly (`from src.decision.order_generator import OrderGenerator`) with zero packaging overhead, while isolating React web dependencies inside the `frontend/` directory.

### Consequences & Trade-Offs
- **Pros:** Zero API lag between model updates and backend services; synchronized testing across feature engineering and API routes; simplified single-command Docker Compose orchestration.
- **Cons:** Repository clone size is slightly larger; requires careful `.gitignore` management to prevent virtual environment and local datasets from polluting Git history.

---

## ADR-002: Strict Mathematical Decoupling of Forecasting and Replenishment

- **Status:** ACCEPTED
- **Date:** September 24, 2026
- **Deciders:** Lead ML Engineer, Director of Supply Chain

### Context
In naive inventory AI projects, machine learning models are trained directly to output suggested order quantities ($Q$). 

### Alternatives Considered
1. **End-to-End Black-Box ML:** Train a model to predict order quantities directly from sales history and current stock.
2. **Decoupled Two-Stage Architecture:** 
   - **Stage 1 (Probabilistic ML):** Predicts 7-day cumulative customer demand ($\hat{Y}_{m,b}^{(7)}$).
   - **Stage 2 (Deterministic Operations Research):** Applies safety stock, reorder point, distributor lead times, pack size rounding, and budget ceilings.

### Decision Outcome
We adopted the **Decoupled Two-Stage Architecture**. 
The machine learning forecaster is strictly an estimator of consumer demand. The replenishment engine is an operational controller applying validated inventory balancing formulas.

### Consequences & Trade-Offs
- **Pros:** Full mathematical explainability (pharmacists receive clear calculation rationale for every single order); physical supply chain constraints (MOQs, pack sizes, budgets) are guaranteed without model hallucinations; forecasting models can be upgraded independently.
- **Cons:** Requires maintaining two distinct subsystems (an ML pipeline and a decision engine).

---

## ADR-003: Apache Parquet Columnar Storage for Feature Store

- **Status:** ACCEPTED
- **Date:** October 3, 2026
- **Deciders:** Lead Data Engineer, Principal Architect

### Context
The Feature Engineering Pipeline produces a 311,148-row, 31-column matrix containing multi-horizon lags, rolling statistics, and temporal encodings. Storing intermediate training data in standard CSV files incurred heavy I/O overhead and lost datatype fidelity (e.g., float precision loss, date parsing overhead).

### Alternatives Considered
1. **Raw CSV Files (`.csv` / `.csv.gz`)**
2. **SQLite Database Table**
3. **Apache Parquet Columnar File (`.parquet`)**

### Decision Outcome
We selected **Apache Parquet** (utilizing `pyarrow`).

### Consequences & Trade-Offs
- **Pros:** File size compressed from ~42 MB down to **8.6 MB** on disk; loading speed into pandas/scikit-learn is over 10x faster; exact numeric dtypes and datetime timestamps are strictly preserved.
- **Cons:** Parquet is a binary format that cannot be viewed in plain text editors without parquet viewing extensions or Python scripts.

---

## ADR-004: Inclusion of Batch Lot Numbers and Expiry Intelligence in Version 1

- **Status:** ACCEPTED
- **Date:** September 26, 2026
- **Deciders:** Head of Product, Chief Pharmacist

### Context
Standard retail inventory MVP roadmaps defer batch numbers and expiration dates to Version 2. However, in Indian retail pharmacy operations, expired medicines generate a 2.5%–4.0% annual write-off loss, and near-expiry stock must be returned to stockists at least 90 days prior to expiration to receive full credit.

### Alternatives Considered
1. **Defer to Version 2:** Treat inventory strictly as aggregate unit counts in Version 1.
2. **Promote to Version 1 Core:** Track explicit batch lot numbers, manufacturing dates, and expiry dates, and build predictive waste alerts directly into the replenishment engine.

### Decision Outcome
We **promoted Batch Expiry & Waste Intelligence into Version 1**.
The synthetic generator creates 808 realistic batches with stratified expiry windows, and the replenishment engine flags any lot whose remaining shelf life is shorter than its predicted depletion velocity.

### Consequences & Trade-Offs
- **Pros:** Differentiates RemediSync from generic retail inventory tools; solves one of the highest financial pain points of pharmacy owners on day one.
- **Cons:** Increases data schema complexity; requires tracking inventory at both the SKU level and the lot level.

---

## ADR-005: Strict Chronological Walk-Forward Validation Protocol

- **Status:** ACCEPTED
- **Date:** September 29, 2026
- **Deciders:** Lead ML Engineer, Quantitative Statistician

### Context
Standard machine learning cross-validation splits datasets randomly ($K$-fold cross-validation). In time-series forecasting, randomly shuffling rows leaks future information into past predictions ("lookahead bias"), yielding deceptively high test scores that collapse in production.

### Alternatives Considered
1. **Random $K$-Fold Cross-Validation:** Standard scikit-learn train/test shuffle.
2. **Chronological Walk-Forward Backtesting:** Strictly train on historical dates $t_0 \to t_{\text{split}}$ and evaluate exclusively on unseen future dates $t_{\text{split}} \to t_{\text{end}}$.

### Decision Outcome
We enforce **Chronological Walk-Forward Backtesting** with a strict `.shift(1)` temporal observation boundary. Any feature at date $t$ must only use information available at date $t-1$ or earlier.

### Consequences & Trade-Offs
- **Pros:** Completely prevents data leakage; ensures test evaluation metrics mirror real-world production performance.
- **Cons:** Requires custom splitting logic and drops the initial warm-up period (first 28 days of history).

---

## ADR-006: Selection of WAPE Over MAPE as Primary Accuracy Metric

- **Status:** ACCEPTED
- **Date:** October 3, 2026
- **Deciders:** Lead ML Engineer, Supply Chain Director

### Context
Mean Absolute Percentage Error (MAPE) is widely taught in academic settings:
$$\text{MAPE} = \frac{100\%}{n} \sum \left| \frac{y - \hat{y}}{y} \right|$$
However, in retail pharmacy datasets, many specialized SKUs experience zero-sales days ($y = 0$), causing division by zero, or low-sales days ($y = 1, \hat{y} = 3$), which produces a distorted $200\%$ error on a negligible discrepancy of 2 tablets.

### Alternatives Considered
1. **MAPE (Mean Absolute Percentage Error)**
2. **RMSE (Root Mean Squared Error)**
3. **WAPE (Weighted Absolute Percentage Error)**

### Decision Outcome
We adopted **WAPE (Weighted Absolute Percentage Error)** as the primary metric:
$$\text{WAPE} = \frac{\sum_{i=1}^n |y_i - \hat{y}_i|}{\sum_{i=1}^n y_i}$$

### Consequences & Trade-Offs
- **Pros:** Highly robust to intermittent demand and low-volume counts; naturally weights errors by product volume; aligns directly with working capital impact.
- **Cons:** Less familiar to non-technical stakeholders who are accustomed to standard percentage error terminology.
