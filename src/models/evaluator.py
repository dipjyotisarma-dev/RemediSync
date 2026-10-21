"""Evaluation subsystem for retail pharmacy inventory demand models.

Provides standardized quantitative error metrics and stratified slice analytics
for evaluating demand forecasts against actual customer consumption over multi-day horizons.
"""

from typing import Any, Dict, Sequence, Union
import numpy as np
import pandas as pd


class ForecastEvaluator:
    """Quantitative evaluation engine implementing retail supply chain error contracts."""

    @staticmethod
    def _validate_inputs(
        y_true: Union[np.ndarray, pd.Series, Sequence[float]],
        y_pred: Union[np.ndarray, pd.Series, Sequence[float]],
    ) -> tuple[np.ndarray, np.ndarray]:
        """Convert and validate truth and prediction vectors.

        Args:
            y_true: Ground truth observed demand values.
            y_pred: Model forecasted demand values.

        Returns:
            Tuple of validated 1D float64 numpy arrays (y_true, y_pred).

        Raises:
            ValueError: If input dimensions mismatch or contain invalid NaN values.
        """
        arr_true = np.asarray(y_true, dtype=np.float64).ravel()
        arr_pred = np.asarray(y_pred, dtype=np.float64).ravel()

        if arr_true.shape != arr_pred.shape:
            raise ValueError(
                f"Dimension mismatch: y_true has shape {arr_true.shape}, "
                f"but y_pred has shape {arr_pred.shape}."
            )
        if len(arr_true) == 0:
            raise ValueError("Input arrays must not be empty.")
        if np.isnan(arr_true).any() or np.isnan(arr_pred).any():
            raise ValueError("Input arrays must not contain NaN values.")

        return arr_true, arr_pred

    @classmethod
    def compute_wape(
        cls,
        y_true: Union[np.ndarray, pd.Series, Sequence[float]],
        y_pred: Union[np.ndarray, pd.Series, Sequence[float]],
    ) -> float:
        """Calculate Weighted Absolute Percentage Error (WAPE).

        WAPE = sum(|y - y_hat|) / sum(y)

        Args:
            y_true: Ground truth observed demand.
            y_pred: Predicted demand.

        Returns:
            WAPE as a floating point ratio (e.g., 0.15 represents 15% error).
        """
        arr_true, arr_pred = cls._validate_inputs(y_true, y_pred)
        total_actual = float(np.sum(arr_true))
        total_error = float(np.sum(np.abs(arr_true - arr_pred)))

        if total_actual == 0.0:
            return 0.0 if total_error == 0.0 else float("inf")

        return total_error / total_actual

    @classmethod
    def compute_mae(
        cls,
        y_true: Union[np.ndarray, pd.Series, Sequence[float]],
        y_pred: Union[np.ndarray, pd.Series, Sequence[float]],
    ) -> float:
        """Calculate Mean Absolute Error (MAE).

        MAE = mean(|y - y_hat|)

        Args:
            y_true: Ground truth observed demand.
            y_pred: Predicted demand.

        Returns:
            Mean absolute unit error.
        """
        arr_true, arr_pred = cls._validate_inputs(y_true, y_pred)
        return float(np.mean(np.abs(arr_true - arr_pred)))

    @classmethod
    def compute_rmse(
        cls,
        y_true: Union[np.ndarray, pd.Series, Sequence[float]],
        y_pred: Union[np.ndarray, pd.Series, Sequence[float]],
    ) -> float:
        """Calculate Root Mean Squared Error (RMSE).

        RMSE = sqrt(mean((y - y_hat)^2))

        Args:
            y_true: Ground truth observed demand.
            y_pred: Predicted demand.

        Returns:
            Root mean squared unit error.
        """
        arr_true, arr_pred = cls._validate_inputs(y_true, y_pred)
        return float(np.sqrt(np.mean((arr_true - arr_pred) ** 2)))

    @classmethod
    def compute_bias(
        cls,
        y_true: Union[np.ndarray, pd.Series, Sequence[float]],
        y_pred: Union[np.ndarray, pd.Series, Sequence[float]],
    ) -> float:
        """Calculate Aggregate Percentage Bias (Tracking Signal).

        Bias = sum(y_hat - y) / sum(y)

        Args:
            y_true: Ground truth observed demand.
            y_pred: Predicted demand.

        Returns:
            Aggregate bias ratio (> 0 over-forecasting, < 0 under-forecasting).
        """
        arr_true, arr_pred = cls._validate_inputs(y_true, y_pred)
        total_actual = float(np.sum(arr_true))
        total_diff = float(np.sum(arr_pred - arr_true))

        if total_actual == 0.0:
            return 0.0 if total_diff == 0.0 else float("inf")

        return total_diff / total_actual

    @classmethod
    def evaluate_all(
        cls,
        y_true: Union[np.ndarray, pd.Series, Sequence[float]],
        y_pred: Union[np.ndarray, pd.Series, Sequence[float]],
    ) -> Dict[str, float]:
        """Compute standard retail inventory forecasting metric suite.

        Args:
            y_true: Ground truth observed demand.
            y_pred: Predicted demand.

        Returns:
            Dictionary containing wape, mae, rmse, bias, and total_volume.
        """
        arr_true, arr_pred = cls._validate_inputs(y_true, y_pred)
        return {
            "wape": cls.compute_wape(arr_true, arr_pred),
            "mae": cls.compute_mae(arr_true, arr_pred),
            "rmse": cls.compute_rmse(arr_true, arr_pred),
            "bias": cls.compute_bias(arr_true, arr_pred),
            "total_actual": float(np.sum(arr_true)),
            "total_predicted": float(np.sum(arr_pred)),
            "sample_size": int(len(arr_true)),
        }

    @classmethod
    def evaluate_stratified(
        cls,
        df: pd.DataFrame,
        y_true_col: str,
        y_pred_col: str,
        group_col: str,
    ) -> pd.DataFrame:
        """Evaluate forecasting metrics across categorical business strata.

        Args:
            df: DataFrame containing truth, predictions, and grouping attribute.
            y_true_col: Column name of actual observed demand.
            y_pred_col: Column name of predicted demand.
            group_col: Column name to segment by (e.g., 'abc_class', 'demand_pattern').

        Returns:
            Summary DataFrame indexed by stratum with metrics as columns.
        """
        records: list[Dict[str, Any]] = []

        for group_val, group_data in df.groupby(group_col, observed=True):
            if group_data.empty:
                continue

            metrics = cls.evaluate_all(
                group_data[y_true_col], group_data[y_pred_col]
            )
            records.append({group_col: group_val, **metrics})

        result_df = pd.DataFrame(records)
        if not result_df.empty:
            result_df = result_df.set_index(group_col)

        return result_df
