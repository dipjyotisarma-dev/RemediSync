"""Pydantic v2 schemas for purchase order recommendations."""

from typing import List
from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    """Detailed replenishment purchase recommendation for a single SKU."""

    medicine_id: str = Field(..., description="Medicine identifier")
    brand_name: str = Field(..., description="Brand name")
    primary_supplier_id: str = Field(..., description="Primary authorized distributor ID")
    primary_supplier_name: str = Field(..., description="Distributor legal name")
    supplier_fulfillment_tier: str = Field(default="STANDARD", description="Supplier logistics tier")
    lead_time_days: float = Field(..., description="Expected replenishment lead time in days")
    current_stock_units: float = Field(..., description="Current stock position")
    pending_order_units: float = Field(default=0.0, description="Existing pending orders")
    predicted_7d_demand: float = Field(..., description="7-day demand forecast")
    safety_stock_units: float = Field(..., description="Dynamic safety stock buffer")
    reorder_point: float = Field(..., description="Calculated statistical reorder point")
    recommended_order_units: float = Field(..., description="Recommended reorder quantity in units")
    unit_cost_price: float = Field(..., description="Cost price per unit")
    estimated_cost_inr: float = Field(..., description="Total purchase order value in INR")
    pack_size_rounding: str = Field(..., description="Packaging adjustment explanation")
    urgency: str = Field(..., description="Urgency classification: CRITICAL, REORDER, HEALTHY, OVERSTOCKED")
    calculation_rationale: str = Field(..., description="Plain-English explanation for pharmacist audit")


class ReplenishmentRecommendationsResponse(BaseModel):
    """Consolidated purchase order recommendations for a pharmacy branch."""

    branch_id: str = Field(..., description="Branch identifier")
    generated_at: str = Field(..., description="Timestamp of recommendation generation")
    total_recommended_orders: int = Field(..., description="Count of items recommended for reorder")
    total_estimated_expenditure_inr: float = Field(..., description="Total purchase cost across all items")
    recommendations: List[RecommendationItem] = Field(..., description="List of SKU recommendations")
