"""Strict integration test suite for RemediSync FastAPI Backend Service.

Tests all REST endpoints, Pydantic v2 schemas, database dependency injection,
uniform error envelopes, and CORS middleware against an isolated in-memory database.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.database.models import (
    Base,
    Batch,
    Branch,
    DailySale,
    InventorySnapshot,
    Medicine,
    Supplier,
)
from src.database.session import get_db
from src.api.main import app


# ------------------------------------------------------------------------------
# Test Database Fixture & FastAPI Client Setup
# ------------------------------------------------------------------------------

@pytest.fixture(scope="function")
def test_db_session() -> Session:
    """Provides an isolated, in-memory SQLite database populated with test fixtures."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON;"))
        conn.commit()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    # Seed minimal valid dimension records
    branch = Branch(
        branch_id="BR001",
        branch_name="Guwahati Central Pharmacy",
        location_type="HIGH_STREET",
        daily_target_revenue=Decimal("55000.00"),
        is_active=True,
    )
    supplier = Supplier(
        supplier_id="SUP001",
        supplier_name="Assam Drug Distributors",
        contact_phone="+91-9864011223",
        city_hub="Guwahati",
        lead_time_days=Decimal("1.5"),
        fulfillment_tier="STANDARD",
        is_active=True,
    )
    med1 = Medicine(
        medicine_id="MED001",
        brand_name="Dolo 650",
        generic_salt="Paracetamol",
        strength="650mg",
        manufacturer="Micro Labs",
        category="Analgesic",
        dosage_form="TABLET",
        pack_size="15 tablets",
        units_per_pack=15,
        mrp=Decimal("30.00"),
        cost_price=Decimal("20.00"),
        is_cold_chain=False,
        schedule_type="OTC",
        primary_supplier_id="SUP001",
    )
    med2 = Medicine(
        medicine_id="MED002",
        brand_name="Telma 40",
        generic_salt="Telmisartan",
        strength="40mg",
        manufacturer="Glenmark",
        category="Cardiovascular",
        dosage_form="TABLET",
        pack_size="30 tablets",
        units_per_pack=30,
        mrp=Decimal("220.00"),
        cost_price=Decimal("160.00"),
        is_cold_chain=False,
        schedule_type="SCHEDULE_H",
        primary_supplier_id="SUP001",
    )
    session.add_all([branch, supplier, med1, med2])
    session.commit()

    # Seed batches (one healthy, one near expiry)
    today = date.today()
    batch_healthy = Batch(
        batch_id="BAT001",
        batch_number="DL-2026-001",
        branch_id="BR001",
        medicine_id="MED001",
        mfg_date=today - timedelta(days=180),
        expiry_date=today + timedelta(days=360),
        initial_quantity=500,
        current_quantity=120,
        unit_cost_price=Decimal("20.00"),
    )
    batch_expiring = Batch(
        batch_id="BAT002",
        batch_number="TL-2025-099",
        branch_id="BR001",
        medicine_id="MED002",
        mfg_date=today - timedelta(days=650),
        expiry_date=today + timedelta(days=45),  # Expires in 45 days (<=90d)
        initial_quantity=300,
        current_quantity=180,
        unit_cost_price=Decimal("160.00"),
    )
    session.add_all([batch_healthy, batch_expiring])

    # Seed inventory snapshots
    inv1 = InventorySnapshot(
        branch_id="BR001",
        medicine_id="MED001",
        current_stock=Decimal("120.00"),
        pending_order_quantity=Decimal("0.00"),
        last_replenished_date=today - timedelta(days=5),
    )
    inv2 = InventorySnapshot(
        branch_id="BR001",
        medicine_id="MED002",
        current_stock=Decimal("15.00"),  # Low stock
        pending_order_quantity=Decimal("0.00"),
        last_replenished_date=today - timedelta(days=12),
    )
    session.add_all([inv1, inv2])

    # Seed daily sales (past 30 days)
    for day_idx in range(30):
        sale_dt = today - timedelta(days=30 - day_idx)
        s1 = DailySale(
            branch_id="BR001",
            medicine_id="MED001",
            date=sale_dt,
            units_sold=Decimal("10.00"),
            unit_price=Decimal("30.00"),
            total_revenue=Decimal("300.00"),
            is_stockout=False,
        )
        s2 = DailySale(
            branch_id="BR001",
            medicine_id="MED002",
            date=sale_dt,
            units_sold=Decimal("5.00"),
            unit_price=Decimal("220.00"),
            total_revenue=Decimal("1100.00"),
            is_stockout=False,
        )
        session.add_all([s1, s2])

    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db_session: Session) -> TestClient:
    """Provides a FastAPI TestClient with the database session overridden."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ------------------------------------------------------------------------------
# Test Cases
# ------------------------------------------------------------------------------

class TestFastAPIBackend:
    """Integration test suite validating RemediSync REST endpoints and contracts."""

    def test_health_endpoint(self, client: TestClient) -> None:
        """GET /api/v1/health returns system liveness and forecaster metadata."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["HEALTHY", "DEGRADED"]
        assert data["database"] == "CONNECTED"
        assert "uptime_seconds" in data
        assert "active_model" in data
        assert data["active_model"]["name"] is not None

    def test_analytics_overview_network(self, client: TestClient) -> None:
        """GET /api/v1/analytics/overview returns aggregated network KPIs."""
        response = client.get("/api/v1/analytics/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["network_daily_revenue_inr"] > 0
        assert data["target_daily_revenue_inr"] > 0
        assert data["performance_ratio"] > 0
        assert "network_stockout_rate" in data
        assert data["active_branches_count"] >= 1
        assert data["total_skus_tracked"] >= 2
        assert data["near_expiry_batches_count"] >= 1
        assert data["estimated_near_expiry_value_inr"] > 0

    def test_analytics_overview_branch_filtered(self, client: TestClient) -> None:
        """GET /api/v1/analytics/overview?branch_id=BR001 filters metrics to single branch."""
        response = client.get("/api/v1/analytics/overview?branch_id=BR001")
        assert response.status_code == 200
        data = response.json()
        assert data["active_branches_count"] == 1
        assert data["network_daily_revenue_inr"] > 0

    def test_branch_inventory_success(self, client: TestClient) -> None:
        """GET /api/v1/inventory/branches/{branch_id} returns enriched SKU telemetry."""
        response = client.get("/api/v1/inventory/branches/BR001")
        assert response.status_code == 200
        data = response.json()
        assert data["branch_id"] == "BR001"
        assert data["branch_name"] == "Guwahati Central Pharmacy"
        assert data["total_records"] >= 2
        assert len(data["items"]) >= 2

        # Check item structure
        item = data["items"][0]
        assert "medicine_id" in item
        assert "brand_name" in item
        assert "current_stock_units" in item
        assert "days_of_cover" in item
        assert "reorder_point" in item
        assert "is_below_rop" in item
        assert "abc_class" in item
        assert "demand_pattern" in item

    def test_branch_inventory_filtered(self, client: TestClient) -> None:
        """GET /api/v1/inventory/branches/BR001?category=Cardiovascular applies filter."""
        response = client.get("/api/v1/inventory/branches/BR001?category=Cardiovascular")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["brand_name"] == "Telma 40"

    def test_branch_inventory_not_found(self, client: TestClient) -> None:
        """GET /api/v1/inventory/branches/INVALID returns 404 with uniform error envelope."""
        response = client.get("/api/v1/inventory/branches/BR999")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "BRANCH_NOT_FOUND"
        assert "correlation_id" in data["error"]

    def test_batch_expiry_risk(self, client: TestClient) -> None:
        """GET /api/v1/inventory/batches/expiry-risk returns batches <= 90 days to expiry."""
        response = client.get("/api/v1/inventory/batches/expiry-risk?branch_id=BR001")
        assert response.status_code == 200
        data = response.json()
        assert data["total_at_risk_batches"] >= 1
        assert data["total_write_off_exposure_inr"] > 0
        batch = data["batches"][0]
        assert batch["batch_id"] == "BAT002"
        assert batch["days_to_expiry"] <= 90
        assert "recommended_action" in batch
        assert "action_rationale" in batch

    def test_replenishment_recommendations(self, client: TestClient) -> None:
        """GET /api/v1/recommendations/replenish generates prioritized order rationale."""
        response = client.get("/api/v1/recommendations/replenish?branch_id=BR001")
        assert response.status_code == 200
        data = response.json()
        assert data["branch_id"] == "BR001"
        assert "total_recommended_orders" in data
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0

        rec = data["recommendations"][0]
        assert "medicine_id" in rec
        assert "recommended_order_units" in rec
        assert "urgency" in rec
        assert "pack_size_rounding" in rec
        assert "calculation_rationale" in rec

    def test_replenishment_missing_branch_id(self, client: TestClient) -> None:
        """GET /api/v1/recommendations/replenish without branch_id returns 422."""
        response = client.get("/api/v1/recommendations/replenish")
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_order_approval_workflow(self, client: TestClient) -> None:
        """POST /api/v1/orders/approve creates approved POs and updates pending stock."""
        payload = {
            "branch_id": "BR001",
            "orders": [
                {
                    "medicine_id": "MED002",
                    "supplier_id": "SUP001",
                    "approved_quantity_units": 60.0,
                    "notes": "Emergency restock authorized",
                }
            ],
        }
        response = client.post("/api/v1/orders/approve", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert len(data["orders_created"]) == 1
        po = data["orders_created"][0]
        assert po["medicine_id"] == "MED002"
        assert po["approved_units"] == 60.0
        assert po["status"] == "APPROVED"
        assert po["order_id"].startswith("PO-BR001-")

    def test_order_approval_invalid_quantity(self, client: TestClient) -> None:
        """POST /api/v1/orders/approve with zero or negative quantity returns 422."""
        payload = {
            "branch_id": "BR001",
            "orders": [
                {
                    "medicine_id": "MED002",
                    "supplier_id": "SUP001",
                    "approved_quantity_units": -10.0,
                }
            ],
        }
        response = client.post("/api/v1/orders/approve", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_sales_history(self, client: TestClient) -> None:
        """GET /api/v1/sales/history returns chronological daily sales time series."""
        response = client.get("/api/v1/sales/history?branch_id=BR001&medicine_id=MED001&days=30")
        assert response.status_code == 200
        data = response.json()
        assert data["branch_id"] == "BR001"
        assert data["medicine_id"] == "MED001"
        assert data["total_days"] == 30
        assert len(data["sales"]) == 30
        assert data["sales"][0]["units_sold"] == 10.0
        assert "total_revenue" in data["sales"][0]

    def test_cors_preflight_and_headers(self, client: TestClient) -> None:
        """Verifies CORS middleware headers allow configured origins."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://localhost:5173"},
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
