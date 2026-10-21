"""Baseline demand forecasting service and empirical benchmark runner.

Implements chronological walk-forward dataset partitioning and heuristic baseline models
(7-day rolling moving average and seasonal naive) to establish production deployment hurdles.
"""

from pathlib import Path
from typing import Any, Dict, Tuple, Union
import numpy as np
import pandas as pd

from src.models.evaluator import ForecastEvaluator


class BaselineForecaster:
    """Heuristic baseline demand forecaster and evaluation harness.

    Partitions transactional feature matrices chronologically to benchmark forward
    7-day customer demand without temporal data leakage.
    """

    def __init__(
        self,
        data_path: Union[str, Path] = "data/processed/feature_matrix.parquet",
        split_date: str = "2026-07-01",
    ) -> None:
        """Initialize the baseline forecasting engine.

        Args:
            data_path: Filepath to processed feature store parquet file.
            split_date: ISO date string (YYYY-MM-DD) defining the test horizon cutoff.
        """
        self.data_path = Path(data_path)
        self.split_date = pd.Timestamp(split_date)

    def load_data(self) -> pd.DataFrame:
        """Load and sort feature matrix from parquet store.

        Returns:
            Preprocessed DataFrame sorted chronologically by series.

        Raises:
            FileNotFoundError: If the parquet file is not found.
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"Feature matrix not found at {self.data_path}")

        df = pd.read_parquet(self.data_path)
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values(by=["date", "branch_id", "medicine_id"]).reset_index(drop=True)

    def split_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Perform strict chronological walk-forward train/test split.

        Args:
            df: Full feature matrix DataFrame.

        Returns:
            Tuple of (train_df, test_df) partitioned strictly on split_date.
        """
        train_mask = df["date"] < self.split_date
        test_mask = df["date"] >= self.split_date

        train_df = df.loc[train_mask].copy().reset_index(drop=True)
        test_df = df.loc[test_mask].copy().reset_index(drop=True)

        return train_df, test_df

    def predict_moving_average_7d(self, df: pd.DataFrame) -> np.ndarray:
        """Generate forward 7-day demand predictions using 7-day rolling average.

        Prediction formula: y_hat_t = 7 * rolling_mean_7
        Because rolling_mean_7 is computed with a 1-day temporal lag, this estimator
        is strictly free of forward lookahead leakage.

        Args:
            df: DataFrame containing the 'rolling_mean_7' feature column.

        Returns:
            1D numpy array of predicted 7-day cumulative unit demand.
        """
        if "rolling_mean_7" not in df.columns:
            raise KeyError("Required feature 'rolling_mean_7' missing from DataFrame.")

        predictions = 7.0 * df["rolling_mean_7"].to_numpy(dtype=np.float64)
        return np.maximum(0.0, predictions)

    def predict_seasonal_naive(self, df: pd.DataFrame) -> np.ndarray:
        """Generate forward 7-day demand predictions using weekly cycle sales lag.

        Prediction formula: y_hat_t = 7 * sales_lag_7

        Args:
            df: DataFrame containing the 'sales_lag_7' feature column.

        Returns:
            1D numpy array of predicted 7-day cumulative unit demand.
        """
        if "sales_lag_7" not in df.columns:
            raise KeyError("Required feature 'sales_lag_7' missing from DataFrame.")

        predictions = 7.0 * df["sales_lag_7"].to_numpy(dtype=np.float64)
        return np.maximum(0.0, predictions)

    def run_benchmark(self) -> Dict[str, Any]:
        """Execute end-to-end baseline evaluation on the out-of-time test horizon.

        Returns:
            Dictionary containing dataset summary, global metrics, stratified metrics,
            and machine learning candidate promotion gates.
        """
        df = self.load_data()
        train_df, test_df = self.split_data(df)

        if test_df.empty:
            raise ValueError(f"No test records found on or after {self.split_date}.")

        # Generate baseline predictions
        test_df["pred_baseline_7d_ma"] = self.predict_moving_average_7d(test_df)
        test_df["pred_seasonal_naive"] = self.predict_seasonal_naive(test_df)

        # Global evaluation
        global_ma_metrics = ForecastEvaluator.evaluate_all(
            test_df["target_7d"], test_df["pred_baseline_7d_ma"]
        )
        global_seasonal_metrics = ForecastEvaluator.evaluate_all(
            test_df["target_7d"], test_df["pred_seasonal_naive"]
        )

        # Stratified evaluations on primary baseline (7-day MA)
        pareto_stratified = ForecastEvaluator.evaluate_stratified(
            test_df, "target_7d", "pred_baseline_7d_ma", "abc_class"
        )
        demand_stratified = ForecastEvaluator.evaluate_stratified(
            test_df, "target_7d", "pred_baseline_7d_ma", "demand_pattern"
        )
        branch_stratified = ForecastEvaluator.evaluate_stratified(
            test_df, "target_7d", "pred_baseline_7d_ma", "branch_id"
        )

        # Candidate Model Deployment Gates (docs/ml/MODEL_GOVERNANCE_AND_METRICS.md)
        target_wape_hurdle = global_ma_metrics["wape"] * 0.80
        class_a_wape_hurdle = 0.180
        bias_tolerance = 0.030

        return {
            "metadata": {
                "split_date": str(self.split_date.date()),
                "train_start": str(train_df["date"].min().date()),
                "train_end": str(train_df["date"].max().date()),
                "train_rows": len(train_df),
                "test_start": str(test_df["date"].min().date()),
                "test_end": str(test_df["date"].max().date()),
                "test_rows": len(test_df),
                "unique_series": int(test_df.groupby(["branch_id", "medicine_id"]).ngroups),
            },
            "global_metrics": {
                "moving_average_7d": global_ma_metrics,
                "seasonal_naive": global_seasonal_metrics,
            },
            "stratified": {
                "pareto_abc": pareto_stratified,
                "demand_pattern": demand_stratified,
                "branch": branch_stratified,
            },
            "promotion_hurdles": {
                "target_wape_threshold": target_wape_hurdle,
                "class_a_wape_threshold": class_a_wape_hurdle,
                "bias_tolerance": bias_tolerance,
            },
        }


