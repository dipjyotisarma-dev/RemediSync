"""Pydantic v2 schemas for historical daily sales time-series telemetry."""

from typing import List
from pydantic import BaseModel, Field


class DailySaleItem(BaseModel):
    """Daily sales telemetry record for a specific SKU."""

    date: str = Field(..., description="Date of sales transactions (YYYY-MM-DD)")
    units_sold: float = Field(..., description="Quantity of units sold")
    unit_selling_price: float = Field(..., description="Selling price per unit in INR")
    total_revenue: float = Field(..., description="Total gross sales revenue in INR")
    is_stockout_flag: bool = Field(..., description="True if store experienced zero inventory on this day")


class SalesHistoryResponse(BaseModel):
    """Chronological sales history for chart visualizer."""

    branch_id: str = Field(..., description="Branch code")
    medicine_id: str = Field(..., description="Medicine code")
    total_days: int = Field(..., description="Number of daily records returned")
    sales: List[DailySaleItem] = Field(..., description="Ordered list of daily sales records")
