# RemediSync: RESTful API Specification (OpenAPI Contract)

## 1. API Architecture & Standards

The RemediSync backend exposes a high-performance RESTful API developed with **FastAPI** and **Pydantic v2**. 

### 1.1 Base Conventions
- **Base URL:** `http://localhost:8000/api/v1` (Production: `https://api.remedisync.internal/api/v1`)
- **Protocol:** HTTP/1.1 and HTTP/2 over TLS 1.3
- **Payload Format:** `application/json; charset=utf-8`
- **Interactive Documentation:** Automated Swagger UI exposed at `/docs`; Redoc at `/redoc`.

### 1.2 Standard HTTP Status Codes
| Status Code | Semantics |
| :--- | :--- |
| `200 OK` | Request succeeded; response payload returned. |
| `201 Created` | Resource created (e.g. Purchase Order approved). |
| `400 Bad Request` | Client validation failed (e.g. invalid date format or negative order quantity). |
| `404 Not Found` | Entity not found (e.g. invalid `branch_id` or `medicine_id`). |
| `422 Unprocessable Entity` | Pydantic schema validation failure. |
| `500 Internal Error` | Unhandled server error; logged with unique correlation ID. |

### 1.3 Uniform Error Response Envelope
```json
{
  "success": false,
  "error": {
    "code": "INVALID_BRANCH_ID",
    "message": "Branch BR999 does not exist in master records.",
    "timestamp": "2026-10-18T19:55:00Z",
    "correlation_id": "req-98fbc12e"
  }
}
```

---

## 2. Core Endpoint Specifications

### 2.1 System Health & Diagnostics
#### `GET /health`
Returns system liveness, database connection status, and model inference status.

**Response `200 OK`:**
```json
{
  "status": "HEALTHY",
  "version": "1.0.0",
  "uptime_seconds": 86420,
  "database": "CONNECTED",
  "active_model": {
    "name": "HistGradientBoostingForecaster",
    "version": "v1.2.0",
    "trained_date": "2026-10-03"
  }
}
```

---

### 2.2 Executive & Network Analytics
#### `GET /analytics/overview`
Retrieves consolidated business KPIs across all pharmacy branches.

**Query Parameters:**
- `branch_id` *(optional, string)*: Filter to specific branch (e.g. `BR001`). Omit for network total.
- `days` *(optional, integer, default: 30)*: Number of past days to aggregate.

**Response `200 OK`:**
```json
{
  "network_daily_revenue_inr": 226534.59,
  "target_daily_revenue_inr": 220000.00,
  "performance_ratio": 1.029,
  "network_stockout_rate": 0.018,
  "active_branches_count": 4,
  "total_skus_tracked": 129,
  "critical_stockouts_count": 3,
  "near_expiry_batches_count": 12,
  "estimated_near_expiry_value_inr": 48200.00
}
```

---

### 2.3 Branch Inventory & Shelf Telemetry
#### `GET /inventory/branches/{branch_id}`
Returns granular current stock, days of cover, and velocity metrics for all SKUs at a branch.

**Query Parameters:**
- `category` *(optional, string)*: Filter by therapeutic category (e.g. `Cardiovascular`).
- `abc_class` *(optional, string)*: Filter by Pareto tier (`A`, `B`, `C`).
- `limit` *(optional, integer, default: 50)*
- `offset` *(optional, integer, default: 0)*

**Response `200 OK`:**
```json
{
  "branch_id": "BR001",
  "branch_name": "Kamakhya Gate Branch",
  "total_records": 129,
  "items": [
    {
      "medicine_id": "MED001",
      "brand_name": "Dolo 650",
      "generic_salt": "Paracetamol",
      "category": "Analgesic",
      "dosage_form": "TABLET",
      "current_stock_units": 45.0,
      "pending_order_units": 0.0,
      "predicted_7d_demand": 56.4,
      "days_of_cover": 5.6,
      "reorder_point": 65.0,
      "is_below_rop": true,
      "abc_class": "A",
      "demand_pattern": "Smooth"
    }
  ]
}
```

