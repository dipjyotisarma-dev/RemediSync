"""Unit tests for machine learning demand forecaster and production training pipeline.

Validates feature transformations, model fitting, prediction bounds,
release gate evaluations, and artifact persistence.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingRegressor

from src.models.forecaster import DemandForecaster


@pytest.fixture
def sample_feature_df() -> pd.DataFrame:
    """Generate a synthetic DataFrame matching the feature matrix schema for unit testing."""
    n_rows = 100
    rng = np.random.default_rng(42)

    data = {
        "date": pd.date_range("2026-06-01", periods=n_rows, freq="D"),
        "branch_id": rng.choice(["BR001", "BR002"], size=n_rows),
        "medicine_id": rng.choice(["MED001", "MED002"], size=n_rows),
        "category": rng.choice(["Analgesic", "Antibiotic"], size=n_rows),
        "dosage_form": rng.choice(["Tablet", "Syrup"], size=n_rows),
        "location_type": rng.choice(["Urban", "Suburban"], size=n_rows),
        "demand_pattern": rng.choice(["Smooth", "Intermittent"], size=n_rows),
        "abc_class": rng.choice(["A", "B", "C"], size=n_rows),
        "target_7d": rng.uniform(5.0, 50.0, size=n_rows),
    }

    # Populate default numerical columns
    for col in DemandForecaster.DEFAULT_NUMERICAL_FEATURES:
        data[col] = rng.uniform(0.0, 20.0, size=n_rows)

    return pd.DataFrame(data)


class TestDemandForecaster:
    """Verification suite for DemandForecaster operations."""

    def test_feature_preparation(self, sample_feature_df: pd.DataFrame) -> None:
        """Verify feature extraction and dtype conversions for linear and tree models."""
        forecaster = DemandForecaster()

        # Linear features (raw strings preserved for OneHotEncoder)
        X_linear, y = forecaster.prepare_features(sample_feature_df, for_tree=False)
        assert X_linear.shape == (100, 28)
        assert len(y) == 100
        assert not isinstance(X_linear["category"].dtype, pd.CategoricalDtype)

        # Tree features (categoricals converted to category dtype)
        X_tree, _ = forecaster.prepare_features(sample_feature_df, for_tree=True)
        assert isinstance(X_tree["category"].dtype, pd.CategoricalDtype)
        assert isinstance(X_tree["branch_id"].dtype, pd.CategoricalDtype)

    def test_ridge_training_and_prediction(self, sample_feature_df: pd.DataFrame) -> None:
        """Verify Ridge pipeline fitting and non-negativity of predictions."""
        forecaster = DemandForecaster()
        X, y = forecaster.prepare_features(sample_feature_df, for_tree=False)

        pipeline = forecaster.train_ridge(X, y, alpha=5.0)
        assert isinstance(pipeline, Pipeline)

        preds = forecaster.predict(pipeline, X)
        assert preds.shape == (100,)
        assert (preds >= 0.0).all()

    def test_hgb_training_and_prediction(self, sample_feature_df: pd.DataFrame) -> None:
        """Verify HistGradientBoostingRegressor fitting with native categorical inputs."""
        forecaster = DemandForecaster()
        X, y = forecaster.prepare_features(sample_feature_df, for_tree=True)

        model = forecaster.train_hist_gradient_boosting(X, y, max_iter=10)
        assert isinstance(model, HistGradientBoostingRegressor)

        preds = forecaster.predict(model, X)
        assert preds.shape == (100,)
        assert (preds >= 0.0).all()

    def test_promotion_gates_evaluation(self, sample_feature_df: pd.DataFrame) -> None:
        """Verify release gate evaluation logic across passing and failing conditions."""
        forecaster = DemandForecaster()
        X, _ = forecaster.prepare_features(sample_feature_df, for_tree=False)

        # Mock model that predicts perfect truth
        class PerfectMockModel:
            def predict(self, df: pd.DataFrame) -> np.ndarray:
                return sample_feature_df["target_7d"].to_numpy()

        eval_res = forecaster.evaluate_candidate(
            PerfectMockModel(), X, sample_feature_df, baseline_wape=0.2258
        )

        assert eval_res["gates"]["gate_1_passed"] is True
        assert eval_res["gates"]["gate_2_passed"] is True
        assert eval_res["gates"]["gate_3_passed"] is True
        assert eval_res["gates"]["all_passed"] is True

        # Mock model with extreme bias and high error
        class FailingMockModel:
            def predict(self, df: pd.DataFrame) -> np.ndarray:
                return sample_feature_df["target_7d"].to_numpy() * 2.5

        failing_res = forecaster.evaluate_candidate(
            FailingMockModel(), X, sample_feature_df, baseline_wape=0.2258
        )
        assert failing_res["gates"]["all_passed"] is False

    def test_model_serialization_and_deserialization(
        self, sample_feature_df: pd.DataFrame, tmp_path: Path
    ) -> None:
        """Verify model persistence to disk and round-trip deserialization."""
        forecaster = DemandForecaster()
        X, y = forecaster.prepare_features(sample_feature_df, for_tree=False)
        pipeline = forecaster.train_ridge(X, y, alpha=1.0)

        metadata = {"model_name": "TestRidge", "version": "1.0.0"}
        artifact_path = tmp_path / "models" / "test_model.joblib"

        saved_path = forecaster.save_model(pipeline, metadata, artifact_path)
        assert saved_path.exists()

        loaded_model, loaded_meta = forecaster.load_model(saved_path)
        assert loaded_meta["model_name"] == "TestRidge"

        # Predictions before and after serialization must match identically
        orig_preds = forecaster.predict(pipeline, X)
        loaded_preds = forecaster.predict(loaded_model, X)
        np.testing.assert_allclose(orig_preds, loaded_preds)

    def test_full_production_training_pipeline(self) -> None:
        """Verify end-to-end training pipeline on real feature store data."""
        forecaster = DemandForecaster(
            data_path="data/processed/feature_matrix.parquet",
            split_date="2026-07-01",
        )
        results = forecaster.run_training_pipeline(save_artifact=False)

        assert "candidates" in results
        assert "Ridge Regression" in results["candidates"]
        assert "HistGradientBoosting" in results["candidates"]
        assert "winner" in results

        hgb_data = results["candidates"]["HistGradientBoosting"]
        assert hgb_data["metrics"]["wape"] < 0.1806
        assert hgb_data["gates"]["all_passed"] is True
        assert results["winner"]["name"] == "HistGradientBoosting"
