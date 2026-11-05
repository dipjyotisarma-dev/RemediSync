"""Pharmaceutical batch expiry and predictive waste intelligence engine.

Implements FEFO (First-Expired, First-Out) lot tracking, distributor return window audits
(<= 90 days), and predictive financial write-off risk quantification based on forward demand velocity.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd


class ExpiryIntelligenceEngine:
    """Predictive pharmaceutical batch lot expiry and financial waste intelligence service."""

    RETURN_WINDOW_DAYS: int = 90  # Statutory distributor return window for full credit
    WARNING_WINDOW_DAYS: int = 180  # Advance warning window for stock rotation

    def __init__(
        self,
        batches_path: Union[str, Path] = "data/raw/batches.csv",
    ) -> None:
        """Initialize the expiry intelligence engine.

        Args:
            batches_path: Path to raw batches CSV catalog.
        """
        self.batches_path = Path(batches_path)

    def load_batches(self) -> pd.DataFrame:
        """Load and structure batch inventory sorted by FEFO (First-Expired, First-Out).

        Returns:
            DataFrame sorted by branch_id, medicine_id, and expiry_date.

        Raises:
            FileNotFoundError: If batches.csv is missing.
        """
        if not self.batches_path.exists():
            raise FileNotFoundError(f"Batches file not found at {self.batches_path}")

        df = pd.read_csv(self.batches_path)
        df["mfg_date"] = pd.to_datetime(df["mfg_date"])
        df["expiry_date"] = pd.to_datetime(df["expiry_date"])
        df = df.sort_values(
            by=["branch_id", "medicine_id", "expiry_date", "batch_number"]
        ).reset_index(drop=True)
        return df

    def audit_batch_expiry_risk(
        self,
        daily_demand_lookup: Dict[Tuple[str, str], float],
        as_of_date: Optional[Union[str, pd.Timestamp]] = None,
    ) -> pd.DataFrame:
        """Evaluate all physical batch lots against forward sales velocity and expiration dates.

        Simulates FEFO dispensing queue: each batch begins depleting only after earlier-expiring
        lots for that same (branch_id, medicine_id) series are fully exhausted.

        Args:
            daily_demand_lookup: Dictionary mapping (branch_id, medicine_id) -> daily forecasted demand.
            as_of_date: Current operating date. Defaults to max expiry/sales date context.

        Returns:
            DataFrame enriched with days_to_expiry, depletion_days, units_at_risk,
            capital_at_risk, and risk_tier.
        """
        df = self.load_batches()
        ref_date = pd.Timestamp(as_of_date) if as_of_date else pd.Timestamp("2026-09-30")

        records: list[Dict[str, Any]] = []

        for (branch_id, medicine_id), group in df.groupby(
            ["branch_id", "medicine_id"], sort=False
        ):
            daily_demand = max(
                0.01,
                float(daily_demand_lookup.get((str(branch_id), str(medicine_id)), 1.0)),
            )

            # Track cumulative stock in FEFO order
            cumulative_sold_offset = 0.0

            for _, row in group.iterrows():
                batch_qty = float(row["current_quantity"])
                cost_price = float(row["unit_cost_price"])
                expiry_dt = pd.Timestamp(row["expiry_date"])
                days_to_expiry = int((expiry_dt - ref_date).days)

                if days_to_expiry <= 0:
                    # Already expired
                    units_at_risk = batch_qty
                    depletion_days = 0.0
                    risk_tier = "EXPIRED"
                else:
                    # Depletion time from when this batch starts dispensing
                    demand_during_shelf_life = max(0.0, days_to_expiry * daily_demand)
                    # Units consumed before this batch expires
                    available_demand_for_batch = max(
                        0.0, demand_during_shelf_life - cumulative_sold_offset
                    )
                    units_sold_before_expiry = min(batch_qty, available_demand_for_batch)
                    units_at_risk = max(0.0, batch_qty - units_sold_before_expiry)
                    depletion_days = (
                        (cumulative_sold_offset + batch_qty) / daily_demand
                    )

                    # Classify risk tier
                    if units_at_risk > 0 and days_to_expiry <= self.RETURN_WINDOW_DAYS:
                        risk_tier = "HIGH"
                    elif (
                        units_at_risk > 0
                        and days_to_expiry <= self.WARNING_WINDOW_DAYS
                    ) or (days_to_expiry <= self.RETURN_WINDOW_DAYS):
                        risk_tier = "MEDIUM"
                    else:
                        risk_tier = "LOW"

                cumulative_sold_offset += batch_qty
                capital_at_risk = units_at_risk * cost_price

                records.append(
                    {
                        "batch_id": row["batch_id"],
                        "medicine_id": medicine_id,
                        "branch_id": branch_id,
                        "batch_number": row["batch_number"],
                        "mfg_date": str(row["mfg_date"].date()),
                        "expiry_date": str(expiry_dt.date()),
                        "current_quantity": int(batch_qty),
                        "unit_cost_price": cost_price,
                        "daily_demand": round(daily_demand, 2),
                        "days_to_expiry": days_to_expiry,
                        "depletion_days": round(depletion_days, 1),
                        "units_at_risk": round(units_at_risk, 1),
                        "capital_at_risk": round(capital_at_risk, 2),
                        "is_near_expiry": days_to_expiry <= self.RETURN_WINDOW_DAYS,
                        "risk_tier": risk_tier,
                    }
                )

        return pd.DataFrame(records)

    def summarize_branch_expiry_exposure(
        self, batch_audit_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Aggregate batch audit metrics into branch-level risk exposure cards.

        Args:
            batch_audit_df: Output DataFrame from audit_batch_expiry_risk.

        Returns:
            DataFrame indexed by branch_id with totals and risk counts.
        """
        records: list[Dict[str, Any]] = []

        for branch_id, group in batch_audit_df.groupby("branch_id", observed=True):
            total_batches = len(group)
            near_expiry = int(group["is_near_expiry"].sum())
            high_risk = int((group["risk_tier"] == "HIGH").sum())
            expired = int((group["risk_tier"] == "EXPIRED").sum())
            units_at_risk = float(group["units_at_risk"].sum())
            capital_at_risk = float(group["capital_at_risk"].sum())

            records.append(
                {
                    "branch_id": str(branch_id),
                    "total_batches": int(total_batches),
                    "near_expiry_batches": int(near_expiry),
                    "high_risk_batches": int(high_risk),
                    "expired_batches": int(expired),
                    "total_units_at_risk": round(units_at_risk, 1),
                    "total_capital_at_risk": round(capital_at_risk, 2),
                }
            )

        summary_df = pd.DataFrame(records)
        if not summary_df.empty:
            summary_df = summary_df.set_index("branch_id")
        return summary_df
