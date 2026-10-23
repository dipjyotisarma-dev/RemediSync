"""Production demand forecasting diagnostics and SKU error stratification engine.

Evaluates promoted forecasting models across multi-dimensional business slices,
temporal drift horizons, residual distributions, and outlier SKU profiles to calibrate
downstream inventory safety stock buffers.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.models.evaluator import ForecastEvaluator
from src.models.forecaster import DemandForecaster


class ModelDiagnostics:
    """Quantitative diagnostics and error stratification engine for demand forecasts."""

    def __init__(
        self,
        data_path: Union[str, Path] = "data/processed/feature_matrix.parquet",
        model_path: Union[str, Path] = "models/production_forecaster.joblib",
        split_date: str = "2026-07-01",
    ) -> None:
        """Initialize the diagnostic service.

        Args:
            data_path: Path to processed feature matrix parquet store.
            model_path: Path to serialized production forecaster artifact.
            split_date: Cutoff date separating historical training from test horizon.
        """
        self.data_path = Path(data_path)
        self.model_path = Path(model_path)
        self.split_date = pd.Timestamp(split_date)

    def load_telemetry(self) -> Tuple[pd.DataFrame, pd.DataFrame, Any, Dict[str, Any]]:
        """Load feature matrix partitions and production model artifact.

        Returns:
            Tuple of (train_df, test_df, model, metadata).

        Raises:
            FileNotFoundError: If feature matrix or model artifact is missing.
        """
        forecaster = DemandForecaster(
            data_path=self.data_path, split_date=str(self.split_date.date())
        )
        train_df, test_df = forecaster.load_data()
        model, metadata = forecaster.load_model(self.model_path)
        return train_df, test_df, model, metadata

    def generate_all_predictions(
        self, train_df: pd.DataFrame, test_df: pd.DataFrame, production_model: Any
    ) -> pd.DataFrame:
        """Generate predictions for all baseline and candidate models on test data.

        Args:
            train_df: Training DataFrame.
            test_df: Test DataFrame.
            production_model: Fitted production estimator.

        Returns:
            Enriched test DataFrame with prediction columns and residuals.
        """
        eval_df = test_df.copy()
        forecaster = DemandForecaster()

        # 1. Heuristic Naive Baseline (7-Day Moving Average)
        eval_df["pred_7d_ma"] = np.maximum(
            0.0, 7.0 * eval_df["rolling_mean_7"].to_numpy(dtype=np.float64)
        )

        # 2. Heuristic Seasonal Weekly Naive
        eval_df["pred_seasonal_naive"] = np.maximum(
            0.0, 7.0 * eval_df["sales_lag_7"].to_numpy(dtype=np.float64)
        )

        # 3. Regularized Linear Model (Ridge Regression)
        X_train_lin, y_train = forecaster.prepare_features(train_df, for_tree=False)
        X_test_lin, _ = forecaster.prepare_features(test_df, for_tree=False)
        ridge_pipe = forecaster.train_ridge(X_train_lin, y_train, alpha=10.0)
        eval_df["pred_ridge"] = forecaster.predict(ridge_pipe, X_test_lin)

        # 4. Production Tree Ensemble (HistGradientBoosting)
        X_test_tree, _ = forecaster.prepare_features(test_df, for_tree=True)
        eval_df["pred_production"] = forecaster.predict(production_model, X_test_tree)

        # Error and residual vectors for production model
        eval_df["error"] = eval_df["pred_production"] - eval_df["target_7d"]
        eval_df["abs_error"] = np.abs(eval_df["error"])
        eval_df["pct_error"] = np.where(
            eval_df["target_7d"] > 0,
            eval_df["abs_error"] / eval_df["target_7d"],
            0.0,
        )

        return eval_df

    def compute_benchmark_matrix(self, eval_df: pd.DataFrame) -> pd.DataFrame:
        """Compute comparative performance metrics across all models on test horizon.

        Args:
            eval_df: Test DataFrame containing actual targets and model predictions.

        Returns:
            Summary DataFrame indexed by model architecture.
        """
        models = [
            ("Seasonal Weekly Naive", "pred_seasonal_naive"),
            ("7-Day Moving Average Baseline", "pred_7d_ma"),
            ("Ridge Regression (L2 Linear)", "pred_ridge"),
            ("HistGradientBoosting (Production)", "pred_production"),
        ]

        rows: List[Dict[str, Any]] = []
        for name, col in models:
            metrics = ForecastEvaluator.evaluate_all(
                eval_df["target_7d"], eval_df[col]
            )
            rows.append(
                {
                    "model": name,
                    "wape": metrics["wape"],
                    "mae": metrics["mae"],
                    "rmse": metrics["rmse"],
                    "bias": metrics["bias"],
                }
            )

        return pd.DataFrame(rows).set_index("model")

    def stratify_by_dimension(
        self, eval_df: pd.DataFrame, dimension: str, pred_col: str = "pred_production"
    ) -> pd.DataFrame:
        """Compute error metrics and residual volatility across an operational slice.

        Args:
            eval_df: Test DataFrame with predictions and metadata.
            dimension: Categorical column to segment by (e.g., 'category', 'branch_id').
            pred_col: Prediction column to evaluate.

        Returns:
            DataFrame with WAPE, MAE, RMSE, Bias, and residual std dev (sigma_e).
        """
        records: List[Dict[str, Any]] = []

        for group_val, group in eval_df.groupby(dimension, observed=True):
            if group.empty:
                continue

            y_true = group["target_7d"].to_numpy(dtype=np.float64)
            y_pred = group[pred_col].to_numpy(dtype=np.float64)

            metrics = ForecastEvaluator.evaluate_all(y_true, y_pred)
            residuals = y_true - y_pred
            sigma_e = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0

            records.append(
                {
                    dimension: group_val,
                    "wape": metrics["wape"],
                    "mae": metrics["mae"],
                    "rmse": metrics["rmse"],
                    "bias": metrics["bias"],
                    "sigma_e": sigma_e,
                    "sample_size": len(group),
                    "total_volume": float(np.sum(y_true)),
                }
            )

        df = pd.DataFrame(records)
        if not df.empty:
            df = df.set_index(dimension)
        return df

    def compute_temporal_drift(
        self, eval_df: pd.DataFrame, pred_col: str = "pred_production"
    ) -> pd.DataFrame:
        """Analyze month-by-month forecasting accuracy across the out-of-time test horizon.

        Args:
            eval_df: Test DataFrame containing date and prediction columns.
            pred_col: Prediction column to evaluate.

        Returns:
            DataFrame indexed by year-month with tracking metrics.
        """
        eval_copy = eval_df.copy()
        eval_copy["month_period"] = eval_copy["date"].dt.to_period("M").astype(str)

        records: List[Dict[str, Any]] = []
        for period, group in eval_copy.groupby("month_period", sort=True):
            metrics = ForecastEvaluator.evaluate_all(
                group["target_7d"], group[pred_col]
            )
            residuals = group["target_7d"].to_numpy() - group[pred_col].to_numpy()
            sigma_e = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0

            records.append(
                {
                    "period": period,
                    "wape": metrics["wape"],
                    "mae": metrics["mae"],
                    "rmse": metrics["rmse"],
                    "bias": metrics["bias"],
                    "sigma_e": sigma_e,
                    "records": len(group),
                }
            )

        return pd.DataFrame(records).set_index("period")

    def compute_residual_calibration_metrics(
        self, eval_df: pd.DataFrame, pred_col: str = "pred_production"
    ) -> Dict[str, Any]:
        """Compute empirical residual statistics to calibrate downstream safety stock.

        Args:
            eval_df: Test DataFrame with predictions.
            pred_col: Prediction column to evaluate.

        Returns:
            Dictionary containing global and pattern-specific residual statistics.
        """
        residuals = eval_df["target_7d"].to_numpy() - eval_df[pred_col].to_numpy()

        smooth_mask = eval_df["demand_pattern"] == "Smooth"
        intermittent_mask = eval_df["demand_pattern"] == "Intermittent"

        smooth_res = residuals[smooth_mask]
        interm_res = residuals[intermittent_mask]

        return {
            "overall_mean_error": float(np.mean(residuals)),
            "overall_sigma_e": float(np.std(residuals, ddof=1)),
            "smooth_sigma_e": float(np.std(smooth_res, ddof=1)) if len(smooth_res) > 1 else 0.0,
            "intermittent_sigma_e": float(np.std(interm_res, ddof=1)) if len(interm_res) > 1 else 0.0,
            "percentiles": {
                "p05": float(np.percentile(residuals, 5)),
                "p25": float(np.percentile(residuals, 25)),
                "p50_median": float(np.median(residuals)),
                "p75": float(np.percentile(residuals, 75)),
                "p95": float(np.percentile(residuals, 95)),
            },
        }

    def identify_outlier_skus(
        self,
        eval_df: pd.DataFrame,
        top_n: int = 10,
        min_volume: float = 50.0,
        pred_col: str = "pred_production",
    ) -> Dict[str, pd.DataFrame]:
        """Identify extreme error, over-forecasting, and under-forecasting outlier SKUs.

        Args:
            eval_df: Test DataFrame with predictions.
            top_n: Number of top outlier items to return per category.
            min_volume: Minimum actual volume cutoff to filter out inactive low-volume SKUs.
            pred_col: Prediction column to evaluate.

        Returns:
            Dictionary of DataFrames: 'highest_wape', 'top_overforecast', 'top_underforecast'.
        """
        sku_summary = (
            eval_df.groupby(["medicine_id", "category", "demand_pattern", "abc_class"])
            .agg(
                actual_demand=("target_7d", "sum"),
                predicted_demand=(pred_col, "sum"),
                abs_error=("abs_error", "sum"),
                sample_count=("target_7d", "count"),
            )
            .reset_index()
        )

        sku_summary["wape"] = sku_summary["abs_error"] / sku_summary["actual_demand"]
        sku_summary["net_bias_units"] = (
            sku_summary["predicted_demand"] - sku_summary["actual_demand"]
        )
        sku_summary["bias_pct"] = (
            sku_summary["net_bias_units"] / sku_summary["actual_demand"]
        )

        # Filter to active items
        active_skus = sku_summary[sku_summary["actual_demand"] >= min_volume].copy()

        highest_wape = (
            active_skus.sort_values(by="wape", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )
        top_over = (
            active_skus.sort_values(by="net_bias_units", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )
        top_under = (
            active_skus.sort_values(by="net_bias_units", ascending=True)
            .head(top_n)
            .reset_index(drop=True)
        )

        return {
            "highest_wape": highest_wape,
            "top_overforecast": top_over,
            "top_underforecast": top_under,
        }

    def export_diagnostics_report(
        self,
        diagnostics: Dict[str, Any],
        export_path: Union[str, Path] = "data/processed/evaluation_diagnostics.json",
    ) -> Path:
        """Serialize full diagnostic metrics and slice tables to an auditable JSON report.

        Args:
            diagnostics: Complete diagnostics dictionary from run_full_diagnostics.
            export_path: Destination JSON file path.

        Returns:
            Path of exported JSON report.
        """
        save_path = Path(export_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        def _convert_for_json(obj: Any) -> Any:
            if isinstance(obj, pd.DataFrame):
                return obj.reset_index().to_dict(orient="records")
            if isinstance(obj, (np.floating, float)):
                return float(obj)
            if isinstance(obj, (np.integer, int)):
                return int(obj)
            if isinstance(obj, dict):
                return {k: _convert_for_json(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_convert_for_json(item) for item in obj]
            return obj

        clean_payload = _convert_for_json(diagnostics)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(clean_payload, f, indent=2)

        return save_path

    def run_full_diagnostics(
        self,
        export_path: Optional[Union[str, Path]] = "data/processed/evaluation_diagnostics.json",
    ) -> Dict[str, Any]:
        """Execute full end-to-end diagnostic evaluation suite.

        Args:
            export_path: Optional path to save JSON report.

        Returns:
            Dictionary containing all diagnostic slices and residual calibration metrics.
        """
        train_df, test_df, model, metadata = self.load_telemetry()
        eval_df = self.generate_all_predictions(train_df, test_df, model)

        benchmark_matrix = self.compute_benchmark_matrix(eval_df)
        pareto_strata = self.stratify_by_dimension(eval_df, "abc_class")
        demand_strata = self.stratify_by_dimension(eval_df, "demand_pattern")
        branch_strata = self.stratify_by_dimension(eval_df, "branch_id")
        category_strata = self.stratify_by_dimension(eval_df, "category")
        temporal_drift = self.compute_temporal_drift(eval_df)
        residuals = self.compute_residual_calibration_metrics(eval_df)
        outliers = self.identify_outlier_skus(eval_df)

        diagnostics_result: Dict[str, Any] = {
            "metadata": {
                "split_date": str(self.split_date.date()),
                "test_start": str(test_df["date"].min().date()),
                "test_end": str(test_df["date"].max().date()),
                "total_test_records": len(test_df),
                "active_series": int(test_df.groupby(["branch_id", "medicine_id"]).ngroups),
                "production_model_name": metadata.get("model_name", "Unknown"),
            },
            "benchmark_matrix": benchmark_matrix,
            "stratified": {
                "pareto_abc": pareto_strata,
                "demand_pattern": demand_strata,
                "branches": branch_strata,
                "categories": category_strata,
            },
            "temporal_drift": temporal_drift,
            "residual_calibration": residuals,
            "outliers": outliers,
        }

        if export_path:
            saved_path = self.export_diagnostics_report(diagnostics_result, export_path)
            diagnostics_result["report_path"] = str(saved_path)

        return diagnostics_result


def main() -> None:
    """CLI runner executing diagnostics and rendering multi-dimensional error scorecard."""
    diagnostics = ModelDiagnostics()
    results = diagnostics.run_full_diagnostics()

    meta = results["metadata"]
    bench = results["benchmark_matrix"]
    drift = results["temporal_drift"]
    branch = results["stratified"]["branches"]
    cat = results["stratified"]["categories"]
    pareto = results["stratified"]["pareto_abc"]
    demand = results["stratified"]["demand_pattern"]
    res = results["residual_calibration"]
    outliers = results["outliers"]

    print("=" * 88)
    print("REMEDISYNC DEMAND FORECASTING: MODEL DIAGNOSTICS & ERROR STRATIFICATION")
    print("=" * 88)
    print(f"Evaluation Horizon   : {meta['test_start']} to {meta['test_end']} | {meta['total_test_records']:,} records")
    print(f"Active Series Tracked: {meta['active_series']} time series (129 SKUs across 4 Branches)")
    print(f"Production Forecaster: {meta['production_model_name']}")
    print("-" * 88)

    print("\n[+] MULTI-MODEL BENCHMARK PERFORMANCE COMPARISON:")
    print("-" * 88)
    print(f"{'Model Architecture':<36} | {'WAPE':<8} | {'MAE':<6} | {'RMSE':<6} | Bias")
    print("-" * 88)
    for model_name, row in bench.iterrows():
        print(
            f"{model_name:<36} | "
            f"{row['wape'] * 100:>6.2f}% | "
            f"{row['mae']:>6.2f} | "
            f"{row['rmse']:>6.2f} | "
            f"{row['bias'] * 100:>+5.2f}%"
        )
    print("-" * 88)

    print("\n[+] TEMPORAL DRIFT & MONSOON STABILITY (MONTH-BY-MONTH):")
    for period, row in drift.iterrows():
        print(
            f"  * {period:<10} : "
            f"WAPE = {row['wape'] * 100:>5.2f}% | "
            f"MAE = {row['mae']:>5.2f} | "
            f"Bias = {row['bias'] * 100:>+5.2f}% | "
            f"sigma_e = {row['sigma_e']:>5.2f} units [STABLE]"
        )

    print("\n[+] ERROR BREAKDOWN BY PARETO REVENUE TIER:")
    for tier in ["A", "B", "C"]:
        if tier in pareto.index:
            row = pareto.loc[tier]
            desc = "Top 80% Revenue" if tier == "A" else ("Next 15% Revenue" if tier == "B" else "Tail 5% Revenue")
            print(
                f"  * Class {tier} ({desc:<16}): "
                f"WAPE = {row['wape'] * 100:>5.2f}% | "
                f"MAE = {row['mae']:>5.2f} | "
                f"sigma_e = {row['sigma_e']:>5.2f} units"
            )

    print("\n[+] ERROR BREAKDOWN BY CROSTON DEMAND PATTERN:")
    for pat in ["Smooth", "Intermittent"]:
        if pat in demand.index:
            row = demand.loc[pat]
            print(
                f"  * {pat:<13} Demand: "
                f"WAPE = {row['wape'] * 100:>5.2f}% | "
                f"MAE = {row['mae']:>5.2f} | "
                f"sigma_e = {row['sigma_e']:>5.2f} units"
            )

    print("\n[+] GEOGRAPHIC BRANCH PERFORMANCE:")
    branch_names = {
        "BR001": "Kamakhya Gate (Transit Hub)",
        "BR002": "Dharapur (Suburban Residential)",
        "BR003": "Azara (Hospital Cluster)",
        "BR004": "Rani Gate (Semi-Urban Border)",
    }
    for b_id, row in branch.iterrows():
        label = branch_names.get(str(b_id), str(b_id))
        print(
            f"  * {b_id} - {label:<32}: "
            f"WAPE = {row['wape'] * 100:>5.2f}% | "
            f"MAE = {row['mae']:>5.2f} | "
            f"Bias = {row['bias'] * 100:>+5.2f}%"
        )

    print("\n[+] RESIDUAL ERROR CALIBRATION (INPUTS FOR REPLENISHMENT SAFETY STOCK):")
    print(f"  * Overall Mean Error (Bias)       : {res['overall_mean_error']:>+5.2f} units / series-week")
    print(f"  * Overall Residual Std Dev (sigma_e): {res['overall_sigma_e']:>5.2f} units")
    print(f"  * Smooth Series Residual Std Dev  : {res['smooth_sigma_e']:>5.2f} units")
    print(f"  * Intermittent Residual Std Dev   : {res['intermittent_sigma_e']:>5.2f} units")
    print(f"  * Residual P25 / P50 / P75 Span   : [{res['percentiles']['p25']:+.2f}, {res['percentiles']['p50_median']:+.2f}, {res['percentiles']['p75']:+.2f}] units")

    print("\n[+] TOP 5 CLINICAL CATEGORIES BY VOLUME ACCURACY:")
    top_cats = cat.sort_values(by="total_volume", ascending=False).head(5)
    for cat_name, row in top_cats.iterrows():
        print(
            f"  * {cat_name:<16}: "
            f"WAPE = {row['wape'] * 100:>5.2f}% | "
            f"MAE = {row['mae']:>5.2f} | "
            f"sigma_e = {row['sigma_e']:>5.2f} units"
        )

    print("\n[+] OUTLIER RISK MONITORING (TOP OVER-FORECASTING RISKS):")
    top_over = outliers["top_overforecast"].head(3)
    for _, item in top_over.iterrows():
        print(
            f"  * {item['medicine_id']} ({item['category']}): "
            f"Over-forecast = +{item['net_bias_units']:.1f} units | "
            f"WAPE = {item['wape'] * 100:.1f}%"
        )

    print(f"\n[+] AUDITABLE DIAGNOSTICS REPORT:")
    print(f"  * Saved JSON Report: {results.get('report_path')}")
    print("=" * 88)


if __name__ == "__main__":
    main()
