"""Pydantic v2 schemas for system health and diagnostics endpoints."""

from typing import Optional
from pydantic import BaseModel, Field


class ModelMetadata(BaseModel):
    """Metadata describing the active production machine learning forecaster."""

    name: str = Field(..., description="Name of the deployed forecasting model")
    version: str = Field(..., description="Model release version")
    trained_date: Optional[str] = Field(default=None, description="Date of training completion")
    model_type: Optional[str] = Field(default=None, description="Underlying algorithm or class")


class HealthResponse(BaseModel):
    """System health check and diagnostic telemetry."""

    status: str = Field(..., description="Operational status: HEALTHY or DEGRADED")
    version: str = Field(default="1.0.0", description="RemediSync platform version")
    uptime_seconds: float = Field(..., description="Elapsed server uptime in seconds")
    database: str = Field(..., description="Database connection state: CONNECTED or DISCONNECTED")
    active_model: ModelMetadata = Field(..., description="Active production demand forecaster")
