"""Replenishment order recommendation routes."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import get_repository
from src.api.schemas.recommendations import (
    RecommendationItem,
    ReplenishmentRecommendationsResponse,
)
from src.database.repository import PharmacyRepository

router = APIRouter()


@router.get(
    "/recommendations/replenish",
    response_model=ReplenishmentRecommendationsResponse,
    tags=["Recommendations"],
)
def get_replenishment_recommendations(
    branch_id: str = Query(..., description="Target branch identifier (required)"),
    urgency: Optional[str] = Query(
        default=None,
        description="Filter by urgency tier (CRITICAL, REORDER, HEALTHY, OVERSTOCKED)",
    ),
    supplier_id: Optional[str] = Query(default=None, description="Filter by supplier identifier"),
    repo: PharmacyRepository = Depends(get_repository),
) -> ReplenishmentRecommendationsResponse:
    """Generate prioritized replenishment recommendations for store pharmacist review."""
    branch = repo.get_branch_by_id(branch_id)
    if not branch:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "BRANCH_NOT_FOUND",
                "message": f"Branch '{branch_id}' does not exist in master records.",
            },
        )

    recs_data = repo.get_replenishment_recommendations(
        branch_id=branch_id,
        urgency=urgency,
        supplier_id=supplier_id,
    )

    total_cost = sum(r["estimated_cost_inr"] for r in recs_data)
    now_utc = datetime.now(timezone.utc).isoformat()

    return ReplenishmentRecommendationsResponse(
        branch_id=branch_id,
        generated_at=now_utc,
        total_recommended_orders=len(recs_data),
        total_estimated_expenditure_inr=round(total_cost, 2),
        recommendations=[RecommendationItem(**r) for r in recs_data],
    )
