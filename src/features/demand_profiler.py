"""
RemediSync Demand Profiling & Time-Series Characterization Service.

Computes Syntetos-Boylan demand categorization (Croston matrix: ADI vs CV^2),
ABC Pareto revenue segmentation, temporal seasonality indices, and series-level
velocity metrics for retail pharmacy inventory optimization.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CrostonThresholds:
    """Threshold constants for Syntetos-Boylan classification."""
    ADI_CUTOFF: float = 1.32
    CV2_CUTOFF: float = 0.49


class DemandProfiler:
    """
    Object-oriented demand profiling engine for multi-branch retail pharmacy inventory.
    """

    def __init__(self, data_dir: str | Path = "data/raw") -> None:
        self.data_dir = Path(data_dir)
        self.sales_df: Optional[pd.DataFrame] = None
        self.medicines_df: Optional[pd.DataFrame] = None
        self.branches_df: Optional[pd.DataFrame] = None
        self.profiles_df: Optional[pd.DataFrame] = None

    def load_data(self) -> None:
        """Loads and formats dimension and transaction tables."""
        sales_path = self.data_dir / "daily_sales.csv"
        meds_path = self.data_dir / "medicines.csv"
        branches_path = self.data_dir / "branches.csv"

        if not sales_path.exists():
            raise FileNotFoundError(f"Sales dataset not found at {sales_path}")

        self.sales_df = pd.read_csv(sales_path, parse_dates=["date"])
        self.medicines_df = pd.read_csv(meds_path)
        self.branches_df = pd.read_csv(branches_path)

    @staticmethod
    def classify_demand_pattern(adi: float, cv2: float) -> str:
        """
        Classifies time-series into Syntetos-Boylan demand quadrants.

        Args:
            adi: Average Demand Interval (intermittency).
            cv2: Squared Coefficient of Variation (size volatility).

        Returns:
            Quadrant label: 'Smooth', 'Intermittent', 'Erratic', or 'Lumpy'.
        """
        if adi < CrostonThresholds.ADI_CUTOFF and cv2 < CrostonThresholds.CV2_CUTOFF:
            return "Smooth"
        elif adi >= CrostonThresholds.ADI_CUTOFF and cv2 < CrostonThresholds.CV2_CUTOFF:
            return "Intermittent"
        elif adi < CrostonThresholds.ADI_CUTOFF and cv2 >= CrostonThresholds.CV2_CUTOFF:
            return "Erratic"
        else:
            return "Lumpy"

    def compute_croston_metrics(self) -> pd.DataFrame:
        """
        Computes ADI, CV^2, and demand quadrant for each (medicine_id, branch_id) series.
        """
        if self.sales_df is None:
            self.load_data()

        records = []
        grouped = self.sales_df.groupby(["medicine_id", "branch_id"])

        for (med_id, branch_id), group in grouped:
            total_periods = len(group)
            units = group["units_sold"].values
            positive_units = units[units > 0]
            non_zero_periods = len(positive_units)

            if non_zero_periods == 0:
                adi = float(total_periods)
                cv2 = 0.0
                mean_pos_demand = 0.0
                std_pos_demand = 0.0
            else:
                adi = total_periods / non_zero_periods
                mean_pos_demand = float(np.mean(positive_units))
                std_pos_demand = float(np.std(positive_units, ddof=1)) if non_zero_periods > 1 else 0.0
                cv2 = (std_pos_demand / mean_pos_demand) ** 2 if mean_pos_demand > 0 else 0.0

            zero_rate = (total_periods - non_zero_periods) / total_periods
            pattern = self.classify_demand_pattern(adi, cv2)

            records.append({
                "medicine_id": med_id,
                "branch_id": branch_id,
                "total_periods": total_periods,
                "non_zero_periods": non_zero_periods,
                "adi": round(adi, 4),
                "cv2": round(cv2, 4),
                "mean_daily_demand": round(float(np.mean(units)), 4),
                "mean_pos_demand": round(mean_pos_demand, 4),
                "std_pos_demand": round(std_pos_demand, 4),
                "zero_demand_rate": round(zero_rate, 4),
                "demand_pattern": pattern,
                "total_revenue": round(float(group["total_revenue"].sum()), 2),
                "stockout_days": int(group["is_stockout"].sum()),
            })

        return pd.DataFrame(records)

    def compute_abc_classification(self, series_metrics: pd.DataFrame) -> pd.DataFrame:
        """
        Computes Pareto ABC revenue tiers across the catalog.

        Class A: Top 80% revenue.
        Class B: Next 15% revenue (80% - 95%).
        Class C: Tail 5% revenue (> 95%).
        """
        sku_rev = (
            series_metrics.groupby("medicine_id")["total_revenue"]
            .sum()
            .reset_index()
            .sort_values(by="total_revenue", ascending=False)
        )
        total_network_rev = sku_rev["total_revenue"].sum()
        sku_rev["rev_share"] = sku_rev["total_revenue"] / total_network_rev
        sku_rev["cumulative_share"] = sku_rev["rev_share"].cumsum()

        def assign_abc(cum_share: float) -> str:
            if cum_share <= 0.80:
                return "A"
            elif cum_share <= 0.95:
                return "B"
            else:
                return "C"

        sku_rev["abc_class"] = sku_rev["cumulative_share"].apply(assign_abc)
        return sku_rev[["medicine_id", "abc_class", "rev_share", "cumulative_share"]]

    def compute_temporal_seasonality(self) -> Dict[str, pd.DataFrame]:
        """
        Computes Day-of-Week index and Payday refill index across categories.
        """
        if self.sales_df is None:
            self.load_data()

        merged = self.sales_df.merge(
            self.medicines_df[["medicine_id", "category"]],
            on="medicine_id",
            how="left"
        )
        merged["day_of_week"] = merged["date"].dt.day_name()
        merged["day_of_week_num"] = merged["date"].dt.dayofweek
        merged["is_payday_week"] = merged["date"].dt.day <= 7

        # Day of week profile
        dow_agg = (
            merged.groupby(["category", "day_of_week_num", "day_of_week"])["units_sold"]
            .mean()
            .reset_index()
        )
        cat_mean = merged.groupby("category")["units_sold"].mean().reset_index()
        cat_mean.rename(columns={"units_sold": "category_avg_units"}, inplace=True)
        dow_agg = dow_agg.merge(cat_mean, on="category", how="left")
        dow_agg["dow_index"] = round(dow_agg["units_sold"] / dow_agg["category_avg_units"], 4)
        dow_agg.sort_values(by=["category", "day_of_week_num"], inplace=True)

        # Payday wave profile
        payday_agg = (
            merged.groupby(["category", "is_payday_week"])["units_sold"]
            .mean()
            .unstack()
            .reset_index()
        )
        payday_agg.rename(columns={True: "payday_avg_units", False: "regular_avg_units"}, inplace=True)
        payday_agg["payday_surge_ratio"] = round(payday_agg["payday_avg_units"] / payday_agg["regular_avg_units"], 4)

        return {
            "day_of_week_index": dow_agg,
            "payday_surge": payday_agg,
        }

    def generate_full_profiles(self) -> pd.DataFrame:
        """
        Generates enriched demand profile table for all (medicine_id, branch_id) series.
        """
        croston_df = self.compute_croston_metrics()
        abc_df = self.compute_abc_classification(croston_df)

        profiles = croston_df.merge(abc_df, on="medicine_id", how="left")
        profiles = profiles.merge(
            self.medicines_df[[
                "medicine_id", "brand_name", "generic_salt", "category",
                "dosage_form", "mrp", "cost_price"
            ]],
            on="medicine_id",
            how="left"
        )
        profiles = profiles.merge(
            self.branches_df[["branch_id", "branch_name", "location_type"]],
            on="branch_id",
            how="left"
        )

        ordered_cols = [
            "medicine_id", "brand_name", "generic_salt", "category",
            "branch_id", "branch_name", "location_type",
            "demand_pattern", "abc_class", "adi", "cv2",
            "mean_daily_demand", "mean_pos_demand", "std_pos_demand",
            "zero_demand_rate", "total_revenue", "rev_share", "cumulative_share",
            "stockout_days"
        ]
        self.profiles_df = profiles[ordered_cols].sort_values(
            by=["branch_id", "total_revenue"], ascending=[True, False]
        ).reset_index(drop=True)

        return self.profiles_df

    def export_profiles(self, output_path: str | Path = "data/processed/sku_demand_profiles.csv") -> Path:
        """
        Persists demand profiles to CSV.
        """
        if self.profiles_df is None:
            self.generate_full_profiles()

        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.profiles_df.to_csv(target, index=False)
        return target
