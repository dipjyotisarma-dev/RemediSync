"""
Master Data Generation Service for RemediSync.

Exports static dimension tables:
- data/raw/branches.csv
- data/raw/suppliers.csv
- data/raw/medicines.csv
"""

import os
from pathlib import Path
from typing import Dict, Any
import pandas as pd

from src.data_generator.config import BRANCHES, SUPPLIERS, MASTER_MEDICINE_CATALOG


def generate_master_tables(output_dir: str = "data/raw") -> Dict[str, str]:
    """Generates and writes static master CSV tables to the specified directory.

    Args:
        output_dir: Target directory path for raw data exports.

    Returns:
        Dict mapping table names to their exported file paths.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # 1. branches.csv
    df_branches = pd.DataFrame(BRANCHES)
    branches_file = out_path / "branches.csv"
    # Select columns matching official schema
    branch_cols = ["branch_id", "branch_name", "location_type", "daily_target_revenue", "is_active"]
    df_branches[branch_cols].to_csv(branches_file, index=False)

    # 2. suppliers.csv
    df_suppliers = pd.DataFrame(SUPPLIERS)
    suppliers_file = out_path / "suppliers.csv"
    supplier_cols = ["supplier_id", "supplier_name", "fulfillment_type", "lead_time_days", "city", "is_active"]
    df_suppliers[supplier_cols].to_csv(suppliers_file, index=False)

    # 3. medicines.csv
    df_medicines = pd.DataFrame(MASTER_MEDICINE_CATALOG)
    medicines_file = out_path / "medicines.csv"
    medicine_cols = [
        "medicine_id", "brand_name", "generic_salt", "strength", "dosage_form",
        "category", "manufacturer", "mrp", "cost_price", "pack_size",
        "units_per_pack", "primary_supplier_id"
    ]
    df_medicines[medicine_cols].to_csv(medicines_file, index=False)

    return {
        "branches": str(branches_file),
        "suppliers": str(suppliers_file),
        "medicines": str(medicines_file)
    }


if __name__ == "__main__":
    results = generate_master_tables()
    print("Master tables generated successfully:")
    for k, v in results.items():
        print(f" - {k}: {v}")
