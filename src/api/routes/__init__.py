"""RemediSync REST API router aggregation."""

from fastapi import APIRouter

from src.api.routes.analytics import router as analytics_router
from src.api.routes.health import router as health_router
from src.api.routes.inventory import router as inventory_router
from src.api.routes.orders import router as orders_router
from src.api.routes.recommendations import router as recommendations_router
from src.api.routes.sales import router as sales_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(analytics_router)
api_router.include_router(inventory_router)
api_router.include_router(recommendations_router)
api_router.include_router(orders_router)
api_router.include_router(sales_router)

__all__ = ["api_router"]
