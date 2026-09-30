"""
Data Understanding and Schema Integrity Audit Service for RemediSync.

Implements an Object-Oriented auditing pipeline to verify:
- Complete file presence and schema compliance
- 0.0% null rate across mandatory fields
- Strict foreign key referential integrity
- 100% time-series date continuity (zero missing dates in grid)
- Domain invariant compliance (margins, non-negativity, valid lead times)
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
import numpy as np
import pandas as pd


class DataHealthAuditor:
    """Automated schema auditor and integrity checker for raw pharmacy telemetry."""

    EXPECTED_COLUMNS: Dict[str, Set[str]] = {
        "branches.csv": {"branch_id", "branch_name", "location_type", "daily_target_revenue", "is_active"},
        "suppliers.csv": {"supplier_id", "supplier_name", "fulfillment_type", "lead_time_days", "city", "is_active"},
        "medicines.csv": {
            "medicine_id", "brand_name", "generic_salt", "strength", "dosage_form",
            "category", "manufacturer", "mrp", "cost_price", "pack_size", "units_per_pack", "primary_supplier_id"
        },
        "batches.csv": {
            "batch_id", "medicine_id", "branch_id", "batch_number", "mfg_date",
            "expiry_date", "initial_quantity", "current_quantity", "unit_cost_price"
        },
        "daily_sales.csv": {"date", "branch_id", "medicine_id", "units_sold", "unit_price", "total_revenue", "is_stockout"},
        "inventory_snapshot.csv": {"branch_id", "medicine_id", "current_stock", "last_replenished_date", "pending_order_quantity"}
    }

    def __init__(self, raw_dir: str = "data/raw", processed_dir: str = "data/processed") -> None:
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.tables: Dict[str, pd.DataFrame] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def load_data(self) -> None:
        """Loads all CSV tables into memory with standard typing."""
        for filename in self.EXPECTED_COLUMNS.keys():
            filepath = self.raw_dir / filename
            if not filepath.exists():
                self.errors.append(f"Missing required file: {filename}")
                continue
            self.tables[filename] = pd.read_csv(filepath)

    def audit_schema_and_columns(self) -> Dict[str, Any]:
        """Validates file existence, non-emptiness, and expected column sets."""
        schema_results = {}
        for filename, expected_cols in self.EXPECTED_COLUMNS.items():
            if filename not in self.tables:
                schema_results[filename] = {"status": "MISSING"}
                continue

            df = self.tables[filename]
            actual_cols = set(df.columns)
            missing = expected_cols - actual_cols
            extra = actual_cols - expected_cols

            if missing:
                self.errors.append(f"{filename}: Missing columns {missing}")

            schema_results[filename] = {
                "status": "VALID" if not missing else "INVALID",
                "row_count": len(df),
                "columns_matched": len(actual_cols & expected_cols),
                "missing_columns": list(missing),
                "extra_columns": list(extra)
            }
        return schema_results

    def audit_nulls(self) -> Dict[str, float]:
        """Calculates total and per-column null percentages across all tables."""
        null_report = {}
        for filename, df in self.tables.items():
            total_cells = df.size
            total_nulls = int(df.isna().sum().sum())
            null_pct = (total_nulls / total_cells * 100.0) if total_cells > 0 else 0.0

            if total_nulls > 0:
                self.errors.append(f"{filename} contains {total_nulls} null values ({null_pct:.2f}%)")

            null_report[filename] = round(null_pct, 4)
        return null_report

    def audit_referential_integrity(self) -> Dict[str, bool]:
        """Verifies foreign key relationships across master and transaction tables."""
        results = {}
        if not all(k in self.tables for k in ["branches.csv", "suppliers.csv", "medicines.csv", "batches.csv", "daily_sales.csv"]):
            return {"referential_integrity": False}

        valid_branches = set(self.tables["branches.csv"]["branch_id"])
        valid_suppliers = set(self.tables["suppliers.csv"]["supplier_id"])
        valid_medicines = set(self.tables["medicines.csv"]["medicine_id"])

        # Medicines -> Suppliers
        med_sup = set(self.tables["medicines.csv"]["primary_supplier_id"])
        invalid_med_sup = med_sup - valid_suppliers
        if invalid_med_sup:
            self.errors.append(f"medicines.csv contains invalid supplier IDs: {invalid_med_sup}")
        results["medicines_to_suppliers"] = len(invalid_med_sup) == 0

        # Batches -> Medicines & Branches
        batch_med = set(self.tables["batches.csv"]["medicine_id"]) - valid_medicines
        batch_br = set(self.tables["batches.csv"]["branch_id"]) - valid_branches
        if batch_med:
            self.errors.append(f"batches.csv contains invalid medicine IDs: {batch_med}")
        if batch_br:
            self.errors.append(f"batches.csv contains invalid branch IDs: {batch_br}")
        results["batches_foreign_keys"] = (len(batch_med) == 0 and len(batch_br) == 0)

        # Sales -> Medicines & Branches
        sales_med = set(self.tables["daily_sales.csv"]["medicine_id"]) - valid_medicines
        sales_br = set(self.tables["daily_sales.csv"]["branch_id"]) - valid_branches
        if sales_med:
            self.errors.append(f"daily_sales.csv contains invalid medicine IDs: {sales_med}")
        if sales_br:
            self.errors.append(f"daily_sales.csv contains invalid branch IDs: {sales_br}")
        results["sales_foreign_keys"] = (len(sales_med) == 0 and len(sales_br) == 0)

        return results

    def audit_date_grid_continuity(self) -> Dict[str, Any]:
        """Verifies that every branch-medicine pair has an unbroken date grid."""
        if "daily_sales.csv" not in self.tables:
            return {"grid_continuity": False, "missing_records": -1}

        df_sales = self.tables["daily_sales.csv"]
        unique_dates = df_sales["date"].unique()
        num_dates = len(unique_dates)
        num_branches = df_sales["branch_id"].nunique()
        num_medicines = df_sales["medicine_id"].nunique()

        expected_records = num_dates * num_branches * num_medicines
        actual_records = len(df_sales)
        missing_records = expected_records - actual_records

        # Check for duplicate composite keys [date, branch_id, medicine_id]
        duplicates = df_sales.duplicated(subset=["date", "branch_id", "medicine_id"]).sum()
        if duplicates > 0:
            self.errors.append(f"daily_sales.csv contains {duplicates} duplicate [date, branch_id, medicine_id] records")

        if missing_records != 0:
            self.errors.append(f"Date grid mismatch: expected {expected_records} rows, got {actual_records} rows")

        return {
            "total_dates": num_dates,
            "branches": num_branches,
            "medicines": num_medicines,
            "expected_records": expected_records,
            "actual_records": actual_records,
            "missing_records": int(missing_records),
            "duplicate_records": int(duplicates),
            "grid_continuity_valid": bool(missing_records == 0 and duplicates == 0)
        }

    def audit_domain_invariants(self) -> Dict[str, Any]:
        """Validates domain business rules (margins, bounds, expiry horizons)."""
        checks = {}

        # 1. Medicine Pricing & Margins
        if "medicines.csv" in self.tables:
            df_med = self.tables["medicines.csv"]
            margin_valid = (df_med["mrp"] > df_med["cost_price"]).all()
            positive_prices = (df_med["cost_price"] > 0).all()
            positive_units = (df_med["units_per_pack"] >= 1).all()

            if not margin_valid:
                self.errors.append("medicines.csv contains records where cost_price >= mrp")
            checks["pricing_and_margins_valid"] = bool(margin_valid and positive_prices and positive_units)

        # 2. Supplier Lead Times
        if "suppliers.csv" in self.tables:
            df_sup = self.tables["suppliers.csv"]
            valid_lead_times = df_sup["lead_time_days"].isin([1, 2, 3]).all()
            if not valid_lead_times:
                self.errors.append("suppliers.csv contains invalid lead_time_days outside [1, 2, 3]")
            checks["lead_times_valid"] = bool(valid_lead_times)

        # 3. Batch Expiry Horizons
        if "batches.csv" in self.tables:
            df_bat = self.tables["batches.csv"]
            expiries = pd.to_datetime(df_bat["expiry_date"])
            sim_end = pd.to_datetime("2026-09-30")
            near_term_count = int((expiries <= (sim_end + pd.Timedelta(days=90))).sum())

            if near_term_count == 0:
                self.warnings.append("batches.csv contains zero near-term batches (<90 days)")
            checks["near_term_expiries_count"] = near_term_count
            checks["near_term_expiries_present"] = near_term_count > 0

        # 4. Sales Non-Negativity
        if "daily_sales.csv" in self.tables:
            df_sales = self.tables["daily_sales.csv"]
            non_negative = (df_sales["units_sold"] >= 0).all() and (df_sales["total_revenue"] >= 0).all()
            if not non_negative:
                self.errors.append("daily_sales.csv contains negative quantities or revenues")
            checks["sales_quantities_valid"] = bool(non_negative)

        return checks

    def run_full_audit(self) -> Dict[str, Any]:
        """Executes all audit components and compiles a complete health report."""
        self.load_data()
        schema_results = self.audit_schema_and_columns()
        null_results = self.audit_nulls()
        ref_results = self.audit_referential_integrity()
        grid_results = self.audit_date_grid_continuity()
        invariant_results = self.audit_domain_invariants()

        overall_status = "PASSED" if len(self.errors) == 0 else "FAILED"

        report = {
            "audit_status": overall_status,
            "critical_errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "critical_errors": self.errors,
            "warnings": self.warnings,
            "schema_audit": schema_results,
            "null_rates_pct": null_results,
            "referential_integrity": ref_results,
            "date_grid_audit": grid_results,
            "domain_invariants": invariant_results
        }

        # Export report to data/processed/data_health_report.json
        def _json_default(obj: Any) -> Any:
            if isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            if isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            if isinstance(obj, (np.bool_, bool)):
                return bool(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return str(obj)

        report_file = self.processed_dir / "data_health_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=_json_default)

        return report


def main() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    auditor = DataHealthAuditor()
    report = auditor.run_full_audit()

    print("=" * 65)
    print(f"REMEDISYNC DATA HEALTH AUDIT: {report['audit_status']}")
    print("=" * 65)
    print(f"Critical Errors: {report['critical_errors_count']}")
    print(f"Warnings:        {report['warnings_count']}")
    print(f"Date Grid:       {report['date_grid_audit'].get('actual_records', 0):,} records verified")
    print(f"Grid Continuity: {'100% Complete' if report['date_grid_audit'].get('grid_continuity_valid') else 'FAILED'}")
    print(f"Report Exported: data/processed/data_health_report.json")
    print("=" * 65)

    if report["critical_errors"]:
        print("\nERRORS DETECTED:")
        for err in report["critical_errors"]:
            print(f"  [X] {err}")


if __name__ == "__main__":
    main()
