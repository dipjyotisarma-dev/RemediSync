"""
Batch & Expiry Management Module for RemediSync.

Generates physical pharmaceutical lots with:
- Authentic lot codes (e.g., DL-25B04, AG-24K12)
- Manufacturing and expiration dates
- Strategic expiry stratification to benchmark the Version 1 Predictive Expiry Risk engine:
  * ~6% Near-Term Expiry (< 90 days from end date: Oct, Nov, Dec 2026)
  * ~20% Medium-Term Expiry (6-12 months: 2027)
  * ~74% Long-Term Expiry (12-24 months: late 2027 / 2028)
- FEFO (First Expired, First Out) inventory depletion tracking.
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd


def generate_batch_number(medicine_code: str, mfg_date: date, batch_idx: int) -> str:
    """Generates an authentic pharmaceutical lot code.

    Format: [BrandPrefix]-[YY][MonthLetter][Sequence]
    Example: DL-25A01 (Dolo 650, manufactured Jan 2025, lot 1)
    """
    prefix = medicine_code[:2]
    month_letters = "ABCDEFGHIJKL"
    month_letter = month_letters[mfg_date.month - 1]
    year_str = str(mfg_date.year)[-2:]
    return f"{prefix}-{year_str}{month_letter}{batch_idx:02d}"


def create_initial_batches(
    branches: List[Dict[str, Any]],
    medicines: List[Dict[str, Any]],
    simulation_end_date: date,
    rng: np.random.Generator
) -> Tuple[List[Dict[str, Any]], Dict[Tuple[str, str], List[Dict[str, Any]]]]:
    """Initializes multi-batch inventory across all branch-medicine pairs.

    Returns:
        Tuple containing:
        - Flat list of batch records for CSV export
        - In-memory nested lookup: (branch_id, medicine_id) -> list of batch objects sorted by FEFO
    """
    flat_batches: List[Dict[str, Any]] = []
    batch_lookup: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

    batch_counter = 1

    for branch in branches:
        b_id = branch["branch_id"]
        for med in medicines:
            m_id = med["medicine_id"]
            cost_price = float(med["cost_price"])
            base_demand = float(med["base_daily_demand"])

            # Each SKU typically has 1 to 3 active batches in stock
            num_batches = int(rng.choice([1, 2, 3], p=[0.50, 0.40, 0.10]))
            sku_batches: List[Dict[str, Any]] = []

            for i in range(1, num_batches + 1):
                batch_id = f"BAT{batch_counter:05d}"
                batch_counter += 1

                # Sample expiry horizon:
                # 6% Near-term (< 90 days: Oct-Dec 2026) -> triggers expiry risk alerts
                # 20% Medium-term (6-12 months: mid 2027)
                # 74% Long-term (12-24 months: late 2027 to 2028)
                rand_val = rng.random()
                if rand_val < 0.06:
                    days_until_expiry = rng.integers(15, 85)
                elif rand_val < 0.26:
                    days_until_expiry = rng.integers(120, 365)
                else:
                    days_until_expiry = rng.integers(366, 730)

                expiry_dt = simulation_end_date + timedelta(days=int(days_until_expiry))
                # Shelf life is typically 24 months, so mfg_date is ~730 days prior to expiry
                mfg_dt = expiry_dt - timedelta(days=730)

                batch_num = generate_batch_number(med["brand_name"], mfg_dt, i)

                # Batch quantity proportional to daily demand (covers 7 to 30 days of sales)
                calibrated_daily = base_demand * 0.23
                initial_qty = int(max(5, round(calibrated_daily * rng.uniform(10, 25))))
                # Current stock on hand is a fraction of initial
                current_qty = int(max(0, round(initial_qty * rng.uniform(0.3, 0.8))))

                batch_record = {
                    "batch_id": batch_id,
                    "medicine_id": m_id,
                    "branch_id": b_id,
                    "batch_number": batch_num,
                    "mfg_date": str(mfg_dt),
                    "expiry_date": str(expiry_dt),
                    "initial_quantity": initial_qty,
                    "current_quantity": current_qty,
                    "unit_cost_price": cost_price
                }

                flat_batches.append(batch_record)
                sku_batches.append(batch_record)

            # Sort batches for this SKU using FEFO (First Expired, First Out)
            sku_batches.sort(key=lambda b: b["expiry_date"])
            batch_lookup[(b_id, m_id)] = sku_batches

    return flat_batches, batch_lookup


def deplete_batch_stock(
    batches: List[Dict[str, Any]],
    units_to_deplete: float
) -> float:
    """Depletes stock from the earliest expiring active batches (FEFO).

    Args:
        batches: List of active batch dicts for a single SKU/branch sorted by expiry date.
        units_to_deplete: Customer sales demand in packs to deduct.

    Returns:
        Actual units fulfilled from stock.
    """
    remaining_demand = units_to_deplete
    fulfilled = 0.0

    for batch in batches:
        avail = float(batch["current_quantity"])
        if avail <= 0:
            continue

        if avail >= remaining_demand:
            batch["current_quantity"] = round(avail - remaining_demand, 2)
            fulfilled += remaining_demand
            remaining_demand = 0.0
            break
        else:
            fulfilled += avail
            remaining_demand -= avail
            batch["current_quantity"] = 0.0

    return round(fulfilled, 2)
