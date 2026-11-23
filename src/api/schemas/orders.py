"""Pydantic v2 schemas for purchase order execution, approval, and lifecycle."""

from typing import List, Optional
from pydantic import BaseModel, Field


class OrderItemRequest(BaseModel):
    """Payload representing a single purchase item approved by a pharmacist."""

    medicine_id: str = Field(..., description="Medicine identifier")
    supplier_id: str = Field(..., description="Fulfilling supplier identifier")
    approved_quantity_units: float = Field(
        ..., gt=0.0, description="Authorized replenishment quantity in units (must be > 0)"
    )
    notes: Optional[str] = Field(default=None, description="Optional pharmacist clinical or logistics notes")


class OrderApproveRequest(BaseModel):
    """Batch purchase order approval request submitted by a pharmacist."""

    branch_id: str = Field(..., description="Target branch identifier")
    orders: List[OrderItemRequest] = Field(
        ..., min_length=1, description="List of individual approved purchase order line items"
    )


class OrderCreatedItem(BaseModel):
    """Summary of an approved purchase order record created in the system."""

    order_id: str = Field(..., description="Immutable generated Purchase Order number")
    medicine_id: str = Field(..., description="Target medicine identifier")
    approved_units: float = Field(..., description="Approved order quantity in units")
    estimated_cost_inr: float = Field(..., description="Total estimated cost in INR")
    status: str = Field(default="APPROVED", description="Lifecycle status: APPROVED")
    created_at: str = Field(..., description="UTC ISO timestamp of PO generation")


class OrderApproveResponse(BaseModel):
    """Response returned upon successful creation and approval of purchase orders."""

    success: bool = Field(default=True, description="Indicates approval transaction success")
    orders_created: List[OrderCreatedItem] = Field(..., description="Created PO records")
