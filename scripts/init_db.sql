-- ==============================================================================
-- REMEDISYNC: POSTGRESQL RELATIONAL SCHEMA SPECIFICATION
-- Target: Local pgAdmin 4 / Production Supabase (PostgreSQL 16+)
-- ==============================================================================

-- 1. Master Dimensions: branches & suppliers
CREATE TABLE IF NOT EXISTS branches (
    branch_id VARCHAR(16) PRIMARY KEY,
    branch_name VARCHAR(128) NOT NULL,
    location_type VARCHAR(64) NOT NULL,
    daily_target_revenue NUMERIC(12, 2) NOT NULL DEFAULT 50000.00,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id VARCHAR(16) PRIMARY KEY,
    supplier_name VARCHAR(128) NOT NULL,
    contact_phone VARCHAR(32) NOT NULL DEFAULT '+91-361-2540001',
    city_hub VARCHAR(64) NOT NULL,
    lead_time_days NUMERIC(4, 2) NOT NULL DEFAULT 1.00,
    fulfillment_tier VARCHAR(32) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Master Catalog: medicines
CREATE TABLE IF NOT EXISTS medicines (
    medicine_id VARCHAR(16) PRIMARY KEY,
    brand_name VARCHAR(128) NOT NULL,
    generic_salt VARCHAR(256) NOT NULL,
    strength VARCHAR(64) NOT NULL,
    dosage_form VARCHAR(64) NOT NULL,
    category VARCHAR(64) NOT NULL,
    manufacturer VARCHAR(128) NOT NULL,
    mrp NUMERIC(10, 2) NOT NULL,
    cost_price NUMERIC(10, 2) NOT NULL,
    pack_size VARCHAR(64) NOT NULL,
    units_per_pack INTEGER NOT NULL DEFAULT 10,
    primary_supplier_id VARCHAR(16) NOT NULL REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
    is_cold_chain BOOLEAN NOT NULL DEFAULT FALSE,
    schedule_type VARCHAR(16) NOT NULL DEFAULT 'SCHEDULE_H',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_medicines_category ON medicines(category);
CREATE INDEX IF NOT EXISTS idx_medicines_supplier ON medicines(primary_supplier_id);

-- 3. Lot-Level Batch Tracking: batches (FEFO Support)
CREATE TABLE IF NOT EXISTS batches (
    batch_id VARCHAR(32) PRIMARY KEY,
    medicine_id VARCHAR(16) NOT NULL REFERENCES medicines(medicine_id) ON DELETE RESTRICT,
    branch_id VARCHAR(16) NOT NULL REFERENCES branches(branch_id) ON DELETE CASCADE,
    batch_number VARCHAR(64) NOT NULL,
    mfg_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    initial_quantity INTEGER NOT NULL,
    current_quantity INTEGER NOT NULL CHECK (current_quantity >= 0),
    unit_cost_price NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_branch_batch UNIQUE (branch_id, medicine_id, batch_number)
);

CREATE INDEX IF NOT EXISTS idx_batches_expiry ON batches(expiry_date ASC);
CREATE INDEX IF NOT EXISTS idx_batches_branch_med ON batches(branch_id, medicine_id);

-- 4. Transactional Telemetry: daily_sales
CREATE TABLE IF NOT EXISTS daily_sales (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    branch_id VARCHAR(16) NOT NULL REFERENCES branches(branch_id) ON DELETE CASCADE,
    medicine_id VARCHAR(16) NOT NULL REFERENCES medicines(medicine_id) ON DELETE RESTRICT,
    units_sold NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (units_sold >= 0),
    unit_price NUMERIC(10, 2) NOT NULL,
    total_revenue NUMERIC(12, 2) NOT NULL,
    is_stockout BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_daily_sales_series_date UNIQUE (branch_id, medicine_id, date)
);

CREATE INDEX IF NOT EXISTS idx_sales_branch_med_date ON daily_sales(branch_id, medicine_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_sales_date ON daily_sales(date DESC);

-- 5. Operational State: inventory_snapshots
CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id BIGSERIAL PRIMARY KEY,
    branch_id VARCHAR(16) NOT NULL REFERENCES branches(branch_id) ON DELETE CASCADE,
    medicine_id VARCHAR(16) NOT NULL REFERENCES medicines(medicine_id) ON DELETE RESTRICT,
    current_stock NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (current_stock >= 0),
    last_replenished_date DATE,
    pending_order_quantity NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_snapshot_branch_med UNIQUE (branch_id, medicine_id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_branch ON inventory_snapshots(branch_id);

-- 6. Decision Engine Operational Orders: replenishment_orders
CREATE TABLE IF NOT EXISTS replenishment_orders (
    order_id VARCHAR(32) PRIMARY KEY,
    branch_id VARCHAR(16) NOT NULL REFERENCES branches(branch_id) ON DELETE RESTRICT,
    supplier_id VARCHAR(16) NOT NULL REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
    medicine_id VARCHAR(16) NOT NULL REFERENCES medicines(medicine_id) ON DELETE RESTRICT,
    predicted_demand_7d NUMERIC(10, 2) NOT NULL,
    safety_stock_units NUMERIC(10, 2) NOT NULL,
    recommended_order_units NUMERIC(10, 2) NOT NULL,
    approved_order_units NUMERIC(10, 2),
    estimated_total_cost NUMERIC(12, 2) NOT NULL,
    urgency_status VARCHAR(16) NOT NULL CHECK (urgency_status IN ('CRITICAL', 'REORDER', 'HEALTHY', 'OVERSTOCKED')),
    order_status VARCHAR(16) NOT NULL DEFAULT 'PENDING_APPROVAL' CHECK (order_status IN ('PENDING_APPROVAL', 'APPROVED', 'DISPATCHED', 'REJECTED')),
    calculation_rationale TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_orders_status_urgency ON replenishment_orders(order_status, urgency_status);
CREATE INDEX IF NOT EXISTS idx_orders_branch_created ON replenishment_orders(branch_id, created_at DESC);
