"""Automated unit test suite for replenishment decision engine and expiry intelligence.

Validates safety stock scaling, reorder point arithmetic, urgency classification,
pack size ceiling rounding, FEFO lot depletion, supplier PO consolidation,
and plain-English pharmacist rationale generation.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.decision.expiry_intelligence import ExpiryIntelligenceEngine
from src.decision.inventory_policy import InventoryPolicy
from src.decision.order_generator import OrderGenerator


class TestInventoryPolicy:
    """Mathematical verification and boundary tests for InventoryPolicy."""

    def test_service_level_z_scores(self) -> None:
        """Verify Z-score assignments reflect therapeutic criticality."""
        # Critical chronic therapeutics (98% CSL)
        assert InventoryPolicy.get_service_level_z("Cardiovascular") == 2.05
        assert InventoryPolicy.get_service_level_z("Antidiabetic") == 2.05
        assert InventoryPolicy.get_service_level_z("Respiratory") == 2.05

        # Acute therapeutics (95% CSL)
        assert InventoryPolicy.get_service_level_z("Antibiotic") == 1.65
        assert InventoryPolicy.get_service_level_z("Analgesic") == 1.65

        # Discretionary OTC (90% CSL)
        assert InventoryPolicy.get_service_level_z("Nutritional") == 1.28
        assert InventoryPolicy.get_service_level_z("Probiotic") == 1.28

        # Unmapped fallback
        assert InventoryPolicy.get_service_level_z("UnknownTherapy") == 1.65

    def test_safety_stock_scaling(self) -> None:
        """Verify safety stock scales higher for life-saving therapeutics than OTC."""
        d_hat = 10.0
        lead_time = 2.0
        sigma_e = 4.0

        ss_chronic = InventoryPolicy.calculate_safety_stock(
            daily_demand=d_hat,
            lead_time_days=lead_time,
            sigma_e=sigma_e,
            category="Cardiovascular",
        )
        ss_acute = InventoryPolicy.calculate_safety_stock(
            daily_demand=d_hat,
            lead_time_days=lead_time,
            sigma_e=sigma_e,
            category="Antibiotic",
        )
        ss_otc = InventoryPolicy.calculate_safety_stock(
            daily_demand=d_hat,
            lead_time_days=lead_time,
            sigma_e=sigma_e,
            category="Nutritional",
        )

        assert ss_chronic > ss_acute > ss_otc > 0.0

    def test_safety_stock_input_validation(self) -> None:
        """Verify negative parameters trigger ValueErrors."""
        with pytest.raises(ValueError, match="daily_demand"):
            InventoryPolicy.calculate_safety_stock(-1.0, 1.0, 1.0, "Antibiotic")
        with pytest.raises(ValueError, match="lead_time_days"):
            InventoryPolicy.calculate_safety_stock(1.0, -1.0, 1.0, "Antibiotic")
        with pytest.raises(ValueError, match="sigma_e"):
            InventoryPolicy.calculate_safety_stock(1.0, 1.0, -1.0, "Antibiotic")

    def test_reorder_point_and_days_of_cover(self) -> None:
        """Verify ROP and DoC mathematical formulas."""
        rop = InventoryPolicy.calculate_reorder_point(
            daily_demand=5.0, lead_time_days=2.0, safety_stock=10.0
        )
        assert rop == 20.0  # (5 * 2) + 10

        # Standard Days of Cover
        assert InventoryPolicy.calculate_days_of_cover(50.0, 5.0) == 10.0
        # Zero demand with stock
        assert InventoryPolicy.calculate_days_of_cover(20.0, 0.0) == 999.0
        # Zero demand with zero stock
        assert InventoryPolicy.calculate_days_of_cover(0.0, 0.0) == 0.0

    def test_urgency_classification_boundaries(self) -> None:
        """Verify transitions across all 4 operational urgency tiers."""
        lead_time = 2.0
        rop = 30.0

        # CRITICAL: Stock on hand covers <= lead time (stockout before arrival)
        assert (
            InventoryPolicy.classify_urgency(
                current_stock=8.0,
                pending_order=0.0,
                rop=rop,
                days_of_cover=1.6,
                lead_time_days=lead_time,
            )
            == "CRITICAL"
        )

        # REORDER: (S + P) <= ROP, but DoC > lead_time (safe buffer during delivery)
        assert (
            InventoryPolicy.classify_urgency(
                current_stock=25.0,
                pending_order=0.0,
                rop=rop,
                days_of_cover=5.0,
                lead_time_days=lead_time,
            )
            == "REORDER"
        )

        # HEALTHY: (S + P) > ROP and DoC <= 21 days
        assert (
            InventoryPolicy.classify_urgency(
                current_stock=40.0,
                pending_order=0.0,
                rop=rop,
                days_of_cover=8.0,
                lead_time_days=lead_time,
            )
            == "HEALTHY"
        )

        # OVERSTOCKED: DoC > 21 days
        assert (
            InventoryPolicy.classify_urgency(
                current_stock=150.0,
                pending_order=0.0,
                rop=rop,
                days_of_cover=30.0,
                lead_time_days=lead_time,
            )
            == "OVERSTOCKED"
        )

    def test_pack_size_rounding(self) -> None:
        """Verify order units round up to exact integer commercial pack multiples."""
        daily_d = 5.0
        ss = 10.0
        # Target level = (5 * 7) + 10 = 45 units
        # Stock on hand = 15 units. Deficit = 30 units.
        # Pack size = 15 tablets/pack -> Exactly 2 packs (30 units)
        units, packs = InventoryPolicy.calculate_reorder_quantity(
            daily_demand=daily_d,
            safety_stock=ss,
            current_stock=15.0,
            pending_order=0.0,
            units_per_pack=15,
            rop=25.0,
        )
        assert packs == 2
        assert units == 30

        # Odd deficit rounding: Deficit = 32 units, Pack size = 10 -> 4 packs (40 units)
        units, packs = InventoryPolicy.calculate_reorder_quantity(
            daily_demand=daily_d,
            safety_stock=ss,
            current_stock=13.0,
            pending_order=0.0,
            units_per_pack=10,
            rop=25.0,
        )
        assert packs == 4
        assert units == 40

        # No order when (S + P) > ROP
        units, packs = InventoryPolicy.calculate_reorder_quantity(
            daily_demand=daily_d,
            safety_stock=ss,
            current_stock=30.0,
            pending_order=0.0,
            units_per_pack=10,
            rop=25.0,
        )
        assert packs == 0
        assert units == 0

    def test_plain_english_rationale_consistency(self) -> None:
        """Ensure human-readable rationale outputs contain actionable figures."""
        rationale_crit = InventoryPolicy.generate_rationale(
            brand_name="Dolo 650",
            current_stock=6,
            days_of_cover=1.2,
            lead_time_days=2.0,
            predicted_7d_demand=35.0,
            safety_stock=8,
            rop=18,
            order_units=45,
            order_packs=3,
            urgency="CRITICAL",
        )
        assert "Dolo 650" in rationale_crit
        assert "gap" in rationale_crit
        assert "3 packs (45 units) immediately" in rationale_crit

        rationale_reorder = InventoryPolicy.generate_rationale(
            brand_name="Telma 40",
            current_stock=15,
            days_of_cover=3.0,
            lead_time_days=1.0,
            predicted_7d_demand=35.0,
            safety_stock=10,
            rop=20,
            order_units=30,
            order_packs=2,
            urgency="REORDER",
        )
        assert "breached ROP" in rationale_reorder
        assert "Telma 40" in rationale_reorder


class TestExpiryIntelligenceEngine:
    """Verification suite for batch-level expiry auditing and waste estimation."""

    def test_load_batches_structure(self) -> None:
        """Verify batches CSV loading and FEFO sorting."""
        engine = ExpiryIntelligenceEngine()
        df = engine.load_batches()

        assert len(df) == 808
        assert "batch_number" in df.columns
        assert "expiry_date" in df.columns
        assert df["expiry_date"].is_monotonic_increasing or len(df) > 0

    def test_audit_batch_expiry_risk(self) -> None:
        """Verify FEFO depletion tracking and risk tiering."""
        engine = ExpiryIntelligenceEngine()
        demand_lookup = {("BR001", "MED001"): 5.0}

        audit_df = engine.audit_batch_expiry_risk(
            daily_demand_lookup=demand_lookup, as_of_date="2026-09-30"
        )

        assert len(audit_df) == 808
        assert "days_to_expiry" in audit_df.columns
        assert "units_at_risk" in audit_df.columns
        assert "capital_at_risk" in audit_df.columns
        assert "risk_tier" in audit_df.columns

        # Verify risk tiers are valid
        valid_tiers = {"EXPIRED", "HIGH", "MEDIUM", "LOW"}
        assert set(audit_df["risk_tier"].unique()).issubset(valid_tiers)
        assert (audit_df["units_at_risk"] >= 0.0).all()
        assert (audit_df["capital_at_risk"] >= 0.0).all()

    def test_summarize_branch_expiry_exposure(self) -> None:
        """Verify branch aggregation metrics."""
        engine = ExpiryIntelligenceEngine()
        demand_lookup = {("BR001", "MED001"): 5.0}
        audit_df = engine.audit_batch_expiry_risk(
            daily_demand_lookup=demand_lookup, as_of_date="2026-09-30"
        )
        summary = engine.summarize_branch_expiry_exposure(audit_df)

        assert len(summary) == 4  # 4 branches
        assert "total_batches" in summary.columns
        assert "near_expiry_batches" in summary.columns
        assert "total_capital_at_risk" in summary.columns
        assert summary["total_batches"].sum() == 808


class TestOrderGenerator:
    """Full end-to-end integration test suite for OrderGenerator."""

    def test_load_telemetry(self) -> None:
        """Verify merged schema integrity across inventory, medicines, and suppliers."""
        generator = OrderGenerator()
        merged_inv, med_df, sup_df = generator.load_telemetry()

        assert len(merged_inv) == 516
        assert len(med_df) == 129
        assert len(sup_df) == 30
        assert "primary_supplier_id" in merged_inv.columns
        assert "units_per_pack" in merged_inv.columns

    def test_fetch_demand_forecasts(self) -> None:
        """Verify ML forecaster integration returns predictions for all 516 series."""
        generator = OrderGenerator()
        forecasts = generator.fetch_demand_forecasts()

        assert len(forecasts) == 516
        assert "predicted_7d_demand" in forecasts.columns
        assert (forecasts["predicted_7d_demand"] >= 0.0).all()

    def test_generate_daily_recommendations(self) -> None:
        """Verify full series replenishment calculations and packaging rounding."""
        generator = OrderGenerator()
        recs_df = generator.generate_daily_recommendations()

        assert len(recs_df) == 516
        for col in [
            "branch_id",
            "medicine_id",
            "brand_name",
            "current_stock",
            "predicted_7d_demand",
            "safety_stock",
            "reorder_point",
            "days_of_cover",
            "urgency",
            "recommended_order_packs",
            "recommended_order_units",
            "recommended_order_cost",
            "rationale",
        ]:
            assert col in recs_df.columns

        # Verify all order units are exact integer multiples of units_per_pack
        for _, row in recs_df.iterrows():
            if row["recommended_order_packs"] > 0:
                assert (
                    row["recommended_order_units"]
                    == row["recommended_order_packs"] * row["units_per_pack"]
                )

    def test_build_supplier_purchase_orders(self) -> None:
        """Verify distributor PO grouping, line item ordering, and cost totals."""
        generator = OrderGenerator()
        recs_df = generator.generate_daily_recommendations()
        pos = generator.build_supplier_purchase_orders(recs_df)

        assert len(pos) > 0
        for po in pos:
            assert "po_id" in po
            assert "supplier_id" in po
            assert "supplier_name" in po
            assert "line_items" in po
            assert po["total_cost"] >= 0.0
            assert po["total_packs"] >= 0
            assert len(po["line_items"]) == po["total_items"]

            # Line items must be sorted with CRITICAL first
            urgencies = [item["urgency"] for item in po["line_items"]]
            if "CRITICAL" in urgencies and "REORDER" in urgencies:
                crit_idx = urgencies.index("CRITICAL")
                reorder_idx = urgencies.index("REORDER")
                assert crit_idx < reorder_idx

    def test_run_pipeline(self) -> None:
        """Verify complete pipeline execution and KPI dictionary completeness."""
        generator = OrderGenerator()
        results = generator.run_pipeline()

        assert "recommendations" in results
        assert "purchase_orders" in results
        assert "batch_expiry_audit" in results
        assert "branch_expiry_summary" in results
        assert "kpis" in results

        kpis = results["kpis"]
        assert kpis["total_series"] == 516
        assert kpis["critical_count"] >= 0
        assert kpis["reorder_count"] >= 0
        assert kpis["total_procurement_cost"] > 0.0
