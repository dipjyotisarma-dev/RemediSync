"""
Unit tests for the OOP DemandProfiler service.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.features.demand_profiler import DemandProfiler, CrostonThresholds


@pytest.fixture
def profiler() -> DemandProfiler:
    """Provides a DemandProfiler instance pointing to the raw dataset."""
    prof = DemandProfiler(data_dir="data/raw")
    prof.load_data()
    return prof


def test_classify_demand_pattern_quadrants():
    """Validates the 4 Croston demand quadrant boundary classifications."""
    assert DemandProfiler.classify_demand_pattern(1.10, 0.30) == "Smooth"
    assert DemandProfiler.classify_demand_pattern(1.50, 0.30) == "Intermittent"
    assert DemandProfiler.classify_demand_pattern(1.10, 0.60) == "Erratic"
    assert DemandProfiler.classify_demand_pattern(1.50, 0.60) == "Lumpy"

    # Exact threshold boundary checks
    assert DemandProfiler.classify_demand_pattern(
        CrostonThresholds.ADI_CUTOFF, 0.10
    ) == "Intermittent"
    assert DemandProfiler.classify_demand_pattern(
        1.0, CrostonThresholds.CV2_CUTOFF
    ) == "Erratic"


def test_croston_metrics_dimensions_and_ranges(profiler: DemandProfiler):
    """Verifies that Croston metrics compute for all 516 series within valid bounds."""
    metrics_df = profiler.compute_croston_metrics()

    # 129 medicines * 4 branches = 516 series
    assert len(metrics_df) == 516
    assert (metrics_df["adi"] >= 1.0).all()
    assert (metrics_df["cv2"] >= 0.0).all()
    assert (metrics_df["zero_demand_rate"].between(0.0, 1.0)).all()

    valid_patterns = {"Smooth", "Intermittent", "Erratic", "Lumpy"}
    assert set(metrics_df["demand_pattern"].unique()).issubset(valid_patterns)


def test_abc_classification(profiler: DemandProfiler):
    """Verifies ABC Pareto segmentation properties and cumulative share continuity."""
    metrics_df = profiler.compute_croston_metrics()
    abc_df = profiler.compute_abc_classification(metrics_df)

    assert len(abc_df) == 129
    assert set(abc_df["abc_class"].unique()).issubset({"A", "B", "C"})
    assert abc_df["cumulative_share"].is_monotonic_increasing
    assert np.isclose(abc_df["cumulative_share"].iloc[-1], 1.0, atol=1e-4)


def test_temporal_seasonality(profiler: DemandProfiler):
    """Verifies temporal decomposition structures."""
    seasonality = profiler.compute_temporal_seasonality()

    assert "day_of_week_index" in seasonality
    assert "payday_surge" in seasonality

    dow_df = seasonality["day_of_week_index"]
    assert len(dow_df["day_of_week_num"].unique()) == 7
    assert (dow_df["dow_index"] > 0).all()

    payday_df = seasonality["payday_surge"]
    assert "payday_surge_ratio" in payday_df.columns
    assert (payday_df["payday_surge_ratio"] > 0).all()


def test_full_profiles_generation_and_export(profiler: DemandProfiler, tmp_path: Path):
    """Verifies complete profile generation and CSV export."""
    profiles_df = profiler.generate_full_profiles()

    assert len(profiles_df) == 516
    assert profiles_df["demand_pattern"].isna().sum() == 0
    assert profiles_df["abc_class"].isna().sum() == 0
    assert profiles_df["mean_daily_demand"].isna().sum() == 0

    export_path = tmp_path / "sku_demand_profiles.csv"
    exported_file = profiler.export_profiles(output_path=export_path)

    assert exported_file.exists()
    loaded_df = pd.read_csv(exported_file)
    assert len(loaded_df) == 516
