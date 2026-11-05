"""Consolidated replenishment order generator and supplier purchase order dispatch engine.

Coordinates inventory snapshots, machine learning demand forecasts, therapeutic criticality,
packaging constraints, and distributor catalogs to generate auditable purchase orders
and plain-English pharmacist replenishment feeds.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.decision.expiry_intelligence import ExpiryIntelligenceEngine
from src.decision.inventory_policy import InventoryPolicy
from src.models.forecaster import DemandForecaster


class OrderGenerator:
    """Full-service replenishment generator consolidating store demand into supplier POs."""

    def __init__(
        self,
        inventory_path: Union[str, Path] = "data/raw/inventory_snapshot.csv",
        medicines_path: Union[str, Path] = "data/raw/medicines.csv",
        suppliers_path: Union[str, Path] = "data/raw/suppliers.csv",
        batches_path: Union[str, Path] = "data/raw/batches.csv",
        model_path: Union[str, Path] = "models/production_forecaster.joblib",
        feature_store_path: Union[str, Path] = "data/processed/feature_matrix.parquet",
    ) -> None:
        """Initialize the replenishment order generator.

        Args:
            inventory_path: Path to current store inventory snapshot.
            medicines_path: Path to master medicine catalog.
            suppliers_path: Path to master supplier catalog.
            batches_path: Path to raw batch lot records.
            model_path: Path to serialized production forecaster artifact.
            feature_store_path: Path to processed feature matrix parquet file.
        """
        self.inventory_path = Path(inventory_path)
        self.medicines_path = Path(medicines_path)
        self.suppliers_path = Path(suppliers_path)
        self.batches_path = Path(batches_path)
        self.model_path = Path(model_path)
        self.feature_store_path = Path(feature_store_path)

    def load_telemetry(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load and merge master catalogs with store inventory snapshot.

        Returns:
            Tuple of (merged_inventory_df, medicines_df, suppliers_df).

        Raises:
            FileNotFoundError: If any required CSV is missing.
        """
        for p in [self.inventory_path, self.medicines_path, self.suppliers_path]:
            if not p.exists():
                raise FileNotFoundError(f"Required telemetry file not found: {p}")

        inv_df = pd.read_csv(self.inventory_path)
        med_df = pd.read_csv(self.medicines_path)
        sup_df = pd.read_csv(self.suppliers_path)

        # Merge inventory with medicines and supplier attributes
        merged = inv_df.merge(med_df, on="medicine_id", how="left")
        merged = merged.merge(
            sup_df,
            left_on="primary_supplier_id",
            right_on="supplier_id",
            how="left",
            suffixes=("", "_supplier"),
        )

        return merged, med_df, sup_df

    def fetch_demand_forecasts(self) -> pd.DataFrame:
        """Generate 7-day demand forecasts for all active series using the production ML model.

        Returns:
            DataFrame containing branch_id, medicine_id, and predicted_7d_demand.
        """
        if not self.feature_store_path.exists():
            raise FileNotFoundError(
                f"Feature store not found at {self.feature_store_path}"
            )
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Production forecaster not found at {self.model_path}"
            )

        forecaster = DemandForecaster(data_path=self.feature_store_path)
        model, _ = forecaster.load_model(self.model_path)

        df = pd.read_parquet(self.feature_store_path)
        df["date"] = pd.to_datetime(df["date"])
        max_date = df["date"].max()

        # Extract latest snapshot slice across all 516 series
        latest_slice = df[df["date"] == max_date].copy().reset_index(drop=True)

        X_tree, _ = forecaster.prepare_features(latest_slice, for_tree=True)
        latest_slice["predicted_7d_demand"] = forecaster.predict(model, X_tree)

        return latest_slice[
            ["branch_id", "medicine_id", "predicted_7d_demand", "demand_pattern"]
        ]

    def generate_daily_recommendations(self) -> pd.DataFrame:
        """Calculate dynamic safety stocks, ROPs, and order quantities for all 516 series.

        Returns:
            DataFrame containing item-level replenishment intelligence and rationale.
        """
        merged_inv, _, _ = self.load_telemetry()
        forecasts = self.fetch_demand_forecasts()

        recs_df = merged_inv.merge(
            forecasts, on=["branch_id", "medicine_id"], how="left"
        )

        # Default fallback if forecast is unmapped
        recs_df["predicted_7d_demand"] = recs_df["predicted_7d_demand"].fillna(14.0)
        recs_df["daily_demand"] = recs_df["predicted_7d_demand"] / 7.0

        records: list[Dict[str, Any]] = []

        for _, row in recs_df.iterrows():
            branch_id = str(row["branch_id"])
            medicine_id = str(row["medicine_id"])
            brand_name = str(row["brand_name"])
            category = str(row["category"])
            current_stock = int(row["current_stock"])
            pending_order = int(row["pending_order_quantity"])
            lead_time = float(row.get("lead_time_days", 1.0))
            units_per_pack = int(row.get("units_per_pack", 10))
            cost_price = float(row.get("cost_price", 0.0))
            demand_pattern = str(row.get("demand_pattern", "Smooth"))

            # Calibrated residual standard deviation (sigma_e from diagnostics)
            sigma_e = 5.18 if demand_pattern == "Smooth" else 2.90

            daily_d = float(row["daily_demand"])
            pred_7d = float(row["predicted_7d_demand"])

            safety_stock = InventoryPolicy.calculate_safety_stock(
                daily_demand=daily_d,
                lead_time_days=lead_time,
                sigma_e=sigma_e,
                category=category,
            )
            rop = InventoryPolicy.calculate_reorder_point(
                daily_demand=daily_d,
                lead_time_days=lead_time,
                safety_stock=safety_stock,
            )
            days_of_cover = InventoryPolicy.calculate_days_of_cover(
                current_stock=current_stock,
                daily_demand=daily_d,
            )
            urgency = InventoryPolicy.classify_urgency(
                current_stock=current_stock,
                pending_order=pending_order,
                rop=rop,
                days_of_cover=days_of_cover,
                lead_time_days=lead_time,
            )
            order_units, order_packs = InventoryPolicy.calculate_reorder_quantity(
                daily_demand=daily_d,
                safety_stock=safety_stock,
                current_stock=current_stock,
                pending_order=pending_order,
                units_per_pack=units_per_pack,
                rop=rop,
            )

            order_cost = order_packs * cost_price

            rationale = InventoryPolicy.generate_rationale(
                brand_name=brand_name,
                current_stock=current_stock,
                days_of_cover=days_of_cover,
                lead_time_days=lead_time,
                predicted_7d_demand=pred_7d,
                safety_stock=int(round(safety_stock)),
                rop=int(round(rop)),
                order_units=order_units,
                order_packs=order_packs,
                urgency=urgency,
                pending_order=pending_order,
            )

            records.append(
                {
                    "branch_id": branch_id,
                    "medicine_id": medicine_id,
                    "brand_name": brand_name,
                    "generic_salt": row["generic_salt"],
                    "category": category,
                    "primary_supplier_id": row["primary_supplier_id"],
                    "supplier_name": row.get("supplier_name", "Unknown"),
                    "fulfillment_type": row.get("fulfillment_type", "EXPRESS_PICKUP"),
                    "lead_time_days": lead_time,
                    "units_per_pack": units_per_pack,
                    "pack_cost_price": cost_price,
                    "current_stock": current_stock,
                    "pending_order": pending_order,
                    "predicted_7d_demand": round(pred_7d, 1),
                    "daily_demand": round(daily_d, 2),
                    "safety_stock": int(round(safety_stock)),
                    "reorder_point": int(round(rop)),
                    "days_of_cover": round(days_of_cover, 1),
                    "urgency": urgency,
                    "recommended_order_packs": order_packs,
                    "recommended_order_units": order_units,
                    "recommended_order_cost": round(order_cost, 2),
                    "rationale": rationale,
                }
            )

        return pd.DataFrame(records)

    def build_supplier_purchase_orders(
        self, recommendations_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Consolidate item replenishment recommendations into distributor purchase orders.

        Args:
            recommendations_df: DataFrame from generate_daily_recommendations.

        Returns:
            List of structured Purchase Order dictionaries grouped by primary_supplier_id.
        """
        # Filter strictly to items that require commercial procurement
        reorder_items = recommendations_df[
            recommendations_df["recommended_order_packs"] > 0
        ].copy()

        purchase_orders: List[Dict[str, Any]] = []

        for supplier_id, group in reorder_items.groupby(
            "primary_supplier_id", observed=True
        ):
            sup_name = str(group["supplier_name"].iloc[0])
            fulfillment = str(group["fulfillment_type"].iloc[0])
            lead_time = float(group["lead_time_days"].iloc[0])

            line_items: List[Dict[str, Any]] = []
            for _, item in group.iterrows():
                line_items.append(
                    {
                        "branch_id": item["branch_id"],
                        "medicine_id": item["medicine_id"],
                        "brand_name": item["brand_name"],
                        "category": item["category"],
                        "urgency": item["urgency"],
                        "current_stock": item["current_stock"],
                        "days_of_cover": item["days_of_cover"],
                        "order_packs": int(item["recommended_order_packs"]),
                        "order_units": int(item["recommended_order_units"]),
                        "pack_cost": float(item["pack_cost_price"]),
                        "line_total_cost": float(item["recommended_order_cost"]),
                        "rationale": item["rationale"],
                    }
                )

            # Sort line items by urgency (CRITICAL first)
            urgency_rank = {"CRITICAL": 0, "REORDER": 1, "HEALTHY": 2, "OVERSTOCKED": 3}
            line_items.sort(key=lambda x: urgency_rank.get(x["urgency"], 99))

            total_packs = sum(i["order_packs"] for i in line_items)
            total_units = sum(i["order_units"] for i in line_items)
            total_cost = sum(i["line_total_cost"] for i in line_items)

            po_dict = {
                "po_id": f"PO-{supplier_id}-20260930",
                "supplier_id": str(supplier_id),
                "supplier_name": sup_name,
                "fulfillment_type": fulfillment,
                "lead_time_days": lead_time,
                "total_items": len(line_items),
                "total_packs": total_packs,
                "total_units": total_units,
                "total_cost": round(total_cost, 2),
                "line_items": line_items,
            }
            purchase_orders.append(po_dict)

        # Sort purchase orders by total capital descending
        purchase_orders.sort(key=lambda x: x["total_cost"], reverse=True)
        return purchase_orders

    def run_pipeline(self) -> Dict[str, Any]:
        """Execute end-to-end replenishment, expiry audit, and PO consolidation pipeline.

        Returns:
            Dictionary with recommendations DataFrame, PO list, expiry risk DataFrame,
            and aggregate network KPI cards.
        """
        recs_df = self.generate_daily_recommendations()
        purchase_orders = self.build_supplier_purchase_orders(recs_df)

        # Build demand lookup for Expiry Intelligence Engine
        demand_lookup = {
            (str(row["branch_id"]), str(row["medicine_id"])): float(
                row["daily_demand"]
            )
            for _, row in recs_df.iterrows()
        }

        expiry_engine = ExpiryIntelligenceEngine(batches_path=self.batches_path)
        batch_audit_df = expiry_engine.audit_batch_expiry_risk(
            daily_demand_lookup=demand_lookup, as_of_date="2026-09-30"
        )
        branch_expiry_summary = expiry_engine.summarize_branch_expiry_exposure(
            batch_audit_df
        )

        urgency_counts = recs_df["urgency"].value_counts().to_dict()
        total_procurement_cost = sum(po["total_cost"] for po in purchase_orders)

        return {
            "recommendations": recs_df,
            "purchase_orders": purchase_orders,
            "batch_expiry_audit": batch_audit_df,
            "branch_expiry_summary": branch_expiry_summary,
            "kpis": {
                "total_series": len(recs_df),
                "critical_count": urgency_counts.get("CRITICAL", 0),
                "reorder_count": urgency_counts.get("REORDER", 0),
                "healthy_count": urgency_counts.get("HEALTHY", 0),
                "overstocked_count": urgency_counts.get("OVERSTOCKED", 0),
                "total_suppliers_engaged": len(purchase_orders),
                "total_procurement_cost": round(total_procurement_cost, 2),
                "near_expiry_batches": int(batch_audit_df["is_near_expiry"].sum()),
                "total_capital_at_risk": round(
                    float(batch_audit_df["capital_at_risk"].sum()), 2
                ),
            },
        }


def main() -> None:
    """CLI runner executing replenishment engine and displaying production scorecard."""
    generator = OrderGenerator()
    results = generator.run_pipeline()

    kpis = results["kpis"]
    recs_df = results["recommendations"]
    purchase_orders = results["purchase_orders"]
    branch_expiry = results["branch_expiry_summary"]

    print("=" * 88)
    print("REMEDISYNC INVENTORY INTELLIGENCE: DAILY REPLENISHMENT & PURCHASE ORDERS")
    print("=" * 88)
    print("As-of Date           : 2026-09-30 | 516 Branch-Medicine Series Evaluated")
    print("Network Footprint    : 4 Assam Retail Branches (Kamakhya, Dharapur, Azara, Rani Gate)")
    print("Forecast Intelligence: HistGradientBoosting (models/production_forecaster.joblib)")
    print("-" * 88)

    print("\n[+] NETWORK-WIDE REPLENISHMENT URGENCY SUMMARY:")
    print(f"  * CRITICAL Stockout Risks (DoC <= Lead Time) : {kpis['critical_count']:>4} items (IMMEDIATE ACTION REQUIRED)")
    print(f"  * REORDER Threshold Triggered ((S+P) <= ROP) : {kpis['reorder_count']:>4} items (Add to Daily Purchase Order)")
    print(f"  * HEALTHY Stock Levels                       : {kpis['healthy_count']:>4} items (Optimal Buffer Cover)")
    print(f"  * OVERSTOCKED Positions (>21 Days Cover)     : {kpis['overstocked_count']:>4} items (Surplus Working Capital)")

    print("\n[+] TOP REORDER RECOMMENDATIONS (PROCUREMENT ACTION REQUIRED):")
    print("-" * 88)
    header = f"{'Branch':<6} | {'Medicine Name':<28} | {'Stock':<5} | {'Lead':<4} | {'7d Fcst':<7} | {'Order (Packs)':<13} | Rationale"
    print(header)
    print("-" * 88)

    reorder_action_items = recs_df[recs_df["recommended_order_packs"] > 0].sort_values(
        by=["urgency", "recommended_order_cost"], ascending=[True, False]
    ).head(6)

    for _, item in reorder_action_items.iterrows():
        packs_str = f"{item['recommended_order_units']}u ({item['recommended_order_packs']}p)"
        print(
            f"{item['branch_id']:<6} | "
            f"{item['brand_name'][:28]:<28} | "
            f"{item['current_stock']:<5} | "
            f"{item['lead_time_days']:<4.1f} | "
            f"{item['predicted_7d_demand']:<7.1f} | "
            f"{packs_str:<13} | "
            f"{item['rationale'][:60]}..."
        )
    print("-" * 88)

    print("\n[+] INCOMING EXPEDITE ALERTS (ORDERS IN TRANSIT, LOW SHELF COVER):")
    expedite_items = recs_df[(recs_df["urgency"] == "CRITICAL") & (recs_df["pending_order"] > 0)].head(3)
    for _, item in expedite_items.iterrows():
        print(
            f"  * [{item['branch_id']}] {item['brand_name']}: "
            f"Stock = {item['current_stock']}u ({item['days_of_cover']}d cover) | "
            f"In-Transit = {item['pending_order']}u | "
            f"Lead Time = {item['lead_time_days']:.0f}d | Action: Expedite delivery"
        )

    print("\n[+] SUPPLIER PURCHASE ORDER CONSOLIDATION:")
    print(f"  * Total Suppliers Engaged  : {kpis['total_suppliers_engaged']} Stockists")
    print(f"  * Total Purchase Orders    : {len(purchase_orders)} Dispatched POs")
    print(f"  * Total Procurement Capital: INR {kpis['total_procurement_cost']:,.2f}")
    print("\n  Top Supplier Dispatches:")
    for po in purchase_orders[:4]:
        print(
            f"    - {po['po_id']} | {po['supplier_name'][:30]:<30} | "
            f"{po['total_items']:>2} SKUs | "
            f"{po['total_packs']:>3} packs ({po['total_units']:>4} units) | "
            f"INR {po['total_cost']:>9,.2f} ({po['lead_time_days']:.0f}d lead, {po['fulfillment_type']})"
        )

    print("\n[+] BATCH EXPIRY & PREDICTIVE WRITE-OFF INTELLIGENCE:")
    print(f"  * Approaching Return Window (<= 90 Days) : {kpis['near_expiry_batches']} Batches")
    print(f"  * Total Predictive Capital at Risk       : INR {kpis['total_capital_at_risk']:,.2f}")
    print("\n  Branch Risk Exposure Breakdown:")
    for b_id, row in branch_expiry.iterrows():
        print(
            f"    * Branch {b_id}: {int(row['total_batches'])} batches | "
            f"{int(row['near_expiry_batches'])} near-expiry | "
            f"{int(row['high_risk_batches'])} high-risk | "
            f"Capital at Risk: INR {row['total_capital_at_risk']:>8,.2f}"
        )
    print("=" * 88)


if __name__ == "__main__":
    main()
