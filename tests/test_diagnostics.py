"""Unit tests for model diagnostics and error stratification service.

Validates multi-model benchmarking, dimensional stratification, temporal drift,
residual variance extraction (sigma_e), outlier SKU isolation, and JSON report export.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.models.diagnostics import ModelDiagnostics


class TestModelDiagnostics:
    """Verification suite for ModelDiagnostics service."""

    @pytest.fixture
    def diagnostics(self) -> ModelDiagnostics:
        """Initialize ModelDiagnostics pointing to production stores."""
        return ModelDiagnostics(
            data_path="data/processed/feature_matrix.parquet",
            model_path="models/production_forecaster.joblib",
            split_date="2026-07-01",
        )

    def test_load_telemetry(self, diagnostics: ModelDiagnostics) -> None:
        """Verify telemetry and model loading contracts."""
        train_df, test_df, model, metadata = diagnostics.load_telemetry()

        assert len(train_df) == 267288
        assert len(test_df) == 43860
        assert train_df["date"].max() < pd.Timestamp("2026-07-01")
        assert test_df["date"].min() >= pd.Timestamp("2026-07-01")
        assert model is not None
        assert "model_name" in metadata

    def test_generate_all_predictions(self, diagnostics: ModelDiagnostics) -> None:
        """Verify prediction generation across all 4 benchmark models."""
        train_df, test_df, model, _ = diagnostics.load_telemetry()
        # Use small slice of test_df for speed
        test_slice = test_df.head(200).copy()
        train_slice = train_df.tail(500).copy()

        eval_df = diagnostics.generate_all_predictions(train_slice, test_slice, model)

        assert "pred_7d_ma" in eval_df.columns
        assert "pred_seasonal_naive" in eval_df.columns
        assert "pred_ridge" in eval_df.columns
        assert "pred_production" in eval_df.columns
        assert "error" in eval_df.columns
        assert "abs_error" in eval_df.columns

        # Verify physical boundaries
        for col in ["pred_7d_ma", "pred_seasonal_naive", "pred_ridge", "pred_production"]:
            assert (eval_df[col] >= 0.0).all()

    def test_compute_benchmark_matrix(self, diagnostics: ModelDiagnostics) -> None:
        """Verify multi-model comparison matrix structure and metrics."""
        train_df, test_df, model, _ = diagnostics.load_telemetry()
        test_slice = test_df.head(500).copy()
        train_slice = train_df.tail(1000).copy()

        eval_df = diagnostics.generate_all_predictions(train_slice, test_slice, model)
        bench_matrix = diagnostics.compute_benchmark_matrix(eval_df)

        expected_models = [
            "Seasonal Weekly Naive",
            "7-Day Moving Average Baseline",
            "Ridge Regression (L2 Linear)",
            "HistGradientBoosting (Production)",
        ]
        for name in expected_models:
            assert name in bench_matrix.index

        for metric in ["wape", "mae", "rmse", "bias"]:
            assert metric in bench_matrix.columns
            assert not bench_matrix[metric].isna().any()

    def test_stratify_by_dimension(self, diagnostics: ModelDiagnostics) -> None:
        """Verify dimensional error slicing and sigma_e calculation."""
        train_df, test_df, model, _ = diagnostics.load_telemetry()
        test_slice = test_df.head(500).copy()
        train_slice = train_df.tail(1000).copy()

        eval_df = diagnostics.generate_all_predictions(train_slice, test_slice, model)

        pareto_df = diagnostics.stratify_by_dimension(eval_df, "abc_class")
        assert "A" in pareto_df.index
        assert "sigma_e" in pareto_df.columns
        assert (pareto_df["sigma_e"] >= 0.0).all()

        demand_df = diagnostics.stratify_by_dimension(eval_df, "demand_pattern")
        assert "Smooth" in demand_df.index
        assert "sigma_e" in demand_df.columns

    def test_compute_temporal_drift(self, diagnostics: ModelDiagnostics) -> None:
        """Verify monthly backtest drift computation."""
        train_df, test_df, model, _ = diagnostics.load_telemetry()
        test_slice = test_df.head(1000).copy()
        train_slice = train_df.tail(1000).copy()

        eval_df = diagnostics.generate_all_predictions(train_slice, test_slice, model)
        drift_df = diagnostics.compute_temporal_drift(eval_df)

        assert len(drift_df) > 0
        assert "wape" in drift_df.columns
        assert "sigma_e" in drift_df.columns

    def test_compute_residual_calibration_metrics(
        self, diagnostics: ModelDiagnostics
    ) -> None:
        """Verify safety stock calibration residual metrics and percentiles."""
        train_df, test_df, model, _ = diagnostics.load_telemetry()
        test_slice = test_df.head(500).copy()
        train_slice = train_df.tail(1000).copy()

        eval_df = diagnostics.generate_all_predictions(train_slice, test_slice, model)
        res = diagnostics.compute_residual_calibration_metrics(eval_df)

        assert "overall_sigma_e" in res
        assert "smooth_sigma_e" in res
        assert "percentiles" in res
        assert res["overall_sigma_e"] >= 0.0

        p = res["percentiles"]
        assert p["p05"] <= p["p25"] <= p["p50_median"] <= p["p75"] <= p["p95"]

    def test_identify_outlier_skus(self, diagnostics: ModelDiagnostics) -> None:
        """Verify detection and ranking of outlier high-error and biased SKUs."""
        train_df, test_df, model, _ = diagnostics.load_telemetry()
        test_slice = test_df.head(1000).copy()
        train_slice = train_df.tail(1000).copy()

        eval_df = diagnostics.generate_all_predictions(train_slice, test_slice, model)
        outliers = diagnostics.identify_outlier_skus(
            eval_df, top_n=5, min_volume=1.0
        )

        assert "highest_wape" in outliers
        assert "top_overforecast" in outliers
        assert "top_underforecast" in outliers

        assert len(outliers["highest_wape"]) <= 5
        assert len(outliers["top_overforecast"]) <= 5

    def test_export_diagnostics_report(
        self, diagnostics: ModelDiagnostics, tmp_path: Path
    ) -> None:
        """Verify JSON report serialization and schema validity."""
        train_df, test_df, model, meta = diagnostics.load_telemetry()
        test_slice = test_df.head(200).copy()
        train_slice = train_df.tail(500).copy()

        eval_df = diagnostics.generate_all_predictions(train_slice, test_slice, model)
        bench = diagnostics.compute_benchmark_matrix(eval_df)
        pareto = diagnostics.stratify_by_dimension(eval_df, "abc_class")
        res = diagnostics.compute_residual_calibration_metrics(eval_df)
        outliers = diagnostics.identify_outlier_skus(eval_df, top_n=3, min_volume=1.0)

        data = {
            "metadata": {"test_records": len(test_slice)},
            "benchmark_matrix": bench,
            "stratified": {"pareto": pareto},
            "residuals": res,
            "outliers": outliers,
        }

        export_file = tmp_path / "test_report.json"
        saved = diagnostics.export_diagnostics_report(data, export_file)

        assert saved.exists()
        with open(saved, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert "metadata" in loaded
        assert "benchmark_matrix" in loaded
        assert "residuals" in loaded
        assert isinstance(loaded["benchmark_matrix"], list)
