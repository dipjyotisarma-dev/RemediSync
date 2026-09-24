# RemediSync

**Enterprise Demand Forecasting & Inventory Replenishment Platform for Multi-Branch Pharmacy Networks.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production%20Ready-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://www.docker.com/)

---

## Overview

RemediSync is an inventory intelligence system engineered for retail pharmacy chains. It bridges the operational gap between historical dispensing trends and supplier purchase orders.

By combining time-series demand forecasting with dynamic inventory replenishment heuristics (Safety Stock, Reorder Point, and Lead Time Buffering), RemediSync enables pharmacy operators to:
- **Mitigate Stockout Risk:** Proactively identify critical stock depletion before supplier lead-time windows expire.
- **Optimize Working Capital:** Minimize dead inventory and holding costs for slow-moving pharmaceutical SKUs.
- **Automate Purchasing Decisions:** Convert statistical forecasts into actionable, vendor-ready purchase recommendations with transparent rationale.

---

## System Architecture

```text
Historical Sales Telemetry
           │
           ▼
[ Feature Pipeline ] ────────► Lag Analysis, Rolling Statistics, Temporal Encodings
           │
           ▼
[ Forecasting Engine ] ──────► 7-Day Cumulative Demand Estimation (Tree Ensembles)
           │
           ▼
[ Replenishment Engine ] ◄─── Supplier Lead Times, Current On-Hand Stock, Service Level Targets
           │
           ▼
[ Actionable Orders ] ───────► Production REST API (FastAPI) ──► Operations Dashboard (React)
```

---

## Repository Structure

```text
RemediSync/
├── data/                  # Telemetry storage (raw and processed feature stores)
├── src/
│   ├── data_generator/    # High-fidelity pharmacy market simulator
│   ├── features/          # Temporal feature engineering & data pipelines
│   ├── models/            # Forecasting algorithms, training loops & evaluation
│   ├── engine/            # Inventory optimization & replenishment logic
│   ├── api/               # FastAPI backend service & request schemas
│   └── db/                # Persistence layer & SQLAlchemy relational models
├── frontend/              # React + TypeScript inventory operations console
├── tests/                 # Unit, integration, and policy regression tests
├── docs/                  # Architectural specs and mathematical formulations
└── docker-compose.yml     # Multi-container service orchestration
```

---

## Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/<your-username>/RemediSync.git
cd RemediSync

# Set up virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install core dependencies
pip install -r requirements.txt
```
