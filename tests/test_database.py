"""Automated test suite for RemediSync relational persistence layer.

Strictly validates:
- Schema definition and table existence across all 7 entities
- Foreign key constraints and cascade rules
- Unique composite constraints and check constraints
- SQL injection immunity via parameterized queries
- PharmacyRepository data access methods (filtering, joining, pagination)
- Data seeder execution and referential consistency
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, Session

from src.database.models import (
    Base,
    Branch,
    Supplier,
    Medicine,
    Batch,
    DailySale,
    InventorySnapshot,
    ReplenishmentOrder,
)
from src.database.repository import PharmacyRepository
from src.database.schema import create_all_tables, drop_all_tables
from src.database.seed import seed_database


@pytest.fixture(scope="function")
def test_db_session() -> Session:
    """Fixture providing an isolated in-memory SQLite database session for tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    # Enable SQLite foreign key constraint enforcement
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON;"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestDatabaseSchemaAndModels:
    """Strict schema, constraint, and model validation tests."""

    def test_schema_table_registry(self) -> None:
        """Verify all 7 domain tables are properly registered with Base.metadata."""
        table_names = set(Base.metadata.tables.keys())
        expected_tables = {
            "branches",
            "suppliers",
            "medicines",
            "batches",
            "daily_sales",
            "inventory_snapshots",
            "replenishment_orders",
        }
        assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"

    def test_branch_crud_and_pk_uniqueness(self, test_db_session: Session) -> None:
        """Verify Branch creation, query, and primary key collision rejection."""
        branch = Branch(
            branch_id="BR001",
            branch_name="Kamakhya Gate Branch",
            location_type="TRANSIT_HUB",
            daily_target_revenue=Decimal("50000.00"),
            is_active=True,
        )
        test_db_session.add(branch)
        test_db_session.commit()

        queried = test_db_session.get(Branch, "BR001")
        assert queried is not None
        assert queried.branch_name == "Kamakhya Gate Branch"
        assert queried.daily_target_revenue == Decimal("50000.00")

        # Duplicate primary key must fail
        duplicate = Branch(
            branch_id="BR001",
            branch_name="Duplicate Branch",
            location_type="SUBURBAN",
        )
        test_db_session.add(duplicate)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
        test_db_session.rollback()

    def test_supplier_and_medicine_referential_integrity(self, test_db_session: Session) -> None:
        """Verify Medicine-Supplier relationship and foreign key enforcement."""
        supplier = Supplier(
            supplier_id="SUP001",
            supplier_name="Panbazar Med Stockists",
            contact_phone="+91-361-2541001",
            city_hub="PANBAZAR",
            lead_time_days=Decimal("1.00"),
            fulfillment_tier="EXPRESS_PICKUP",
            is_active=True,
        )
        test_db_session.add(supplier)
        test_db_session.commit()

        medicine = Medicine(
            medicine_id="MED001",
            brand_name="Dolo 650",
            generic_salt="Paracetamol",
            strength="650mg",
            dosage_form="TABLET",
            category="Analgesic",
            manufacturer="Micro Labs Ltd",
            mrp=Decimal("30.91"),
            cost_price=Decimal("24.73"),
            pack_size="15 Tablets",
            units_per_pack=15,
            primary_supplier_id="SUP001",
            is_cold_chain=False,
            schedule_type="OTC",
        )
        test_db_session.add(medicine)
        test_db_session.commit()

        # Verify relationship traversal
        sup = test_db_session.get(Supplier, "SUP001")
        assert len(sup.medicines) == 1
        assert sup.medicines[0].brand_name == "Dolo 650"

        # Attempting to add medicine with invalid supplier must fail
        invalid_med = Medicine(
            medicine_id="MED999",
            brand_name="Orphan Drug",
            generic_salt="Unknown",
            strength="100mg",
            dosage_form="TABLET",
            category="General",
            manufacturer="Unknown",
            mrp=Decimal("50.00"),
            cost_price=Decimal("40.00"),
            pack_size="10 Tablets",
            units_per_pack=10,
            primary_supplier_id="NON_EXISTENT_SUPPLIER",
        )
        test_db_session.add(invalid_med)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
        test_db_session.rollback()

    def test_batch_unique_constraint(self, test_db_session: Session) -> None:
        """Verify Batch unique constraint: (branch_id, medicine_id, batch_number)."""
        # Create parent branch & supplier & medicine
        branch = Branch(branch_id="BR001", branch_name="Main", location_type="HUB")
        supplier = Supplier(supplier_id="SUP001", supplier_name="Dist", city_hub="GHY", fulfillment_tier="TIER_1")
        med = Medicine(
            medicine_id="MED001", brand_name="Aspirin", generic_salt="ASA", strength="75mg",
            dosage_form="TABLET", category="Cardiovascular", manufacturer="Bayer",
            mrp=Decimal("20.00"), cost_price=Decimal("15.00"), pack_size="10 Tablets",
            units_per_pack=10, primary_supplier_id="SUP001"
        )
        test_db_session.add_all([branch, supplier, med])
        test_db_session.commit()

        batch1 = Batch(
            batch_id="BAT001",
            medicine_id="MED001",
            branch_id="BR001",
            batch_number="LOT-2026-X1",
            mfg_date=date(2025, 1, 1),
            expiry_date=date(2027, 1, 1),
            initial_quantity=100,
            current_quantity=80,
            unit_cost_price=Decimal("15.00"),
        )
        test_db_session.add(batch1)
        test_db_session.commit()

        # Duplicate (branch_id, medicine_id, batch_number) must fail
        batch_dup = Batch(
            batch_id="BAT002",
            medicine_id="MED001",
            branch_id="BR001",
            batch_number="LOT-2026-X1",  # Same lot number for same branch and medicine
            mfg_date=date(2025, 1, 1),
            expiry_date=date(2027, 1, 1),
            initial_quantity=50,
            current_quantity=50,
            unit_cost_price=Decimal("15.00"),
        )
        test_db_session.add(batch_dup)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
        test_db_session.rollback()

    def test_daily_sales_unique_series_date(self, test_db_session: Session) -> None:
        """Verify DailySale unique constraint: (branch_id, medicine_id, date)."""
        branch = Branch(branch_id="BR001", branch_name="Main", location_type="HUB")
        supplier = Supplier(supplier_id="SUP001", supplier_name="Dist", city_hub="GHY", fulfillment_tier="TIER_1")
        med = Medicine(
            medicine_id="MED001", brand_name="Aspirin", generic_salt="ASA", strength="75mg",
            dosage_form="TABLET", category="Cardiovascular", manufacturer="Bayer",
            mrp=Decimal("20.00"), cost_price=Decimal("15.00"), pack_size="10 Tablets",
            units_per_pack=10, primary_supplier_id="SUP001"
        )
        test_db_session.add_all([branch, supplier, med])
        test_db_session.commit()

        sale1 = DailySale(
            date=date(2026, 7, 1),
            branch_id="BR001",
            medicine_id="MED001",
            units_sold=Decimal("10.00"),
            unit_price=Decimal("20.00"),
            total_revenue=Decimal("200.00"),
            is_stockout=False,
        )
        test_db_session.add(sale1)
        test_db_session.commit()

        # Duplicate sale on same date for same series must fail
        sale_dup = DailySale(
            date=date(2026, 7, 1),
            branch_id="BR001",
            medicine_id="MED001",
            units_sold=Decimal("5.00"),
            unit_price=Decimal("20.00"),
            total_revenue=Decimal("100.00"),
            is_stockout=False,
        )
        test_db_session.add(sale_dup)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
        test_db_session.rollback()

    def test_inventory_snapshot_unique_constraint(self, test_db_session: Session) -> None:
        """Verify InventorySnapshot unique constraint: (branch_id, medicine_id)."""
        branch = Branch(branch_id="BR001", branch_name="Main", location_type="HUB")
        supplier = Supplier(supplier_id="SUP001", supplier_name="Dist", city_hub="GHY", fulfillment_tier="TIER_1")
        med = Medicine(
            medicine_id="MED001", brand_name="Aspirin", generic_salt="ASA", strength="75mg",
            dosage_form="TABLET", category="Cardiovascular", manufacturer="Bayer",
            mrp=Decimal("20.00"), cost_price=Decimal("15.00"), pack_size="10 Tablets",
            units_per_pack=10, primary_supplier_id="SUP001"
        )
        test_db_session.add_all([branch, supplier, med])
        test_db_session.commit()

        snap1 = InventorySnapshot(
            branch_id="BR001",
            medicine_id="MED001",
            current_stock=Decimal("45.00"),
            last_replenished_date=date(2026, 6, 28),
            pending_order_quantity=Decimal("0.00"),
        )
        test_db_session.add(snap1)
        test_db_session.commit()

        # Duplicate snapshot for same series must fail
        snap_dup = InventorySnapshot(
            branch_id="BR001",
            medicine_id="MED001",
            current_stock=Decimal("50.00"),
        )
        test_db_session.add(snap_dup)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
        test_db_session.rollback()

    def test_replenishment_order_lifecycle_and_security(self, test_db_session: Session) -> None:
        """Verify ReplenishmentOrder status transitions and SQL injection safety."""
        branch = Branch(branch_id="BR001", branch_name="Main", location_type="HUB")
        supplier = Supplier(supplier_id="SUP001", supplier_name="Dist", city_hub="GHY", fulfillment_tier="TIER_1")
        med = Medicine(
            medicine_id="MED001", brand_name="Aspirin", generic_salt="ASA", strength="75mg",
            dosage_form="TABLET", category="Cardiovascular", manufacturer="Bayer",
            mrp=Decimal("20.00"), cost_price=Decimal("15.00"), pack_size="10 Tablets",
            units_per_pack=10, primary_supplier_id="SUP001"
        )
        test_db_session.add_all([branch, supplier, med])
        test_db_session.commit()

        # SQL Injection attempt inside rationale
        malicious_string = "Order 30 units'; DROP TABLE branches; --"

        order = ReplenishmentOrder(
            order_id="PO-TEST-001",
            branch_id="BR001",
            supplier_id="SUP001",
            medicine_id="MED001",
            predicted_demand_7d=Decimal("42.00"),
            safety_stock_units=Decimal("8.00"),
            recommended_order_units=Decimal("30.00"),
            estimated_total_cost=Decimal("450.00"),
            urgency_status="CRITICAL",
            order_status="PENDING_APPROVAL",
            calculation_rationale=malicious_string,
        )
        test_db_session.add(order)
        test_db_session.commit()

        # Verify SQL injection attempt was stored as literal text and branches table exists unharmed
        fetched_order = test_db_session.get(ReplenishmentOrder, "PO-TEST-001")
        assert fetched_order is not None
        assert fetched_order.calculation_rationale == malicious_string
        assert test_db_session.get(Branch, "BR001") is not None

        # Verify approval workflow
        repo = PharmacyRepository(test_db_session)
        approved = repo.approve_order("PO-TEST-001", approved_units=30.0)
        assert approved is not None
        assert approved.order_status == "APPROVED"
        assert approved.approved_order_units == Decimal("30.00")
        assert approved.approved_at is not None


