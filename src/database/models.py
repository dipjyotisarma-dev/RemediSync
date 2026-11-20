"""SQLAlchemy ORM domain models for RemediSync.

Implements all 7 enterprise entities:
1. Branch (branches)
2. Supplier (suppliers)
3. Medicine (medicines)
4. Batch (batches - FEFO lot tracking)
5. DailySale (daily_sales - time-series transaction telemetry)
6. InventorySnapshot (inventory_snapshots - active store inventory positions)
7. ReplenishmentOrder (replenishment_orders - decision engine purchase recommendations)
"""

from datetime import datetime, date, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Boolean,
    Date,
    DateTime,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
    CheckConstraint,
    BigInteger,
)
from sqlalchemy.orm import relationship
from src.database.session import Base


def _utcnow() -> datetime:
    """Helper returning timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class Branch(Base):
    """Pharmacy physical branch location and operational profile."""

    __tablename__ = "branches"

    branch_id = Column(String(16), primary_key=True)
    branch_name = Column(String(128), nullable=False)
    location_type = Column(String(64), nullable=False)
    daily_target_revenue = Column(Numeric(12, 2), nullable=False, default=50000.00)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    batches = relationship("Batch", back_populates="branch", cascade="all, delete-orphan")
    daily_sales = relationship("DailySale", back_populates="branch", cascade="all, delete-orphan")
    snapshots = relationship("InventorySnapshot", back_populates="branch", cascade="all, delete-orphan")
    orders = relationship("ReplenishmentOrder", back_populates="branch")


class Supplier(Base):
    """Pharmaceutical distributor or regional stockist."""

    __tablename__ = "suppliers"

    supplier_id = Column(String(16), primary_key=True)
    supplier_name = Column(String(128), nullable=False)
    contact_phone = Column(String(32), nullable=False, default="+91-361-2540001")
    city_hub = Column(String(64), nullable=False)
    lead_time_days = Column(Numeric(4, 2), nullable=False, default=1.00)
    fulfillment_tier = Column(String(32), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    medicines = relationship("Medicine", back_populates="supplier")
    orders = relationship("ReplenishmentOrder", back_populates="supplier")


class Medicine(Base):
    """Core pharmaceutical SKU catalog definition."""

    __tablename__ = "medicines"

    medicine_id = Column(String(16), primary_key=True)
    brand_name = Column(String(128), nullable=False)
    generic_salt = Column(String(256), nullable=False)
    strength = Column(String(64), nullable=False)
    dosage_form = Column(String(64), nullable=False)
    category = Column(String(64), nullable=False, index=True)
    manufacturer = Column(String(128), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2), nullable=False)
    pack_size = Column(String(64), nullable=False)
    units_per_pack = Column(Integer, nullable=False, default=10)
    primary_supplier_id = Column(
        String(16), ForeignKey("suppliers.supplier_id"), nullable=False, index=True
    )
    is_cold_chain = Column(Boolean, nullable=False, default=False)
    schedule_type = Column(String(16), nullable=False, default="SCHEDULE_H")
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="medicines")
    batches = relationship("Batch", back_populates="medicine")
    daily_sales = relationship("DailySale", back_populates="medicine")
    snapshots = relationship("InventorySnapshot", back_populates="medicine")
    orders = relationship("ReplenishmentOrder", back_populates="medicine")


class Batch(Base):
    """Physical manufactured lot tracked under FEFO protocol."""

    __tablename__ = "batches"

    batch_id = Column(String(32), primary_key=True)
    medicine_id = Column(String(16), ForeignKey("medicines.medicine_id"), nullable=False)
    branch_id = Column(String(16), ForeignKey("branches.branch_id"), nullable=False)
    batch_number = Column(String(64), nullable=False)
    mfg_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False, index=True)
    initial_quantity = Column(Integer, nullable=False)
    current_quantity = Column(Integer, nullable=False)
    unit_cost_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        UniqueConstraint("branch_id", "medicine_id", "batch_number", name="uq_branch_batch"),
        CheckConstraint("current_quantity >= 0", name="chk_batch_quantity_non_negative"),
        Index("idx_batches_branch_med", "branch_id", "medicine_id"),
    )

    branch = relationship("Branch", back_populates="batches")
    medicine = relationship("Medicine", back_populates="batches")


class DailySale(Base):
    """Historical customer dispensing transaction telemetry."""

    __tablename__ = "daily_sales"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    branch_id = Column(String(16), ForeignKey("branches.branch_id"), nullable=False)
    medicine_id = Column(String(16), ForeignKey("medicines.medicine_id"), nullable=False)
    units_sold = Column(Numeric(10, 2), nullable=False, default=0.00)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_revenue = Column(Numeric(12, 2), nullable=False)
    is_stockout = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("branch_id", "medicine_id", "date", name="uq_daily_sales_series_date"),
        CheckConstraint("units_sold >= 0", name="chk_units_sold_non_negative"),
        Index("idx_sales_branch_med_date", "branch_id", "medicine_id", "date"),
    )

    branch = relationship("Branch", back_populates="daily_sales")
    medicine = relationship("Medicine", back_populates="daily_sales")


class InventorySnapshot(Base):
    """Current on-hand physical stock and in-transit replenishment pipeline."""

    __tablename__ = "inventory_snapshots"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    branch_id = Column(String(16), ForeignKey("branches.branch_id"), nullable=False, index=True)
    medicine_id = Column(String(16), ForeignKey("medicines.medicine_id"), nullable=False)
    current_stock = Column(Numeric(10, 2), nullable=False, default=0.00)
    last_replenished_date = Column(Date, nullable=True)
    pending_order_quantity = Column(Numeric(10, 2), nullable=False, default=0.00)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    __table_args__ = (
        UniqueConstraint("branch_id", "medicine_id", name="uq_snapshot_branch_med"),
        CheckConstraint("current_stock >= 0", name="chk_current_stock_non_negative"),
    )

    branch = relationship("Branch", back_populates="snapshots")
    medicine = relationship("Medicine", back_populates="snapshots")


class ReplenishmentOrder(Base):
    """Operational purchase recommendation generated by decision engine."""

    __tablename__ = "replenishment_orders"

    order_id = Column(String(32), primary_key=True)
    branch_id = Column(String(16), ForeignKey("branches.branch_id"), nullable=False, index=True)
    supplier_id = Column(String(16), ForeignKey("suppliers.supplier_id"), nullable=False)
    medicine_id = Column(String(16), ForeignKey("medicines.medicine_id"), nullable=False)
    predicted_demand_7d = Column(Numeric(10, 2), nullable=False)
    safety_stock_units = Column(Numeric(10, 2), nullable=False)
    recommended_order_units = Column(Numeric(10, 2), nullable=False)
    approved_order_units = Column(Numeric(10, 2), nullable=True)
    estimated_total_cost = Column(Numeric(12, 2), nullable=False)
    urgency_status = Column(String(16), nullable=False)  # CRITICAL, REORDER, HEALTHY, OVERSTOCKED
    order_status = Column(
        String(16), nullable=False, default="PENDING_APPROVAL"
    )  # PENDING_APPROVAL, APPROVED, DISPATCHED, REJECTED
    calculation_rationale = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_orders_status_urgency", "order_status", "urgency_status"),
        Index("idx_orders_branch_created", "branch_id", "created_at"),
        CheckConstraint(
            "urgency_status IN ('CRITICAL', 'REORDER', 'HEALTHY', 'OVERSTOCKED')",
            name="chk_order_urgency_status",
        ),
        CheckConstraint(
            "order_status IN ('PENDING_APPROVAL', 'APPROVED', 'DISPATCHED', 'REJECTED')",
            name="chk_order_status",
        ),
    )

    branch = relationship("Branch", back_populates="orders")
    supplier = relationship("Supplier", back_populates="orders")
    medicine = relationship("Medicine", back_populates="orders")
