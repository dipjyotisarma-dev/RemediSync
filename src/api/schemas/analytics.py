"""Pydantic v2 schemas for executive and network analytics endpoints."""

from pydantic import BaseModel, Field


class AnalyticsOverviewResponse(BaseModel):
    """Consolidated business and supply chain KPIs across branches or single store."""

    network_daily_revenue_inr: float = Field(..., description="Average daily gross revenue in INR")
    target_daily_revenue_inr: float = Field(..., description="Target daily revenue in INR")
    performance_ratio: float = Field(..., description="Actual revenue / target revenue ratio")
    network_stockout_rate: float = Field(..., description="Fraction of SKU-days resulting in stockout")
    active_branches_count: int = Field(..., description="Number of operational branches in scope")
    total_skus_tracked: int = Field(..., description="Distinct active medicines tracked")
    critical_stockouts_count: int = Field(..., description="Number of SKUs currently at zero or critical stock")
    near_expiry_batches_count: int = Field(..., description="Number of lots expiring within statutory return window")
    estimated_near_expiry_value_inr: float = Field(..., description="Total capital at risk of expiration write-off")
