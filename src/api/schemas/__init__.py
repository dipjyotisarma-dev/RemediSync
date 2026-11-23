"""RemediSync API Pydantic v2 schemas package."""

from src.api.schemas.common import ErrorDetail, ErrorResponse, SuccessEnvelope
from src.api.schemas.health import HealthResponse, ModelMetadata
from src.api.schemas.analytics import AnalyticsOverviewResponse
from src.api.schemas.inventory import (
    BatchExpiryItem,
    BatchExpiryResponse,
    BranchInventoryResponse,
    InventoryItem,
)
from src.api.schemas.recommendations import (
    RecommendationItem,
    ReplenishmentRecommendationsResponse,
)
from src.api.schemas.orders import (
    OrderApproveRequest,
    OrderApproveResponse,
    OrderCreatedItem,
    OrderItemRequest,
)
from src.api.schemas.sales import DailySaleItem, SalesHistoryResponse

__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "SuccessEnvelope",
    "ModelMetadata",
    "HealthResponse",
    "AnalyticsOverviewResponse",
    "InventoryItem",
    "BranchInventoryResponse",
    "BatchExpiryItem",
    "BatchExpiryResponse",
    "RecommendationItem",
    "ReplenishmentRecommendationsResponse",
    "OrderItemRequest",
    "OrderApproveRequest",
    "OrderCreatedItem",
    "OrderApproveResponse",
    "DailySaleItem",
    "SalesHistoryResponse",
]
