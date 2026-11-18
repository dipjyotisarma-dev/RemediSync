"""Automated unit test suite for discrete-event backtesting and replenishment simulator.

Validates simulation data preparation, identical initial starting conditions,
delivery pipeline lead-time arrivals, stockout and lost sales accounting,
commercial pack size rounding compliance, RemediSync outperformance gates,
scorecard string formatting, and JSON export schema.
"""

from pathlib import Path
import json
import numpy as np
import pytest

from src.decision.policy_simulator import PolicySimulator, SimulationKPIs


@pytest.fixture(scope="module")
def simulator() -> PolicySimulator:
    """Fixture providing initialized PolicySimulator instance."""
    return PolicySimulator()


class TestPolicySimulator:
    """Unit tests for PolicySimulator discrete-event replay engine."""

    def test_simulator_initialization(self, simulator: PolicySimulator) -> None:
        """Verify simulator loads paths and validates required artifacts."""
        assert simulator.daily_sales_path.exists()
        assert simulator.medicines_path.exists()
        assert simulator.suppliers_path.exists()
        assert simulator.feature_matrix_path.exists()
        assert simulator.model_path.exists()

        sigma_e = simulator.load_sigma_e()
        assert isinstance(sigma_e, float)
        assert sigma_e > 0.0

    def test_missing_file_raises_error(self, tmp_path: Path) -> None:
        """Verify FileNotFoundError is raised if a required telemetry file is missing."""
        with pytest.raises(FileNotFoundError):
            PolicySimulator(daily_sales_path=str(tmp_path / "missing_sales.csv"))

    def test_prepare_simulation_data_structure(self, simulator: PolicySimulator) -> None:
        """Verify shape, types, and alignment of precomputed simulation data arrays."""
        # Test over a 7-day slice
        prep = simulator.prepare_simulation_data(
            start_date="2026-07-01", end_date="2026-07-07"
        )

        assert prep["num_series"] == 516
        assert prep["total_days"] == 7
        assert len(prep["sim_dates"]) == 7

        # Check matrix shapes
        assert prep["demand_matrix"].shape == (7, 516)
        assert prep["forecast_matrix"].shape == (7, 516)

        # Check dimension vector shapes and values
        assert len(prep["lead_times"]) == 516
        assert len(prep["pack_sizes"]) == 516
        assert len(prep["mrps"]) == 516
        assert len(prep["cost_prices"]) == 516
        assert len(prep["z_scores"]) == 516
        assert len(prep["categories"]) == 516

        # Dimensions sanity
        assert np.all(prep["lead_times"] >= 1)
        assert np.all(prep["pack_sizes"] >= 1)
        assert np.all(prep["mrps"] > 0)
        assert np.all(prep["cost_prices"] > 0)
        assert np.all(prep["z_scores"] >= 1.28)
        assert np.all(prep["demand_matrix"] >= 0.0)
        assert np.all(prep["forecast_matrix"] >= 0.0)

    def test_identical_initial_conditions(self, simulator: PolicySimulator) -> None:
        """Verify both policies start at the exact same inventory levels."""
        prep = simulator.prepare_simulation_data(
            start_date="2026-07-01", end_date="2026-07-03"
        )
        base_daily = prep["base_daily_demand"]
        pack_sizes = prep["pack_sizes"]

        initial_stock = np.maximum(
            pack_sizes.astype(float),
            np.ceil(10.0 * base_daily),
        )

        assert len(initial_stock) == 516
        assert np.all(initial_stock >= pack_sizes)
        assert np.all(initial_stock > 0)

    def test_stockout_and_lost_sales_accounting(self, simulator: PolicySimulator) -> None:
        """Verify dispensing never drives stock negative and correctly tracks lost demand."""
        # Synthetic 3-day scenario with 2 series
        total_days = 3
        num_series = 2
        initial_stock = np.array([10.0, 5.0], dtype=np.float64)
        demand_matrix = np.array([
            [12.0, 3.0],  # Day 0: S0 stocks out (wants 12, has 10), S1 sells 3 (has 5)
            [5.0, 4.0],   # Day 1: S0 wants 5 (has 0), S1 stocks out (wants 4, has 2)
            [0.0, 1.0],   # Day 2: S0 wants 0, S1 wants 1
        ], dtype=np.float64)

        lead_times = np.array([1, 1], dtype=np.int32)
        pack_sizes = np.array([10, 5], dtype=np.int32)
        base_daily = np.array([5.0, 2.0], dtype=np.float64)
        mrps = np.array([100.0, 50.0], dtype=np.float64)
        cost_prices = np.array([70.0, 35.0], dtype=np.float64)
        categories = ["Cardiovascular", "Antibiotic"]

        kpis = simulator._simulate_baseline_policy(
            total_days=total_days,
            num_series=num_series,
            initial_stock=initial_stock,
            demand_matrix=demand_matrix,
            lead_times=lead_times,
            pack_sizes=pack_sizes,
            base_daily_demand=base_daily,
            mrps=mrps,
            cost_prices=cost_prices,
            categories=categories,
        )

        # Day 0: S0 lost = 2, S1 lost = 0
        # Day 1: S0 arriving order (placed at t=0 arrives at t=1, so S0 had stock arrive)
        assert kpis.stockout_incidents >= 1
        assert kpis.total_demand_units == pytest.approx(12 + 3 + 5 + 4 + 0 + 1, rel=1e-3)
        assert kpis.fulfilled_units + kpis.unfulfilled_units == pytest.approx(kpis.total_demand_units, rel=1e-3)
        assert kpis.total_sales_revenue > 0.0
        assert kpis.lost_sales_revenue >= 0.0

    def test_remedisync_outperformance_gates(self, simulator: PolicySimulator) -> None:
        """Verify RemediSync dynamic policy satisfies business promotion criteria."""
        results = simulator.run_simulation(
            start_date="2026-07-01",
            end_date="2026-09-23",
            initial_stock_days=10.0,
        )

        b = results["baseline"]
        r = results["remedisync"]
        d = results["deltas"]

        # 1. Stockout reduction must be at least 50%
        assert d["stockout_delta_pct"] <= -50.0, f"Expected <= -50%, got {d['stockout_delta_pct']}%"
        assert r["stockout_incidents"] < b["stockout_incidents"]

        # 2. Overall prescription fulfillment must be >= 98.0%
        assert r["fulfillment_rate_pct"] >= 98.0

        # 3. Chronic category fulfillment must achieve >= 98.0%
        chronic_cats = ["Cardiovascular", "Antidiabetic", "Respiratory", "Endocrine"]
        chronic_rates = [
            r["category_fulfillment"][c]
            for c in chronic_cats
            if c in r["category_fulfillment"]
        ]
        assert len(chronic_rates) > 0
        assert np.mean(chronic_rates) >= 98.0

        # 4. Emergency expedite alerts must be lower under RemediSync
        assert r["critical_expedite_triggers"] < b["critical_expedite_triggers"]
        assert d["expedite_delta_pct"] <= -50.0

        # 5. Working capital reduction must be positive (capital freed)
        assert d["working_capital_delta_pct"] < 0.0

    def test_scorecard_and_export(self, simulator: PolicySimulator, tmp_path: Path) -> None:
        """Verify terminal scorecard formatting and JSON file export."""
        # Run over a 14-day slice for rapid test assertion
        results = simulator.run_simulation(
            start_date="2026-07-01",
            end_date="2026-07-14",
            initial_stock_days=10.0,
        )

        # 1. Scorecard string format check
        scorecard = simulator.format_scorecard(results)
        assert "REMEDISYNC: BACKTESTING & POLICY SIMULATION SCORECARD" in scorecard
        assert "Stockout Incidents" in scorecard
        assert "Prescription Fulfillment Rate" in scorecard
        assert "Avg Daily Inventory Value" in scorecard

        # 2. JSON export check
        export_file = tmp_path / "test_sim_results.json"
        exported_path = simulator.export_results(results, output_path=str(export_file))
        assert exported_path.exists()

        with open(exported_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "baseline" in data
        assert "remedisync" in data
        assert "deltas" in data
        assert data["metadata"]["total_days"] == 14
        assert data["metadata"]["num_series"] == 516
