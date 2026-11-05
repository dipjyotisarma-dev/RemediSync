"""Replenishment decision and inventory optimization package for RemediSync."""

from typing import Any

__all__ = ["InventoryPolicy", "ExpiryIntelligenceEngine", "OrderGenerator"]


def __getattr__(name: str) -> Any:
    """Lazy module attribute loader to prevent circular imports during CLI execution."""
    if name == "InventoryPolicy":
        from src.decision.inventory_policy import InventoryPolicy
        return InventoryPolicy
    if name == "ExpiryIntelligenceEngine":
        from src.decision.expiry_intelligence import ExpiryIntelligenceEngine
        return ExpiryIntelligenceEngine
    if name == "OrderGenerator":
        from src.decision.order_generator import OrderGenerator
        return OrderGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
