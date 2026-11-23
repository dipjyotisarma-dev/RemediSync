"""Executive and network-level analytics routes."""

from typing import Optional
from fastapi import APIRouter, Depends, Query

from src.api.deps import get_repository
from src.api.schemas.analytics import AnalyticsOverviewResponse
from src.database.repository import PharmacyRepository

router = APIRouter()


@router.get("/analytics/overview", response_model=AnalyticsOverviewResponse, tags=["Analytics"])
def get_analytics_overview(
    branch_id: Optional[str] = Query(default=None, description="Optional branch identifier filter"),
    days: int = Query(default=30, ge=1, le=365, description="Number of historical days to aggregate"),
    repo: PharmacyRepository = Depends(get_repository),
) -> AnalyticsOverviewResponse:
    """Consolidated business and replenishment KPIs for the pharmacy chain or branch."""
    data = repo.get_analytics_overview(branch_id=branch_id, days=days)
    return AnalyticsOverviewResponse(**data)