def main() -> None:
    """CLI entry point for running baseline evaluation and printing terminal scorecard."""
    forecaster = BaselineForecaster()
    results = forecaster.run_benchmark()

    meta = results["metadata"]
    ma_metrics = results["global_metrics"]["moving_average_7d"]
    seasonal_metrics = results["global_metrics"]["seasonal_naive"]
    pareto_df = results["stratified"]["pareto_abc"]
    demand_df = results["stratified"]["demand_pattern"]
    hurdles = results["promotion_hurdles"]

    print("=" * 76)
    print("REMEDISYNC DEMAND FORECASTING: PRODUCTION BASELINE SCORECARD")
    print("=" * 76)
    print(f"Timeline Cutoff Date : {meta['split_date']}")
    print(
        f"Training Horizon     : {meta['train_start']} to {meta['train_end']} "
        f"({meta['train_rows']:,} records)"
    )
    print(
        f"Test Horizon         : {meta['test_start']} to {meta['test_end']} "
        f"({meta['test_rows']:,} records)"
    )
    print(f"Active Series Tracked: {meta['unique_series']} time series")
    print("-" * 76)

    print("\n[+] GLOBAL BENCHMARK PERFORMANCE (TEST HORIZON):")
    print(f"  * 7-Day Moving Average Naive (Primary Benchmark):")
    print(f"      - WAPE (Volume Error) : {ma_metrics['wape'] * 100:>6.2f}%")
    print(f"      - MAE  (Mean Abs Error): {ma_metrics['mae']:>6.2f} units")
    print(f"      - RMSE (Extreme Error) : {ma_metrics['rmse']:>6.2f} units")
    bias_str = f"{ma_metrics['bias'] * 100:+.2f}%"
    bias_tag = "NEUTRAL / WELL-CALIBRATED" if abs(ma_metrics["bias"]) <= 0.03 else "BIASED"
    print(f"      - Aggregate Bias       : {bias_str:>6} ({bias_tag})")

    print(f"\n  * Seasonal Weekly Naive (Secondary Reference):")
    print(f"      - WAPE (Volume Error) : {seasonal_metrics['wape'] * 100:>6.2f}%")
    print(f"      - MAE  (Mean Abs Error): {seasonal_metrics['mae']:>6.2f} units")
    print(f"      - RMSE (Extreme Error) : {seasonal_metrics['rmse']:>6.2f} units")
    print(f"      - Aggregate Bias       : {seasonal_metrics['bias'] * 100:>+6.2f}%")

    print("\n[+] ERROR BREAKDOWN BY PARETO REVENUE TIER (7-Day Moving Average):")
    for tier in ["A", "B", "C"]:
        if tier in pareto_df.index:
            row = pareto_df.loc[tier]
            desc = "Top 80% Revenue" if tier == "A" else ("Next 15% Revenue" if tier == "B" else "Tail 5% Revenue")
            print(
                f"  * Class {tier} ({desc:<16}): "
                f"WAPE = {row['wape'] * 100:>5.2f}% | "
                f"MAE = {row['mae']:>5.2f} | "
                f"Bias = {row['bias'] * 100:>+5.2f}%"
            )

    print("\n[+] ERROR BREAKDOWN BY CROSTON DEMAND PATTERN (7-Day Moving Average):")
    for pattern in ["Smooth", "Intermittent"]:
        if pattern in demand_df.index:
            row = demand_df.loc[pattern]
            print(
                f"  * {pattern:<13} Demand: "
                f"WAPE = {row['wape'] * 100:>5.2f}% | "
                f"MAE = {row['mae']:>5.2f} | "
                f"Bias = {row['bias'] * 100:>+5.2f}%"
            )

    print("\n[+] MODEL PROMOTION & RELEASE HURDLES (MODEL_GOVERNANCE_AND_METRICS.md):")
    print("  To deploy a machine learning candidate model to production, it must achieve:")
    print(f"    [1] Global Test WAPE      <= {hurdles['target_wape_threshold'] * 100:.2f}% (>= 20% relative improvement)")
    print(f"    [2] Pareto Class A WAPE   <= {hurdles['class_a_wape_threshold'] * 100:.2f}% (High-value SKU error ceiling)")
    print(f"    [3] Aggregate Bias Bounds within [-3.00%, +3.00%]")
    print("=" * 76)


if __name__ == "__main__":
    main()
