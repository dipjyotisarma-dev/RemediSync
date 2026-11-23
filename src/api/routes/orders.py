"""Purchase order creation, execution, and lifecycle management routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import get_repository
from src.api.schemas.orders import (
    OrderApproveRequest,
    OrderApproveResponse,
    OrderCreatedItem,
)
from src.database.repository import PharmacyRepository

router = APIRouter()


@router.post(
    "/orders/approve",
    response_model=OrderApproveResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Orders"],
)
def approve_orders(
    request: OrderApproveRequest,
    repo: PharmacyRepository = Depends(get_repository),
) -> OrderApproveResponse:
    """Approve replenishment order items, persist immutable POs, and update pending stock."""
    branch = repo.get_branch_by_id(request.branch_id)
    if not branch:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "BRANCH_NOT_FOUND",
                "message": f"Branch '{request.branch_id}' does not exist in master records.",
            },
        )

    orders_payload = [order.model_dump() for order in request.orders]
    created = repo.approve_orders_bulk(
        branch_id=request.branch_id,
        orders_data=orders_payload,
    )

    return OrderApproveResponse(
        success=True,
        orders_created=[OrderCreatedItem(**item) for item in created],
    )
