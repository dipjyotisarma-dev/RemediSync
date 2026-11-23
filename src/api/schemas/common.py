"""Common Pydantic v2 schemas and response envelopes for RemediSync API."""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Uniform error representation adhering to API specifications."""

    code: str = Field(..., description="Machine-readable error classification code")
    message: str = Field(..., description="Human-readable error description")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of error event",
    )
    correlation_id: str = Field(..., description="Unique request tracing correlation ID")


class ErrorResponse(BaseModel):
    """Uniform error envelope returned on 4xx/5xx responses."""

    success: bool = Field(default=False, description="Always false for error envelopes")
    error: ErrorDetail


class SuccessEnvelope(BaseModel):
    """Generic success envelope for acknowledgment operations."""

    success: bool = Field(default=True, description="Indicates operation success")
    message: Optional[str] = Field(default=None, description="Optional success message")
