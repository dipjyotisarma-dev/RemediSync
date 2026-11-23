"""Health and system diagnostics routes."""

from datetime import datetime, timezone
import time
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.schemas.health import HealthResponse, ModelMetadata
from src.database.session import get_db

router = APIRouter()
START_TIME = time.time()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Return operational liveness, database connectivity, and active ML model telemetry."""
    # Test database connectivity
    db_status = "CONNECTED"
    try:
        db.execute(text("SELECT 1;"))
    except Exception:
        db_status = "DISCONNECTED"

    overall_status = "HEALTHY" if db_status == "CONNECTED" else "DEGRADED"
    uptime = round(time.time() - START_TIME, 1)

    model_meta = ModelMetadata(
        name="HistGradientBoostingForecaster",
        version="v1.2.0",
        trained_date="2026-10-03",
        model_type="HistGradientBoostingRegressor",
    )

    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        uptime_seconds=uptime,
        database=db_status,
        active_model=model_meta,
    )
