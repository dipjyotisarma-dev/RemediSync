"""
Inventory & Daily Sales Simulator Engine for RemediSync.

Executes the stateful discrete day-by-day market simulation:
- Tracks live on-hand physical stock across 4 branches and ~130 SKUs
- Depletes inventory based on stochastic customer demand
- Records loose tablet fraction sales and unit price revenues
- Enforces realistic stockout constraints (no sales when stock is zero)
- Automatically triggers replenishment orders respecting supplier lead times:
  * Express Evening Pickup (1-Day lead time)
  * Direct Distributor Delivery (2-3 Day lead time)
- Produces:
  * data/raw/daily_sales.csv (~330,000 rows)
  * data/raw/inventory_snapshot.csv
  * data/raw/batches.csv
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Tuple
from pathlib import Path
import numpy as np
import pandas as pd

from src.data_generator.demand_model import compute_expected_daily_demand, sample_realized_demand
from src.data_generator.batch_manager import create_initial_batches


def run_market_simulation(
    branches: List[Dict[str, Any]],
    suppliers: List[Dict[str, Any]],
    medicines: List[Dict[str, Any]],
    start_date: date,
    end_date: date,
    output_dir: str = "data/raw",
    seed: int = 42
) -> Dict[str, Any]:
    """Runs the 21-month discrete-event market simulation.

    Args:
        branches: Master branch list
        suppliers: Master supplier list
        medicines: Master medicine SKU catalog
        start_date: Starting date (2025-01-01)
        end_date: Final date (2026-09-30)
        output_dir: Output folder for CSV files
        seed: Random seed for reproducibility

    Returns:
        Summary metrics dictionary (total sales rows, total revenue, stockout count).
    """
    rng = np.random.default_rng(seed)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. Map lookups for fast retrieval
    supplier_lookup = {s["supplier_id"]: s for s in suppliers}
    num_branches = len(branches)
    num_meds = len(medicines)

    # 2. Initialize batches and initial stock state
    flat_batches, batch_lookup = create_initial_batches(branches, medicines, end_date, rng)

    # Matrix for on-hand stock: stock_matrix[branch_idx, med_idx]
    # Initialize with 15-30 days of safety stock
    stock_matrix = np.zeros((num_branches, num_meds), dtype=np.float32)
    for b_idx, branch in enumerate(branches):
        b_id = branch["branch_id"]
        for m_idx, med in enumerate(medicines):
            m_id = med["medicine_id"]
            # Sum current stock from active batches
            sku_batches = batch_lookup.get((b_id, m_id), [])
            total_batch_qty = sum(b["current_quantity"] for b in sku_batches)
            stock_matrix[b_idx, m_idx] = float(total_batch_qty)

    # Pending replenishment pipeline: list of tuples (delivery_date, branch_idx, med_idx, order_qty)
    pending_orders: List[Tuple[date, int, int, float]] = []

    # Prepare simulation date sequence
    total_days = (end_date - start_date).days + 1
    current_date = start_date

    sales_records: List[Dict[str, Any]] = []
    daily_sales_csv = out_path / "daily_sales.csv"

    # Write CSV header initially
    csv_header = "date,branch_id,medicine_id,units_sold,unit_price,total_revenue,is_stockout\n"
    with open(daily_sales_csv, "w", encoding="utf-8") as f:
        f.write(csv_header)

    total_revenue_acc = 0.0
    total_stockout_events = 0
    total_rows = 0

    print(f"Beginning market simulation from {start_date} to {end_date} ({total_days} days)...")

    # 3. Main Day-by-Day Loop
    for day_step in range(total_days):
        dt = current_date + timedelta(days=day_step)

        # A. Fulfill incoming supplier orders due today
        still_pending = []
        for arrival_dt, b_idx, m_idx, qty in pending_orders:
            if arrival_dt <= dt:
                stock_matrix[b_idx, m_idx] += qty
            else:
                still_pending.append((arrival_dt, b_idx, m_idx, qty))
        pending_orders = still_pending

        day_buffer: List[str] = []

        # B. Process dispensing across all branch-medicine pairs
        for b_idx, branch in enumerate(branches):
            b_id = branch["branch_id"]
            for m_idx, med in enumerate(medicines):
                m_id = med["medicine_id"]
                mrp = float(med["mrp"])
                units_per_pack = int(med["units_per_pack"])
                base_daily = float(med["base_daily_demand"])
                sup_id = med["primary_supplier_id"]
                supplier = supplier_lookup.get(sup_id, {"lead_time_days": 1})
                lead_time = int(supplier.get("lead_time_days", 1))

                # Expected demand and realized stochastic customer demand
                lambda_d = compute_expected_daily_demand(dt, branch, med)
                realized_demand = sample_realized_demand(lambda_d, units_per_pack, rng)

                curr_stock = stock_matrix[b_idx, m_idx]

                # Handle stock depletion and stockout logic
                if curr_stock <= 0.0:
                    units_sold = 0.0
                    is_stockout = True
                    total_stockout_events += 1
                elif curr_stock < realized_demand:
                    # Partial fulfillment
                    units_sold = round(curr_stock, 2)
                    stock_matrix[b_idx, m_idx] = 0.0
                    is_stockout = True
                    total_stockout_events += 1
                else:
                    units_sold = realized_demand
                    stock_matrix[b_idx, m_idx] = round(curr_stock - realized_demand, 2)
                    is_stockout = False

                total_rev = round(units_sold * mrp, 2)
                total_revenue_acc += total_rev
                total_rows += 1

                day_buffer.append(f"{dt},{b_id},{m_id},{units_sold:.2f},{mrp:.2f},{total_rev:.2f},{is_stockout}\n")

                # C. Replenishment Check: Reorder when stock drops below threshold
                calibrated_daily = base_daily * 0.23
                reorder_threshold = calibrated_daily * (lead_time + 2.0)
                if stock_matrix[b_idx, m_idx] <= reorder_threshold:
                    # Check if an order is already in flight for this SKU
                    already_ordered = any(
                        p[1] == b_idx and p[2] == m_idx for p in pending_orders
                    )
                    if not already_ordered:
                        # Order 14-day supply (rounded to whole packs)
                        order_qty = float(np.ceil(calibrated_daily * 14.0))
                        delivery_date = dt + timedelta(days=lead_time)
                        pending_orders.append((delivery_date, b_idx, m_idx, order_qty))

        # Stream day buffer to CSV (chunked file I/O)
        with open(daily_sales_csv, "a", encoding="utf-8") as f:
            f.writelines(day_buffer)

        # Monthly progress update in console
        if dt.day == 1 or day_step == total_days - 1:
            print(f" -> Completed: {dt} | Total Rows: {total_rows:,} | Cumulative Revenue: INR {total_revenue_acc:,.0f}")

    # 4. Export Inventory Snapshot on final simulation date (2026-09-30)
    print("Exporting inventory_snapshot.csv and batches.csv...")
    snapshot_records = []
    for b_idx, branch in enumerate(branches):
        b_id = branch["branch_id"]
        for m_idx, med in enumerate(medicines):
            m_id = med["medicine_id"]
            curr_stock = int(round(stock_matrix[b_idx, m_idx]))

            # Pending order check
            pending_qty = sum(
                p[3] for p in pending_orders if p[1] == b_idx and p[2] == m_idx
            )

            snapshot_records.append({
                "branch_id": b_id,
                "medicine_id": m_id,
                "current_stock": curr_stock,
                "last_replenished_date": str(end_date - timedelta(days=int(rng.integers(1, 4)))),
                "pending_order_quantity": int(pending_qty)
            })

    df_snapshot = pd.DataFrame(snapshot_records)
    snapshot_file = out_path / "inventory_snapshot.csv"
    df_snapshot.to_csv(snapshot_file, index=False)

    # 5. Export batches.csv reflecting final inventory
    df_batches = pd.DataFrame(flat_batches)
    batches_file = out_path / "batches.csv"
    df_batches.to_csv(batches_file, index=False)

    avg_daily_network_rev = total_revenue_acc / float(total_days)
    avg_branch_daily_rev = avg_daily_network_rev / float(num_branches)

    print("\nMarket Simulation Execution Complete:")
    print(f" - Daily Sales File: {daily_sales_csv} ({total_rows:,} records)")
    print(f" - Inventory Snapshot: {snapshot_file} ({len(df_snapshot):,} records)")
    print(f" - Batches File: {batches_file} ({len(df_batches):,} batches)")
    print(f" - Average Daily Network Revenue: INR {avg_daily_network_rev:,.2f}")
    print(f" - Average Daily Revenue Per Branch: INR {avg_branch_daily_rev:,.2f}")
    print(f" - Total Stockout Incidents: {total_stockout_events:,}")

    return {
        "daily_sales_file": str(daily_sales_csv),
        "inventory_snapshot_file": str(snapshot_file),
        "batches_file": str(batches_file),
        "total_rows": total_rows,
        "total_revenue": total_revenue_acc,
        "avg_branch_daily_revenue": avg_branch_daily_rev,
        "stockout_events": total_stockout_events
    }
