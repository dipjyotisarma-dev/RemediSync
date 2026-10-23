"""Demand forecasting, evaluation, and diagnostic package for RemediSync."""

from typing import Any

__all__ = [
    "BaselineForecaster",
    "ForecastEvaluator",
    "DemandForecaster",
    "ModelDiagnostics",
]


def __getattr__(name: str) -> Any:
    """Lazy module attribute loader to prevent circular imports during CLI execution."""
    if name == "BaselineForecaster":
        from src.models.baseline import BaselineForecaster
        return BaselineForecaster
    if name == "ForecastEvaluator":
        from src.models.evaluator import ForecastEvaluator
        return ForecastEvaluator
    if name == "DemandForecaster":
        from src.models.forecaster import DemandForecaster
        return DemandForecaster
    if name == "ModelDiagnostics":
        from src.models.diagnostics import ModelDiagnostics
        return ModelDiagnostics
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
