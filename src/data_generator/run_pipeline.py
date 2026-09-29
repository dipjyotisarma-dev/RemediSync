"""
End-to-End Orchestrator Pipeline for RemediSync Synthetic Market Generation.

Runs all decoupled components in sequence:
1. Static Dimension Tables (branches, suppliers, medicines)
2. Stochastic Market Simulation (daily sales, inventory ledger, batch expiries)
3. Integrity & Boundary Verification
"""

import sys
import time
from pathlib import Path

from src.data_generator.config import (
    BRANCHES,
    SUPPLIERS,
    MASTER_MEDICINE_CATALOG,
    SIMULATION_START_DATE,
    SIMULATION_END_DATE
)
from src.data_generator.master_data import generate_master_tables
from src.data_generator.inventory_simulator import run_market_simulation


def main() -> None:
    start_time = time.time()
    print("=" * 70)
    print("REMEDISYNC: ENTERPRISE PHARMACY DATA GENERATION PIPELINE")
    print("=" * 70)
    print(f"Network: 4 Assam Branches ({', '.join(b['branch_name'] for b in BRANCHES)})")
    print(f"Procurement: {len(SUPPLIERS)} Stockists (Express Pickup & Distributor Delivery)")
    print(f"Catalog: {len(MASTER_MEDICINE_CATALOG)} Core Indian Medicines")
    print(f"Time Horizon: {SIMULATION_START_DATE} to {SIMULATION_END_DATE}")
    print("=" * 70)

    # Ensure UTF-8 stdout on Windows console
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    # Step 1: Export Master Tables
    print("\n[Stage 1/2] Generating static dimension tables...")
    master_results = generate_master_tables(output_dir="data/raw")
    for name, path in master_results.items():
        print(f"  [+] Created: {path}")

    # Step 2: Run Stateful Market Simulation
    print("\n[Stage 2/2] Running discrete day-by-day market simulation...")
    sim_results = run_market_simulation(
        branches=BRANCHES,
        suppliers=SUPPLIERS,
        medicines=MASTER_MEDICINE_CATALOG,
        start_date=SIMULATION_START_DATE,
        end_date=SIMULATION_END_DATE,
        output_dir="data/raw",
        seed=42
    )

    elapsed = time.time() - start_time
    print("=" * 70)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS")
    print(f"Total Telemetry Rows Generated: {sim_results['total_rows']:,}")
    print(f"Average Daily Revenue Per Branch: ₹{sim_results['avg_branch_daily_revenue']:,.2f}")
    print(f"Total Cumulative Revenue: ₹{sim_results['total_revenue']:,.2f}")
    print(f"Total Stockout Days Encountered: {sim_results['stockout_events']:,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