---

### 2.4 Replenishment Recommendations
#### `GET /recommendations/replenish`
Generates prioritized, mathematically transparent purchase recommendations.

**Query Parameters:**
- `branch_id` *(required, string)*: Branch identifier (`BR001` to `BR004`).
- `urgency` *(optional, string)*: Filter by urgency (`CRITICAL`, `WARNING`, `OPTIMAL`).
- `supplier_id` *(optional, string)*: Filter by supplier.

**Response `200 OK`:**
```json
{
  "branch_id": "BR001",
  "generated_at": "2026-10-18T19:55:00Z",
  "total_recommended_orders": 8,
  "total_estimated_expenditure_inr": 34520.00,
  "recommendations": [
    {
      "medicine_id": "MED019",
      "brand_name": "Augmentin 625 Duo",
      "primary_supplier_id": "SUP004",
      "primary_supplier_name": "Guwahati Medico Stockists",
      "supplier_fulfillment_tier": "EXPRESS_PICKUP",
      "lead_time_days": 0.5,
      "current_stock_units": 8.0,
      "pending_order_units": 0.0,
      "predicted_7d_demand": 49.1,
      "safety_stock_units": 12.0,
      "reorder_point": 28.0,
      "recommended_order_units": 60.0,
      "unit_cost_price": 142.00,
      "estimated_cost_inr": 8520.00,
      "pack_size_rounding": "Rounded from 53.1 to 60 units (6 boxes of 10)",
      "urgency": "CRITICAL",
      "calculation_rationale": "Current stock (8) is below ROP (28). Forecasted demand is 49.1 units over 7 days with 12 units safety buffer."
    }
  ]
}
```

---

### 2.5 Order Execution & Persistence
#### `POST /orders/approve`
Approves a recommended replenishment order, creates an immutable PO record, and increments `pending_order_quantity`.

**Request Body:**
```json
{
  "branch_id": "BR001",
  "orders": [
    {
      "medicine_id": "MED019",
      "supplier_id": "SUP004",
      "approved_quantity_units": 60.0,
      "notes": "Emergency courier dispatch approved by floor pharmacist"
    }
  ]
}
```

**Response `201 Created`:**
```json
{
  "success": true,
  "orders_created": [
    {
      "order_id": "PO-BR001-20261018-001",
      "medicine_id": "MED019",
      "approved_units": 60.0,
      "estimated_cost_inr": 8520.00,
      "status": "APPROVED",
      "created_at": "2026-10-18T19:56:00Z"
    }
  ]
}
```

---

### 2.6 Batch Expiry & Waste Risk Alerts
#### `GET /inventory/batches/expiry-risk`
Scans lot-level inventory and identifies batches approaching the 90-day return deadline or with demand insufficient to deplete stock prior to expiration.

**Query Parameters:**
- `branch_id` *(optional, string)*
- `max_days_to_expiry` *(optional, integer, default: 90)*

**Response `200 OK`:**
```json
{
  "total_at_risk_batches": 4,
  "total_write_off_exposure_inr": 18450.00,
  "batches": [
    {
      "batch_id": "BAT0089",
      "branch_id": "BR002",
      "medicine_id": "MED053",
      "brand_name": "Montair-LC",
      "batch_number": "MLC-2024-8891",
      "expiry_date": "2026-12-15",
      "days_to_expiry": 58,
      "current_quantity_units": 120,
      "predicted_demand_before_expiry": 45.0,
      "projected_unsold_units": 75.0,
      "projected_loss_inr": 9750.00,
      "recommended_action": "IMMEDIATE_DISTRIBUTOR_RETURN",
      "action_rationale": "Batch expires in 58 days (< 90-day return cutoff). Projected sales of 45 units will leave 75 units unsold."
    }
  ]
}
```
