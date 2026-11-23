"""Daily sales historical time-series routes."""

from datetime import date
from fastapi import APIRouter, Depends, Query

from src.api.deps import get_repository
from src.api.schemas.sales import DailySaleItem, SalesHistoryResponse
from src.database.repository import PharmacyRepository

router = APIRouter()


@router.get("/sales/history", response_model=SalesHistoryResponse, tags=["Sales"])
def get_sales_history(
    branch_id: str = Query(..., description="Target branch identifier"),
    medicine_id: str = Query(..., description="Target medicine identifier"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days back"),
    repo: PharmacyRepository = Depends(get_repository),
) -> SalesHistoryResponse:
    """Fetch chronological sales telemetry for interactive dashboard charts."""
    sales_records = repo.get_daily_sales_series(
        branch_id=branch_id,
        medicine_id=medicine_id,
        days_back=days,
    )

    items = [
        DailySaleItem(
            date=s.date.isoformat(),
            units_sold=float(s.units_sold),
            unit_selling_price=float(s.unit_price),
            total_revenue=float(s.total_revenue),
            is_stockout_flag=bool(s.is_stockout),
        )
        for s in sales_records
    ]

    return SalesHistoryResponse(
        branch_id=branch_id,
        medicine_id=medicine_id,
        total_days=len(items),
        sales=items,
    )