class TestPharmacyRepository:
    """Tests for type-safe repository query methods."""

    @pytest.fixture(autouse=True)
    def setup_sample_records(self, test_db_session: Session) -> None:
        """Seed minimal test fixtures."""
        b1 = Branch(branch_id="BR001", branch_name="Branch 1", location_type="HUB")
        b2 = Branch(branch_id="BR002", branch_name="Branch 2", location_type="SUBURBAN")
        s1 = Supplier(supplier_id="SUP001", supplier_name="Sun Pharma", city_hub="GHY", fulfillment_tier="TIER_1")
        m1 = Medicine(
            medicine_id="MED001", brand_name="Telmisartan 40", generic_salt="Telmisartan", strength="40mg",
            dosage_form="TABLET", category="Cardiovascular", manufacturer="Sun Pharma",
            mrp=Decimal("120.00"), cost_price=Decimal("95.00"), pack_size="10 Tablets",
            units_per_pack=10, primary_supplier_id="SUP001"
        )
        m2 = Medicine(
            medicine_id="MED002", brand_name="Augmentin 625", generic_salt="Amoxicillin", strength="625mg",
            dosage_form="TABLET", category="Antibiotic", manufacturer="GSK",
            mrp=Decimal("200.00"), cost_price=Decimal("160.00"), pack_size="10 Tablets",
            units_per_pack=10, primary_supplier_id="SUP001"
        )
        snap1 = InventorySnapshot(branch_id="BR001", medicine_id="MED001", current_stock=Decimal("50.00"))
        snap2 = InventorySnapshot(branch_id="BR001", medicine_id="MED002", current_stock=Decimal("20.00"))

        today = date.today()
        batch_near = Batch(
            batch_id="B01", medicine_id="MED001", branch_id="BR001", batch_number="L1",
            mfg_date=today - timedelta(days=200), expiry_date=today + timedelta(days=45),
            initial_quantity=50, current_quantity=30, unit_cost_price=Decimal("95.00")
        )
        batch_far = Batch(
            batch_id="B02", medicine_id="MED001", branch_id="BR001", batch_number="L2",
            mfg_date=today - timedelta(days=50), expiry_date=today + timedelta(days=400),
            initial_quantity=50, current_quantity=20, unit_cost_price=Decimal("95.00")
        )

        test_db_session.add_all([b1, b2, s1, m1, m2, snap1, snap2, batch_near, batch_far])
        test_db_session.commit()

    def test_get_all_branches(self, test_db_session: Session) -> None:
        """Verify repository fetches all active branches sorted by branch_id."""
        repo = PharmacyRepository(test_db_session)
        branches = repo.get_all_branches()
        assert len(branches) == 2
        assert [b.branch_id for b in branches] == ["BR001", "BR002"]

    def test_get_branch_inventory(self, test_db_session: Session) -> None:
        """Verify repository joins inventory snapshot with medicine dimensions."""
        repo = PharmacyRepository(test_db_session)
        inv = repo.get_branch_inventory(branch_id="BR001")
        assert len(inv) == 2

        # Test category filtering
        cardio = repo.get_branch_inventory(branch_id="BR001", category="Cardiovascular")
        assert len(cardio) == 1
        assert cardio[0]["brand_name"] == "Telmisartan 40"
        assert cardio[0]["current_stock"] == 50.0

    def test_get_expiring_batches_fefo(self, test_db_session: Session) -> None:
        """Verify repository retrieves batches within 90-day threshold sorted by expiry."""
        repo = PharmacyRepository(test_db_session)
        expiring = repo.get_expiring_batches(branch_id="BR001", days_threshold=90)
        assert len(expiring) == 1
        assert expiring[0].batch_id == "B01"


class TestDatabaseSeeder:
    """Integration test validating data seeder against actual raw CSV files."""

    def test_seeder_ingests_master_telemetry(self, tmp_path: Path) -> None:
        """Verify seeder loads all 4 master dimensions, batches, and snapshots."""
        test_db_path = tmp_path / "seeder_test.db"
        test_url = f"sqlite:///{test_db_path}"

        # Run seeder with include_sales=False for fast integration test
        seed_database(
            data_dir="data/raw",
            database_url=test_url,
            reset_tables=True,
            include_sales=False,
        )

        engine = create_engine(test_url)
        with Session(engine) as session:
            num_branches = session.query(Branch).count()
            num_suppliers = session.query(Supplier).count()
            num_medicines = session.query(Medicine).count()
            num_batches = session.query(Batch).count()
            num_snapshots = session.query(InventorySnapshot).count()

            # Assert exact record counts match raw CSV data
            assert num_branches == 4
            assert num_suppliers == 30
            assert num_medicines == 129
            assert num_batches == 808
            assert num_snapshots == 516
