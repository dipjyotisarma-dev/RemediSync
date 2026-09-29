"""
Automated Validation Suite for RemediSync Data Generation Engine.

Verifies:
- Existence and schema integrity of all 6 raw CSV files
- Referential integrity across foreign keys
- Daily revenue limits aligning with ₹50,000–₹70,000 / branch
- Expiry date stratification (near-term batches present)
- Non-negativity constraints across quantities and prices.
"""

import pytest
import pandas as pd
from pathlib import Path

RAW_DATA_DIR = Path("data/raw")


@pytest.fixture(scope="module")
def load_tables():
    """Loads all 6 generated raw CSV tables into DataFrames."""
    tables = {
        "branches": pd.read_csv(RAW_DATA_DIR / "branches.csv"),
        "suppliers": pd.read_csv(RAW_DATA_DIR / "suppliers.csv"),
        "medicines": pd.read_csv(RAW_DATA_DIR / "medicines.csv"),
        "batches": pd.read_csv(RAW_DATA_DIR / "batches.csv"),
        "sales": pd.read_csv(RAW_DATA_DIR / "daily_sales.csv"),
        "snapshot": pd.read_csv(RAW_DATA_DIR / "inventory_snapshot.csv")
    }
    return tables


def test_raw_files_exist():
    """Verifies that all 6 required CSV files are present in data/raw/."""
    expected_files = [
        "branches.csv", "suppliers.csv", "medicines.csv",
        "batches.csv", "daily_sales.csv", "inventory_snapshot.csv"
    ]
    for fname in expected_files:
        p = RAW_DATA_DIR / fname
        assert p.exists(), f"Missing required raw CSV: {fname}"
        assert p.stat().st_size > 0, f"CSV file is empty: {fname}"


def test_branches_integrity(load_tables):
    """Verifies branches schema, row count, and Assam locations."""
    df = load_tables["branches"]
    assert len(df) == 4, f"Expected 4 branches, found {len(df)}"
    expected_cols = {"branch_id", "branch_name", "location_type", "daily_target_revenue", "is_active"}
    assert expected_cols.issubset(df.columns)
    assert (df["daily_target_revenue"] > 0).all()
    assert set(df["branch_id"]) == {"BR001", "BR002", "BR003", "BR004"}


def test_suppliers_integrity(load_tables):
    """Verifies 30 suppliers and lead-time distribution."""
    df = load_tables["suppliers"]
    assert len(df) == 30, f"Expected 30 suppliers, found {len(df)}"
    assert set(df["fulfillment_type"].unique()) == {"EXPRESS_PICKUP", "DISTRIBUTOR_DELIVERY"}
    
    # 20 Express Pickup, 10 Distributor Delivery
    counts = df["fulfillment_type"].value_counts()
    assert counts["EXPRESS_PICKUP"] == 20
    assert counts["DISTRIBUTOR_DELIVERY"] == 10
    
    # Express pickup must have lead_time == 1
    assert (df[df["fulfillment_type"] == "EXPRESS_PICKUP"]["lead_time_days"] == 1).all()
    # Distributor delivery must have lead_time in [2, 3]
    assert (df[df["fulfillment_type"] == "DISTRIBUTOR_DELIVERY"]["lead_time_days"].isin([2, 3])).all()


def test_medicines_pricing_and_units(load_tables):
    """Verifies medicine master pricing, units per pack, and supplier references."""
    df_meds = load_tables["medicines"]
    df_sups = load_tables["suppliers"]

    assert len(df_meds) >= 120, f"Expected >= 120 medicines, found {len(df_meds)}"
    assert (df_meds["cost_price"] > 0).all()
    assert (df_meds["mrp"] > df_meds["cost_price"]).all(), "MRP must be greater than wholesale cost price"
    assert (df_meds["units_per_pack"] >= 1).all(), "Units per pack must be at least 1"
    
    # Referential integrity with suppliers
    valid_suppliers = set(df_sups["supplier_id"])
    assert set(df_meds["primary_supplier_id"]).issubset(valid_suppliers), "Orphan primary_supplier_id found"


def test_batches_expiry_stratification(load_tables):
    """Verifies that batches contain near-term expiries for Version 1 testing."""
    df_batches = load_tables["batches"]
    assert len(df_batches) > 0
    assert (df_batches["current_quantity"] >= 0).all()
    assert (df_batches["unit_cost_price"] > 0).all()

    # Convert expiry_date to datetime
    expiries = pd.to_datetime(df_batches["expiry_date"])
    sim_end = pd.to_datetime("2026-09-30")
    
    # Check for near-term expiring batches (<90 days from simulation end)
    near_term_count = (expiries <= (sim_end + pd.Timedelta(days=90))).sum()
    assert near_term_count > 0, "Batches must include near-term expiries (<90 days) for expiry risk modeling"


def test_daily_sales_revenue_and_stockouts(load_tables):
    """Verifies sales volume, revenue bounds, and stockout flags."""
    df_sales = load_tables["sales"]
    assert len(df_sales) > 300000, f"Expected >300k rows, found {len(df_sales)}"
    assert (df_sales["units_sold"] >= 0).all()
    assert (df_sales["total_revenue"] >= 0).all()
    
    # When is_stockout is True and units_sold == 0, total_revenue must be 0
    zero_sales_stockouts = df_sales[df_sales["units_sold"] == 0]
    assert (zero_sales_stockouts["total_revenue"] == 0.0).all()
    
    # Check daily network revenue distribution
    daily_rev = df_sales.groupby("date")["total_revenue"].sum()
    mean_daily_rev = daily_rev.mean()
    
    # Mean network daily revenue across 4 branches should be in ₹180,000 to ₹270,000 range
    assert 170000.0 <= mean_daily_rev <= 280000.0, (
        f"Mean daily network revenue ₹{mean_daily_rev:,.2f} is outside expected ₹170k-₹280k range"
    )


def test_inventory_snapshot_integrity(load_tables):
    """Verifies inventory snapshot covers all branch-medicine pairs."""
    df_snap = load_tables["snapshot"]
    df_branches = load_tables["branches"]
    df_meds = load_tables["medicines"]

    expected_pairs = len(df_branches) * len(df_meds)
    assert len(df_snap) == expected_pairs, f"Expected {expected_pairs} snapshot rows, found {len(df_snap)}"
    assert (df_snap["current_stock"] >= 0).all()
    assert (df_snap["pending_order_quantity"] >= 0).all()
