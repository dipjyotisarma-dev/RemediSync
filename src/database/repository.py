"""Data access repository (DAO) for RemediSync backend operations.

Provides type-safe, parameterized queries for branches, suppliers, medicines,
batches, live inventory snapshots, daily sales time-series, and replenishment orders.
Immune to SQL injection by using SQLAlchemy Core and ORM parameterized expressions.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from src.database.models import (
    Batch,
    Branch,
    DailySale,
    InventorySnapshot,
    Medicine,
    ReplenishmentOrder,
    Supplier,
)


class PharmacyRepository:
    """Type-safe repository providing operational data access for RemediSync services."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with an active SQLAlchemy session.

        Args:
            db: Database session.
        """
        self.db = db

    # --------------------------------------------------------------------------
    # Master Dimensions
    # --------------------------------------------------------------------------

    def get_all_branches(self, only_active: bool = True) -> List[Branch]:
        """Fetch all registered pharmacy branches sorted by branch_id."""
        stmt = select(Branch)
        if only_active:
            stmt = stmt.where(Branch.is_active.is_(True))
        stmt = stmt.order_by(Branch.branch_id.asc())
        return list(self.db.scalars(stmt).all())

    def get_branch_by_id(self, branch_id: str) -> Optional[Branch]:
        """Retrieve a specific branch by primary key."""
        return self.db.get(Branch, branch_id)

    def get_all_suppliers(self, only_active: bool = True) -> List[Supplier]:
        """Fetch all approved medicine stockists and distributors."""
        stmt = select(Supplier)
        if only_active:
            stmt = stmt.where(Supplier.is_active.is_(True))
        stmt = stmt.order_by(Supplier.supplier_id.asc())
        return list(self.db.scalars(stmt).all())

    def get_supplier_by_id(self, supplier_id: str) -> Optional[Supplier]:
        """Retrieve a specific supplier by primary key."""
        return self.db.get(Supplier, supplier_id)

    def get_medicine_by_id(self, medicine_id: str) -> Optional[Medicine]:
        """Retrieve a medicine by primary key."""
        return self.db.get(Medicine, medicine_id)

    def get_all_medicines(
        self,
        category: Optional[str] = None,
        limit: int = 150,
        offset: int = 0,
    ) -> List[Medicine]:
        """Fetch medicines with optional category filtering and pagination."""
        stmt = select(Medicine)
        if category:
            stmt = stmt.where(Medicine.category == category)
        stmt = stmt.order_by(Medicine.medicine_id.asc()).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    # --------------------------------------------------------------------------
    # Inventory Telemetry & Batches
    # --------------------------------------------------------------------------

    def get_branch_inventory(
        self,
        branch_id: str,
        category: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Retrieve active store inventory joined with medicine catalog attributes.

        Args:
            branch_id: Target branch identifier.
            category: Optional therapeutic category filter.
            limit: Maximum rows to return.
            offset: Pagination offset.

        Returns:
            List of dictionaries containing merged inventory and SKU metadata.
        """
        stmt = (
            select(
                InventorySnapshot.branch_id,
                InventorySnapshot.medicine_id,
                InventorySnapshot.current_stock,
                InventorySnapshot.pending_order_quantity,
                InventorySnapshot.last_replenished_date,
                Medicine.brand_name,
                Medicine.generic_salt,
                Medicine.category,
                Medicine.dosage_form,
                Medicine.pack_size,
                Medicine.units_per_pack,
                Medicine.mrp,
                Medicine.cost_price,
                Medicine.primary_supplier_id,
            )
            .join(Medicine, InventorySnapshot.medicine_id == Medicine.medicine_id)
            .where(InventorySnapshot.branch_id == branch_id)
        )

        if category:
            stmt = stmt.where(Medicine.category == category)

        stmt = stmt.order_by(Medicine.brand_name.asc()).offset(offset).limit(limit)
        results = self.db.execute(stmt).all()

        inventory: List[Dict[str, Any]] = []
        for r in results:
            inventory.append({
                "branch_id": r.branch_id,
                "medicine_id": r.medicine_id,
                "brand_name": r.brand_name,
                "generic_salt": r.generic_salt,
                "category": r.category,
                "dosage_form": r.dosage_form,
                "pack_size": r.pack_size,
                "units_per_pack": int(r.units_per_pack),
                "mrp": float(r.mrp),
                "cost_price": float(r.cost_price),
                "current_stock": float(r.current_stock),
                "pending_order_quantity": float(r.pending_order_quantity),
                "last_replenished_date": r.last_replenished_date.isoformat() if r.last_replenished_date else None,
                "primary_supplier_id": r.primary_supplier_id,
            })
        return inventory

    def get_expiring_batches(
        self,
        branch_id: Optional[str] = None,
        days_threshold: int = 90,
        reference_date: Optional[date] = None,
    ) -> List[Batch]:
        """Fetch physical lots approaching statutory expiration (FEFO order).

        Args:
            branch_id: Optional branch filter.
            days_threshold: Number of days remaining until expiry (default: 90 days).
            reference_date: Reference current date (defaults to date.today()).

        Returns:
            List of Batch objects ordered by expiry_date ascending.
        """
        ref_dt = reference_date or date.today()
        cutoff_date = ref_dt + timedelta(days=days_threshold)

        stmt = (
            select(Batch)
            .where(
                Batch.current_quantity > 0,
                Batch.expiry_date <= cutoff_date,
            )
            .order_by(Batch.expiry_date.asc())
        )
        if branch_id:
            stmt = stmt.where(Batch.branch_id == branch_id)

        return list(self.db.scalars(stmt).all())

    # --------------------------------------------------------------------------
    # Replenishment Orders
    # --------------------------------------------------------------------------

    def get_pending_orders(
        self,
        branch_id: Optional[str] = None,
        urgency_status: Optional[str] = None,
    ) -> List[ReplenishmentOrder]:
        """Fetch pending purchase recommendations awaiting pharmacist approval."""
        stmt = select(ReplenishmentOrder).where(
            ReplenishmentOrder.order_status == "PENDING_APPROVAL"
        )
        if branch_id:
            stmt = stmt.where(ReplenishmentOrder.branch_id == branch_id)
        if urgency_status:
            stmt = stmt.where(ReplenishmentOrder.urgency_status == urgency_status)

        stmt = stmt.order_by(ReplenishmentOrder.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def create_replenishment_order(self, order_data: Dict[str, Any]) -> ReplenishmentOrder:
        """Persist a new replenishment order recommendation generated by the engine."""
        order = ReplenishmentOrder(
            order_id=order_data["order_id"],
            branch_id=order_data["branch_id"],
            supplier_id=order_data["supplier_id"],
            medicine_id=order_data["medicine_id"],
            predicted_demand_7d=Decimal(str(order_data["predicted_demand_7d"])),
            safety_stock_units=Decimal(str(order_data["safety_stock_units"])),
            recommended_order_units=Decimal(str(order_data["recommended_order_units"])),
            approved_order_units=Decimal(str(order_data.get("approved_order_units", order_data["recommended_order_units"])))
            if order_data.get("approved_order_units") is not None
            else None,
            estimated_total_cost=Decimal(str(order_data["estimated_total_cost"])),
            urgency_status=order_data["urgency_status"],
            order_status=order_data.get("order_status", "PENDING_APPROVAL"),
            calculation_rationale=order_data["calculation_rationale"],
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def approve_order(
        self,
        order_id: str,
        approved_units: Optional[float] = None,
    ) -> Optional[ReplenishmentOrder]:
        """Approve a pending purchase order and update approval timestamp."""
        order = self.db.get(ReplenishmentOrder, order_id)
        if not order:
            return None

        order.order_status = "APPROVED"
        order.approved_at = datetime.now(timezone.utc)
        if approved_units is not None:
            order.approved_order_units = Decimal(str(approved_units))
        elif order.approved_order_units is None:
            order.approved_order_units = order.recommended_order_units

        self.db.commit()
        self.db.refresh(order)
        return order

    # --------------------------------------------------------------------------
    # Historical Sales
    # --------------------------------------------------------------------------

    def get_daily_sales_series(
        self,
        branch_id: str,
        medicine_id: str,
        days_back: int = 30,
        end_date: Optional[date] = None,
    ) -> List[DailySale]:
        """Fetch chronological sales telemetry for a specific branch-medicine pair."""
        ref_dt = end_date or date.today()
        start_dt = ref_dt - timedelta(days=days_back)

        stmt = (
            select(DailySale)
            .where(
                DailySale.branch_id == branch_id,
                DailySale.medicine_id == medicine_id,
                DailySale.date >= start_dt,
                DailySale.date <= ref_dt,
            )
            .order_by(DailySale.date.asc())
        )
        return list(self.db.scalars(stmt).all())
