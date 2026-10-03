"""
RemediSync Feature Engineering Pipeline.

Constructs leakage-free tabular training matrices from daily transaction
telemetry, integrating multi-horizon demand lags, rolling volatility statistics,
cyclical calendar encodings, and SKU profile metadata.
"""

from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import pandas as pd


class FeaturePipeline:
    """
    Feature engineering pipeline for multi-branch retail pharmacy forecasting.
    """

    def __init__(
        self,
        raw_dir: str | Path = "data/raw",
        processed_dir: str | Path = "data/processed"
    ) -> None:
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.sales_df: Optional[pd.DataFrame] = None
        self.medicines_df: Optional[pd.DataFrame] = None
        self.branches_df: Optional[pd.DataFrame] = None
        self.profiles_df: Optional[pd.DataFrame] = None
        self.feature_matrix: Optional[pd.DataFrame] = None

    def load_data(self) -> None:
        """Loads transaction data, master dimensions, and demand profile metadata."""
        sales_path = self.raw_dir / "daily_sales.csv"
        meds_path = self.raw_dir / "medicines.csv"
        branches_path = self.raw_dir / "branches.csv"
        profiles_path = self.processed_dir / "sku_demand_profiles.csv"

        if not sales_path.exists():
            raise FileNotFoundError(f"Missing sales data at {sales_path}")
        if not profiles_path.exists():
            raise FileNotFoundError(f"Missing demand profiles at {profiles_path}")

        self.sales_df = pd.read_csv(sales_path, parse_dates=["date"])
        self.medicines_df = pd.read_csv(meds_path)
        self.branches_df = pd.read_csv(branches_path)
        self.profiles_df = pd.read_csv(profiles_path)

    def compute_series_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes forward target and backward lag/rolling statistics with strict shift(1) isolation.
        """
        df = df.sort_values(by=["branch_id", "medicine_id", "date"]).reset_index(drop=True)
        grouped = df.groupby(["branch_id", "medicine_id"], sort=False)["units_sold"]

        # Forward 7-day cumulative customer demand target
        df["target_7d"] = grouped.transform(lambda s: s.rolling(7).sum().shift(-7))

        # Strict t-1 observation boundary to prevent temporal lookahead leakage
        hist_demand = grouped.shift(1)

        # Weekly cyclic lags
        df["sales_lag_7"] = hist_demand.groupby([df["branch_id"], df["medicine_id"]], sort=False).shift(6)
        df["sales_lag_14"] = hist_demand.groupby([df["branch_id"], df["medicine_id"]], sort=False).shift(13)
        df["sales_lag_21"] = hist_demand.groupby([df["branch_id"], df["medicine_id"]], sort=False).shift(20)
        df["sales_lag_28"] = hist_demand.groupby([df["branch_id"], df["medicine_id"]], sort=False).shift(27)

        # Multi-horizon rolling statistics
        hist_grouped = hist_demand.groupby([df["branch_id"], df["medicine_id"]], sort=False)
        df["rolling_mean_7"] = hist_grouped.transform(lambda s: s.rolling(7).mean())
        df["rolling_mean_14"] = hist_grouped.transform(lambda s: s.rolling(14).mean())
        df["rolling_mean_28"] = hist_grouped.transform(lambda s: s.rolling(28).mean())
        df["rolling_std_7"] = hist_grouped.transform(lambda s: s.rolling(7).std())
        df["rolling_std_28"] = hist_grouped.transform(lambda s: s.rolling(28).std())

        return df

    def compute_calendar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts temporal rhythms, payday refill waves, and cyclical trigonometric encodings.
        """
        dow = df["date"].dt.dayofweek
        dom = df["date"].dt.day
        month = df["date"].dt.month

        df["day_of_week"] = dow
        df["day_of_month"] = dom
        df["month"] = month
        df["quarter"] = df["date"].dt.quarter
        df["is_payday_week"] = (dom <= 7).astype(np.int8)

        df["sin_dow"] = np.sin(2 * np.pi * dow / 7.0).round(4)
        df["cos_dow"] = np.cos(2 * np.pi * dow / 7.0).round(4)
        df["sin_month"] = np.sin(2 * np.pi * (month - 1) / 12.0).round(4)
        df["cos_month"] = np.cos(2 * np.pi * (month - 1) / 12.0).round(4)

        return df

    def merge_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enriches transactions with clinical dimensions, branch context, and demand profiles.
        """
        med_cols = ["medicine_id", "category", "dosage_form", "mrp", "cost_price"]
        df = df.merge(self.medicines_df[med_cols], on="medicine_id", how="left")

        branch_cols = ["branch_id", "location_type"]
        df = df.merge(self.branches_df[branch_cols], on="branch_id", how="left")

        profile_cols = ["branch_id", "medicine_id", "demand_pattern", "abc_class", "adi", "cv2"]
        df = df.merge(self.profiles_df[profile_cols], on=["branch_id", "medicine_id"], how="left")

        return df

    def generate_feature_matrix(self) -> pd.DataFrame:
        """
        Executes end-to-end transformation, boundary trimming, and schema validation.
        """
        if self.sales_df is None:
            self.load_data()

        df = self.compute_series_features(self.sales_df.copy())
        df = self.compute_calendar_features(df)
        df = self.merge_metadata(df)

        # Trim initial 28-day warm-up and terminal 7-day target horizon
        df = df.dropna().reset_index(drop=True)

        ordered_cols = [
            "date", "branch_id", "medicine_id",
            "category", "dosage_form", "location_type",
            "demand_pattern", "abc_class", "adi", "cv2",
            "mrp", "cost_price",
            "day_of_week", "day_of_month", "month", "quarter", "is_payday_week",
            "sin_dow", "cos_dow", "sin_month", "cos_month",
            "sales_lag_7", "sales_lag_14", "sales_lag_21", "sales_lag_28",
            "rolling_mean_7", "rolling_mean_14", "rolling_mean_28",
            "rolling_std_7", "rolling_std_28",
            "target_7d"
        ]

        self.feature_matrix = df[ordered_cols]
        return self.feature_matrix

    def export(self, output_path: str | Path | None = None) -> Path:
        """Persists the transformed matrix to Parquet format."""
        if self.feature_matrix is None:
            self.generate_feature_matrix()

        target = Path(output_path) if output_path else self.processed_dir / "feature_matrix.parquet"
        target.parent.mkdir(parents=True, exist_ok=True)
        self.feature_matrix.to_parquet(target, index=False, engine="pyarrow")
        return target
