"""
Unit tests for the FeaturePipeline service.
"""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from src.features.feature_pipeline import FeaturePipeline


@pytest.fixture
def pipeline() -> FeaturePipeline:
    """Provides an initialized FeaturePipeline instance."""
    pipe = FeaturePipeline(raw_dir="data/raw", processed_dir="data/processed")
    pipe.load_data()
    return pipe


def test_zero_lookahead_leakage(pipeline: FeaturePipeline):
    """
    Verifies that lag and rolling features observe the strict t-1 boundary
    and contain zero lookahead leakage into date t or future dates.
    """
    matrix = pipeline.generate_feature_matrix()

    # Pick a sample series
    sample_series = matrix[
        (matrix["branch_id"] == "BR001") & (matrix["medicine_id"] == "MED001")
    ].sort_values("date").reset_index(drop=True)

    raw_sales = pipeline.sales_df[
        (pipeline.sales_df["branch_id"] == "BR001") & (pipeline.sales_df["medicine_id"] == "MED001")
    ].sort_values("date").reset_index(drop=True)

    # Check date alignment for date t
    sample_date = sample_series.iloc[10]["date"]
    row_feat = sample_series.iloc[10]

    raw_idx = raw_sales[raw_sales["date"] == sample_date].index[0]

    # sales_lag_7 at date t must exactly equal raw units_sold at date t-7
    expected_lag_7 = raw_sales.iloc[raw_idx - 7]["units_sold"]
    assert np.isclose(row_feat["sales_lag_7"], expected_lag_7)

    # rolling_mean_7 at date t must equal mean of units_sold from t-7 to t-1
    expected_rolling_mean_7 = raw_sales.iloc[raw_idx - 7 : raw_idx]["units_sold"].mean()
    assert np.isclose(row_feat["rolling_mean_7"], expected_rolling_mean_7)


def test_target_calculation(pipeline: FeaturePipeline):
    """
    Verifies that target_7d at date t strictly represents the forward sum of t+1 to t+7.
    """
    matrix = pipeline.generate_feature_matrix()

    sample_series = matrix[
        (matrix["branch_id"] == "BR001") & (matrix["medicine_id"] == "MED001")
    ].sort_values("date").reset_index(drop=True)

    raw_sales = pipeline.sales_df[
        (pipeline.sales_df["branch_id"] == "BR001") & (pipeline.sales_df["medicine_id"] == "MED001")
    ].sort_values("date").reset_index(drop=True)

    sample_date = sample_series.iloc[5]["date"]
    target_val = sample_series.iloc[5]["target_7d"]

    raw_idx = raw_sales[raw_sales["date"] == sample_date].index[0]

    # Target must be sum of sales on dates t+1 through t+7
    expected_target = raw_sales.iloc[raw_idx + 1 : raw_idx + 8]["units_sold"].sum()
    assert np.isclose(target_val, expected_target)


def test_feature_matrix_integrity_and_nulls(pipeline: FeaturePipeline):
    """
    Verifies row counts, column presence, and complete absence of NaN values.
    """
    matrix = pipeline.generate_feature_matrix()

    # 516 series * (total days - 28 warm-up days - 7 tail target days)
    total_days = pipeline.sales_df["date"].nunique()
    expected_days = total_days - 28 - 7
    assert len(matrix) == 516 * expected_days
    assert matrix.isna().sum().sum() == 0

    expected_cols = {
        "date", "branch_id", "medicine_id", "category", "location_type",
        "demand_pattern", "abc_class", "sales_lag_7", "sales_lag_14",
        "rolling_mean_7", "rolling_std_7", "is_payday_week", "target_7d"
    }
    assert expected_cols.issubset(set(matrix.columns))


def test_parquet_export_and_reload(pipeline: FeaturePipeline, tmp_path: Path):
    """Verifies Parquet persistence and reload schema consistency."""
    export_path = tmp_path / "test_matrix.parquet"
    out_file = pipeline.export(output_path=export_path)

    assert out_file.exists()
    reloaded = pd.read_parquet(out_file)
    assert len(reloaded) == len(pipeline.feature_matrix)
    assert reloaded["target_7d"].equals(pipeline.feature_matrix["target_7d"])
