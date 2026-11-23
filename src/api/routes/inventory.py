"""Branch inventory telemetry and batch expiry audit routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import get_repository
from src.api.schemas.inventory import (
    BatchExpiryItem,
    BatchExpiryResponse,
    BranchInventoryResponse,
    InventoryItem,
)
from src.database.repository import PharmacyRepository

router = APIRouter()


@router.get(
    "/inventory/branches/{branch_id}",
    response_model=BranchInventoryResponse,
    tags=["Inventory"],
)
def get_branch_inventory(
    branch_id: str,
    category: Optional[str] = Query(default=None, description="Optional therapeutic category filter"),
    abc_class: Optional[str] = Query(default=None, pattern="^[ABC]$", description="Optional Pareto class filter (A, B, C)"),
    limit: int = Query(default=50, ge=1, le=200, description="Page limit"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    repo: PharmacyRepository = Depends(get_repository),
) -> BranchInventoryResponse:
    """Retrieve SKU inventory telemetry and days-of-cover intelligence for a store."""
    branch = repo.get_branch_by_id(branch_id)
    if not branch:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "BRANCH_NOT_FOUND",
                "message": f"Branch '{branch_id}' does not exist in master records.",
            },
        )

    result = repo.get_branch_inventory_with_metrics(
        branch_id=branch_id,
        category=category,
        abc_class=abc_class,
        limit=limit,
        offset=offset,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "BRANCH_NOT_FOUND",
                "message": f"Branch '{branch_id}' does not exist in master records.",
            },
        )

    total_records, items = result
    return BranchInventoryResponse(
        branch_id=branch.branch_id,
        branch_name=branch.branch_name,
        total_records=total_records,
        items=[InventoryItem(**it) for it in items],
    )


@router.get(
    "/inventory/batches/expiry-risk",
    response_model=BatchExpiryResponse,
    tags=["Inventory"],
)
@router.get(
    "/batches/expiring",
    response_model=BatchExpiryResponse,
    include_in_schema=False,
    tags=["Inventory"],
)
def get_batch_expiry_risk(
    branch_id: Optional[str] = Query(default=None, description="Optional branch identifier filter"),
    max_days_to_expiry: int = Query(default=90, ge=1, le=365, description="Days to statutory cutoff"),
    repo: PharmacyRepository = Depends(get_repository),
) -> BatchExpiryResponse:
    """Audit batches approaching statutory return windows or facing write-off loss."""
    batches_data = repo.get_expiring_batches_risk(
        branch_id=branch_id,
        max_days_to_expiry=max_days_to_expiry,
    )
    total_exposure = sum(b["projected_loss_inr"] for b in batches_data)
    return BatchExpiryResponse(
        total_at_risk_batches=len(batches_data),
        total_write_off_exposure_inr=round(total_exposure, 2),
        batches=[BatchExpiryItem(**b) for b in batches_data],
    )
