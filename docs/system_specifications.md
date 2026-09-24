# RemediSync: System & Domain Specifications
## 1. Executive Summary
Community and multi-branch retail pharmacies face persistent friction in inventory balance: unfulfilled prescriptions due to reactive ordering, contrasted with idle capital trapped in slow-moving pharmaceuticals. RemediSync provides automated, decision-support replenishment based on predictive demand modeling.
## 2. Domain Entities
The system operates on five core relational entities:
- **SKU (Medicine):** Chemical formulation, packaging unit, unit procurement cost, and retail price.
- **Branch:** Autonomous physical dispensing location with distinct local demand demographics.
- **Supplier:** Distribution vendor characterized by deterministic order lead times and order batch constraints.
- **Sales Transaction:** Timestamped dispensing event capturing realized customer demand.
- **Inventory Ledger:** Real-time stock levels, pending supplier shipments, and historical stockout events.
## 3. Core Architectural Boundaries
To maintain software reliability and clean separation of concerns:
1. **The Statistical Forecasting Engine (`src/models/`):** Responsible exclusively for modeling and predicting continuous latent customer demand over a 7-day rolling horizon.
2. **The Inventory Decision Engine (`src/engine/`):** Ingests demand forecasts along with live operational constraints (on-hand stock, supplier lead times, target service level $\alpha$) to calculate concrete reorder quantities and urgency classifications.