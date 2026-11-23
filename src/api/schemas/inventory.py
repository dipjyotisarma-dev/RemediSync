"""Pydantic v2 schemas for branch inventory telemetry and batch expiry audits."""

from typing import List, Optional
from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    """Enriched telemetry for a single SKU at a store location."""

    medicine_id: str = Field(..., description="Unique medicine identifier")
    brand_name: str = Field(..., description="Commercial brand name")
    generic_salt: str = Field(..., description="Active pharmaceutical ingredient")
    category: str = Field(..., description="Therapeutic category")
    dosage_form: str = Field(..., description="Formulation form (e.g. TABLET, SYRUP)")
    current_stock_units: float = Field(..., description="Physical units on hand")
    pending_order_units: float = Field(default=0.0, description="Units in transit or pending dispatch")
    predicted_7d_demand: float = Field(..., description="Forward 7-day cumulative forecasted demand")
    days_of_cover: float = Field(..., description="Current stock divided by daily demand velocity")
    reorder_point: float = Field(..., description="Dynamic statistical reorder point (ROP)")
    is_below_rop: bool = Field(..., description="Flag indicating if stock position requires replenishment")
    abc_class: str = Field(default="B", description="Pareto revenue classification (A, B, C)")
    demand_pattern: str = Field(default="Smooth", description="Croston demand classification (Smooth, Intermittent)")


class BranchInventoryResponse(BaseModel):
    """Paginated inventory catalog for a specific pharmacy branch."""

    branch_id: str = Field(..., description="Branch unique code")
    branch_name: str = Field(..., description="Branch commercial name")
    total_records: int = Field(..., description="Total items matching filter criteria")
    items: List[InventoryItem] = Field(..., description="List of SKU inventory items")


class BatchExpiryItem(BaseModel):
    """Physical batch lot approaching expiration or at risk of financial waste."""

    batch_id: str = Field(..., description="Batch system identifier")
    branch_id: str = Field(..., description="Store location identifier")
    medicine_id: str = Field(..., description="Medicine identifier")
    brand_name: str = Field(..., description="Medicine brand name")
    batch_number: str = Field(..., description="Manufacturer batch/lot code")
    expiry_date: str = Field(..., description="Batch expiration date (YYYY-MM-DD)")
    days_to_expiry: int = Field(..., description="Calendar days remaining until expiration")
    current_quantity_units: float = Field(..., description="Physical units remaining in batch")
    predicted_demand_before_expiry: float = Field(..., description="Forecasted demand before expiration")
    projected_unsold_units: float = Field(..., description="Estimated surplus units that will expire unsold")
    projected_loss_inr: float = Field(..., description="Potential cost-price write-off exposure")
    recommended_action: str = Field(..., description="Recommended mitigation protocol")
    action_rationale: str = Field(..., description="Pharmacist justification explaining the recommendation")


class BatchExpiryResponse(BaseModel):
    """Audit report of all expiring batches across the pharmacy network or branch."""

    total_at_risk_batches: int = Field(..., description="Count of lots flagged with expiry or write-off risk")
    total_write_off_exposure_inr: float = Field(..., description="Consolidated capital exposure in INR")
    batches: List[BatchExpiryItem] = Field(..., description="List of lot-level audit items")
