"""Unit tests for baseline demand forecaster and evaluation engine.

Validates chronological dataset partitioning, error metric formulations,
and heuristic prediction constraints.
"""

import numpy as np
import pandas as pd
import pytest

from src.models.baseline import BaselineForecaster
from src.models.evaluator import ForecastEvaluator


class TestForecastEvaluator:
    """Mathematical and contract verification for ForecastEvaluator."""

    def test_metric_mathematical_accuracy(self) -> None:
        """Verify WAPE, MAE, RMSE, and Bias on deterministic mock vectors."""
        y_true = np.array([10.0, 20.0, 30.0, 40.0])
        y_pred = np.array([12.0, 18.0, 33.0, 37.0])

        # |10-12|=2, |20-18|=2, |30-33|=3, |40-37|=3 -> sum = 10.0
        # total_actual = 100.0
        wape = ForecastEvaluator.compute_wape(y_true, y_pred)
        mae = ForecastEvaluator.compute_mae(y_true, y_pred)
        rmse = ForecastEvaluator.compute_rmse(y_true, y_pred)
        bias = ForecastEvaluator.compute_bias(y_true, y_pred)

        assert pytest.approx(wape, rel=1e-5) == 0.10
        assert pytest.approx(mae, rel=1e-5) == 2.50
        assert pytest.approx(rmse, rel=1e-5) == np.sqrt(26.0 / 4.0)
        assert pytest.approx(bias, rel=1e-5) == 0.0

    def test_perfect_prediction_metrics(self) -> None:
        """Verify metric behavior on perfect forecasts."""
        y_true = np.array([5.0, 15.0, 25.0])
        metrics = ForecastEvaluator.evaluate_all(y_true, y_true)

        assert metrics["wape"] == 0.0
        assert metrics["mae"] == 0.0
        assert metrics["rmse"] == 0.0
        assert metrics["bias"] == 0.0

    def test_bias_directional_polarity(self) -> None:
        """Verify that positive bias reflects over-forecasting and negative reflects under-forecasting."""
        y_true = np.array([10.0, 20.0])
        y_over = np.array([12.0, 22.0])
        y_under = np.array([8.0, 18.0])

        assert ForecastEvaluator.compute_bias(y_true, y_over) > 0.0
        assert ForecastEvaluator.compute_bias(y_true, y_under) < 0.0

    def test_input_validation_errors(self) -> None:
        """Ensure input validation catches length mismatches, empty vectors, and NaNs."""
        with pytest.raises(ValueError, match="Dimension mismatch"):
            ForecastEvaluator.compute_wape([1.0, 2.0], [1.0])

        with pytest.raises(ValueError, match="empty"):
            ForecastEvaluator.compute_mae([], [])

        with pytest.raises(ValueError, match="NaN"):
            ForecastEvaluator.compute_rmse([1.0, np.nan], [1.0, 2.0])

    def test_stratified_evaluation(self) -> None:
        """Verify stratified slicing across business segments."""
        df = pd.DataFrame(
            {
                "abc_class": ["A", "A", "B", "B"],
                "y_true": [100.0, 200.0, 10.0, 20.0],
                "y_pred": [110.0, 190.0, 12.0, 18.0],
            }
        )
        result = ForecastEvaluator.evaluate_stratified(df, "y_true", "y_pred", "abc_class")

        assert "A" in result.index
        assert "B" in result.index
        assert "wape" in result.columns
        assert pytest.approx(result.loc["A", "wape"], rel=1e-5) == 20.0 / 300.0
        assert pytest.approx(result.loc["B", "wape"], rel=1e-5) == 4.0 / 30.0


class TestBaselineForecaster:
    """Integrity and functional tests for BaselineForecaster service."""

    @pytest.fixture
    def forecaster(self) -> BaselineForecaster:
        """Initialize forecaster pointing to production parquet store."""
        return BaselineForecaster(
            data_path="data/processed/feature_matrix.parquet",
            split_date="2026-07-01",
        )

    def test_chronological_split_integrity(self, forecaster: BaselineForecaster) -> None:
        """Verify zero lookahead leakage, date boundary isolation, and record counts."""
        df = forecaster.load_data()
        train_df, test_df = forecaster.split_data(df)

        split_date = pd.Timestamp("2026-07-01")

        # Temporal bounds isolation
        assert train_df["date"].max() < split_date
        assert test_df["date"].min() >= split_date

        # Zero row leakage or loss
        assert len(train_df) + len(test_df) == len(df)
        assert len(train_df) == 267288
        assert len(test_df) == 43860

        # Exact series continuity (516 active series)
        train_series = set(zip(train_df["branch_id"], train_df["medicine_id"]))
        test_series = set(zip(test_df["branch_id"], test_df["medicine_id"]))
        assert len(train_series) == 516
        assert len(test_series) == 516
        assert train_series == test_series

    def test_prediction_properties(self, forecaster: BaselineForecaster) -> None:
        """Verify non-negativity and mathematical exactness of heuristic predictions."""
        df = forecaster.load_data()
        _, test_df = forecaster.split_data(df)

        pred_ma = forecaster.predict_moving_average_7d(test_df)
        pred_seasonal = forecaster.predict_seasonal_naive(test_df)

        # Vector dimensions
        assert len(pred_ma) == len(test_df)
        assert len(pred_seasonal) == len(test_df)

        # Domain boundary: unit demand cannot be negative
        assert (pred_ma >= 0.0).all()
        assert (pred_seasonal >= 0.0).all()

        # Deterministic formula alignment: 7 * rolling_mean_7
        expected_ma = np.maximum(0.0, 7.0 * test_df["rolling_mean_7"].to_numpy())
        np.testing.assert_allclose(pred_ma, expected_ma)

    def test_benchmark_runner_contract(self, forecaster: BaselineForecaster) -> None:
        """Verify end-to-end benchmark execution and hurdle contract calculation."""
        benchmark = forecaster.run_benchmark()

        assert "metadata" in benchmark
        assert "global_metrics" in benchmark
        assert "stratified" in benchmark
        assert "promotion_hurdles" in benchmark

        global_ma = benchmark["global_metrics"]["moving_average_7d"]
        hurdles = benchmark["promotion_hurdles"]

        assert 0.0 < global_ma["wape"] < 1.0
        assert hurdles["target_wape_threshold"] == pytest.approx(global_ma["wape"] * 0.80)
        assert hurdles["class_a_wape_threshold"] == 0.180
