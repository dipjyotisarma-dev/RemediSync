"""Discrete-event backtesting and replenishment policy simulation engine.

Simulates and benchmarks RemediSync ML-driven dynamic replenishment policy
against a baseline static heuristic policy across out-of-time test series.
Tracks business KPIs: stockout incidents, prescription fulfillment, working
capital, lost revenue, and emergency expedite triggers.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import math
import numpy as np
import pandas as pd

from src.decision.inventory_policy import InventoryPolicy
from src.models.forecaster import DemandForecaster


@dataclass
class SimulationKPIs:
    """Consolidated performance scorecard for an inventory replenishment policy."""

    policy_name: str
    total_series_days: int
    stockout_incidents: int
    stockout_days: int
    stockout_rate_pct: float
    total_demand_units: float
    fulfilled_units: float
    unfulfilled_units: float
    fulfillment_rate_pct: float
    total_sales_revenue: float
    lost_sales_revenue: float
    avg_daily_inventory_units: float
    avg_daily_inventory_value: float
    peak_inventory_value: float
    total_orders_placed: int
    total_units_ordered: int
    total_procurement_cost: float
    critical_expedite_triggers: int
    category_fulfillment: Dict[str, float] = field(default_factory=dict)
    category_stockouts: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert KPIs dataclass to JSON-serializable dictionary."""
        return {
            "policy_name": self.policy_name,
            "total_series_days": int(self.total_series_days),
            "stockout_incidents": int(self.stockout_incidents),
            "stockout_days": int(self.stockout_days),
            "stockout_rate_pct": float(round(self.stockout_rate_pct, 3)),
            "total_demand_units": float(round(self.total_demand_units, 1)),
            "fulfilled_units": float(round(self.fulfilled_units, 1)),
            "unfulfilled_units": float(round(self.unfulfilled_units, 1)),
            "fulfillment_rate_pct": float(round(self.fulfillment_rate_pct, 2)),
            "total_sales_revenue": float(round(self.total_sales_revenue, 2)),
            "lost_sales_revenue": float(round(self.lost_sales_revenue, 2)),
            "avg_daily_inventory_units": float(round(self.avg_daily_inventory_units, 1)),
            "avg_daily_inventory_value": float(round(self.avg_daily_inventory_value, 2)),
            "peak_inventory_value": float(round(self.peak_inventory_value, 2)),
            "total_orders_placed": int(self.total_orders_placed),
            "total_units_ordered": int(self.total_units_ordered),
            "total_procurement_cost": float(round(self.total_procurement_cost, 2)),
            "critical_expedite_triggers": int(self.critical_expedite_triggers),
            "category_fulfillment": {
                k: float(round(v, 2)) for k, v in self.category_fulfillment.items()
            },
            "category_stockouts": {
                k: int(v) for k, v in self.category_stockouts.items()
            },
        }


class PolicySimulator:
    """Discrete-event inventory backtesting engine for retail pharmacy chains."""

    def __init__(
        self,
        daily_sales_path: str = "data/raw/daily_sales.csv",
        medicines_path: str = "data/raw/medicines.csv",
        suppliers_path: str = "data/raw/suppliers.csv",
        feature_matrix_path: str = "data/processed/feature_matrix.parquet",
        model_path: str = "models/production_forecaster.joblib",
        diagnostics_path: str = "data/processed/evaluation_diagnostics.json",
    ) -> None:
        """Initialize simulator environment and data paths.

        Args:
            daily_sales_path: Path to historical daily sales CSV.
            medicines_path: Path to master medicine catalog CSV.
            suppliers_path: Path to master supplier catalog CSV.
            feature_matrix_path: Path to engineered feature store Parquet.
            model_path: Path to serialized production demand forecaster.
            diagnostics_path: Path to model evaluation diagnostics JSON.
        """
        self.daily_sales_path = Path(daily_sales_path)
        self.medicines_path = Path(medicines_path)
        self.suppliers_path = Path(suppliers_path)
        self.feature_matrix_path = Path(feature_matrix_path)
        self.model_path = Path(model_path)
        self.diagnostics_path = Path(diagnostics_path)

        self._validate_inputs()

    def _validate_inputs(self) -> None:
        """Verify that all required data and model artifacts exist."""
        required = [
            (self.daily_sales_path, "Daily sales CSV"),
            (self.medicines_path, "Medicines catalog CSV"),
            (self.suppliers_path, "Suppliers catalog CSV"),
            (self.feature_matrix_path, "Feature matrix Parquet"),
            (self.model_path, "Production forecaster model"),
        ]
        for path, desc in required:
            if not path.exists():
                raise FileNotFoundError(f"{desc} not found at {path}")

    def load_sigma_e(self) -> float:
        """Load empirical forecast residual error standard deviation.

        Returns:
            sigma_e standard deviation in units (defaults to 5.12 if file missing).
        """
        if self.diagnostics_path.exists():
            try:
                with open(self.diagnostics_path, "r", encoding="utf-8") as f:
                    diag = json.load(f)
                return float(diag.get("residual_calibration", {}).get("overall_sigma_e", 5.12))
            except Exception:
                return 5.12
        return 5.12

    def prepare_simulation_data(
        self,
        start_date: str = "2026-07-01",
        end_date: str = "2026-09-23",
    ) -> Dict[str, Any]:
        """Load and precompute static dimensions, historical baselines, and test demand.

        Args:
            start_date: Start date string (YYYY-MM-DD).
            end_date: End date string (YYYY-MM-DD).

        Returns:
            Dictionary containing structured arrays, lookups, and test demand matrix.
        """
        # 1. Ingest master dimensions
        med_df = pd.read_csv(self.medicines_path)
        sup_df = pd.read_csv(self.suppliers_path)
        sales_df = pd.read_csv(self.daily_sales_path)

        # Merge supplier lead times
        sup_lead_map = dict(zip(sup_df["supplier_id"], sup_df["lead_time_days"]))
        med_df["lead_time_days"] = med_df["primary_supplier_id"].map(sup_lead_map).fillna(1).astype(int)

        # 2. Extract series identity: sorted (branch_id, medicine_id) pairs
        branches = sorted(sales_df["branch_id"].unique().tolist())
        med_ids = sorted(med_df["medicine_id"].unique().tolist())

        series_pairs: List[Tuple[str, str]] = [
            (b, m) for b in branches for m in med_ids
        ]
        num_series = len(series_pairs)
        series_to_idx = {pair: i for i, pair in enumerate(series_pairs)}

        # 3. Create static attribute arrays for all 516 series
        med_dict = med_df.set_index("medicine_id").to_dict(orient="index")

        lead_times = np.zeros(num_series, dtype=np.int32)
        pack_sizes = np.zeros(num_series, dtype=np.int32)
        mrps = np.zeros(num_series, dtype=np.float64)
        cost_prices = np.zeros(num_series, dtype=np.float64)
        categories: List[str] = []
        z_scores = np.zeros(num_series, dtype=np.float64)

        for i, (b_id, m_id) in enumerate(series_pairs):
            m_info = med_dict[m_id]
            lead_times[i] = int(m_info["lead_time_days"])
            pack_sizes[i] = max(1, int(m_info["units_per_pack"]))
            mrps[i] = float(m_info["mrp"])
            cost_prices[i] = float(m_info["cost_price"])
            cat = str(m_info["category"])
            categories.append(cat)
            z_scores[i] = InventoryPolicy.get_service_level_z(cat)

        # 4. Compute baseline historical average daily sales from training set (prior to start_date)
        sales_train = sales_df[sales_df["date"] < start_date]
        mean_sales = (
            sales_train.groupby(["branch_id", "medicine_id"])["units_sold"]
            .mean()
            .to_dict()
        )
        base_daily_demand = np.zeros(num_series, dtype=np.float64)
        for i, pair in enumerate(series_pairs):
            base_daily_demand[i] = max(0.1, float(mean_sales.get(pair, 2.0)))

        # 5. Extract simulation date sequence
        dt_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        dt_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        total_days = (dt_end - dt_start).days + 1
        sim_dates = [dt_start + timedelta(days=d) for d in range(total_days)]
        date_to_t = {d.isoformat(): t for t, d in enumerate(sim_dates)}

        # 6. Build actual customer demand matrix: shape (num_days, num_series)
        sales_test = sales_df[
            (sales_df["date"] >= start_date) & (sales_df["date"] <= end_date)
        ]
        demand_matrix = np.zeros((total_days, num_series), dtype=np.float64)

        for row in sales_test.itertuples(index=False):
            t_idx = date_to_t.get(row.date)
            s_idx = series_to_idx.get((row.branch_id, row.medicine_id))
            if t_idx is not None and s_idx is not None:
                demand_matrix[t_idx, s_idx] = float(row.units_sold)

        # 7. Generate out-of-time ML forecasts using DemandForecaster
        forecast_matrix = self._generate_ml_forecast_matrix(
            start_date=start_date,
            end_date=end_date,
            series_to_idx=series_to_idx,
            date_to_t=date_to_t,
            total_days=total_days,
            num_series=num_series,
        )

        return {
            "num_series": num_series,
            "total_days": total_days,
            "sim_dates": sim_dates,
            "series_pairs": series_pairs,
            "lead_times": lead_times,
            "pack_sizes": pack_sizes,
            "mrps": mrps,
            "cost_prices": cost_prices,
            "categories": categories,
            "z_scores": z_scores,
            "base_daily_demand": base_daily_demand,
            "demand_matrix": demand_matrix,
            "forecast_matrix": forecast_matrix,
            "sigma_e": self.load_sigma_e(),
        }

    def _generate_ml_forecast_matrix(
        self,
        start_date: str,
        end_date: str,
        series_to_idx: Dict[Tuple[str, str], int],
        date_to_t: Dict[str, int],
        total_days: int,
        num_series: int,
    ) -> np.ndarray:
        """Batch-generate 7-day out-of-time ML forecasts across test horizon.

        Returns:
            Matrix of predicted daily demand (Y_hat / 7) of shape (total_days, num_series).
        """
        forecaster = DemandForecaster(data_path=self.feature_matrix_path)
        model, _ = forecaster.load_model(self.model_path)

        df = pd.read_parquet(self.feature_matrix_path)
        df["date_str"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        test_slice = df[
            (df["date_str"] >= start_date) & (df["date_str"] <= end_date)
        ].copy().reset_index(drop=True)

        X_tree, _ = forecaster.prepare_features(test_slice, for_tree=True)
        raw_predictions = forecaster.predict(model, X_tree)
        test_slice["y_hat_7d"] = np.maximum(0.0, raw_predictions)

        forecast_matrix = np.zeros((total_days, num_series), dtype=np.float64)

        for row in test_slice.itertuples(index=False):
            t_idx = date_to_t.get(row.date_str)
            s_idx = series_to_idx.get((row.branch_id, row.medicine_id))
            if t_idx is not None and s_idx is not None:
                # Store daily demand velocity: Y_hat / 7.0
                forecast_matrix[t_idx, s_idx] = float(row.y_hat_7d) / 7.0

        return forecast_matrix

    def _simulate_baseline_policy(
        self,
        total_days: int,
        num_series: int,
        initial_stock: np.ndarray,
        demand_matrix: np.ndarray,
        lead_times: np.ndarray,
        pack_sizes: np.ndarray,
        base_daily_demand: np.ndarray,
        mrps: np.ndarray,
        cost_prices: np.ndarray,
        categories: List[str],
    ) -> SimulationKPIs:
        """Execute discrete-event simulation under Baseline Static Min-Max Heuristic."""
        current_stock = initial_stock.copy()
        pending_stock = np.zeros(num_series, dtype=np.float64)

        # Pending order arrivals queue: delivery_day -> list of (series_idx, qty)
        deliveries_queue: Dict[int, List[Tuple[int, float]]] = {}

        # Static policy parameters
        # ROP = max(ceil(3 * base_daily), pack_size)
        static_rop = np.maximum(
            np.ceil(3.0 * base_daily_demand), pack_sizes.astype(float)
        )
        # Order quantity = max(1, ceil(10 * base_daily / pack_size)) * pack_size
        static_batches = np.maximum(
            1.0, np.ceil((10.0 * base_daily_demand) / pack_sizes.astype(float))
        )
        static_q = static_batches * pack_sizes.astype(float)

        # Metric accumulators
        stockout_incidents = 0
        stockout_days_set = set()
        total_demand_units = 0.0
        fulfilled_units = 0.0
        unfulfilled_units = 0.0
        total_sales_revenue = 0.0
        lost_sales_revenue = 0.0
        total_orders_placed = 0
        total_units_ordered = 0
        total_procurement_cost = 0.0
        critical_expedite_triggers = 0

        daily_closing_units_sum = 0.0
        daily_closing_value_sum = 0.0
        peak_inventory_value = 0.0

        cat_demand: Dict[str, float] = {}
        cat_fulfilled: Dict[str, float] = {}
        cat_stockouts: Dict[str, int] = {}

        for t in range(total_days):
            # Step 1: Morning Delivery Ingestion
            arriving = deliveries_queue.pop(t, [])
            for s_idx, qty in arriving:
                current_stock[s_idx] += qty
                pending_stock[s_idx] = max(0.0, pending_stock[s_idx] - qty)

            # Step 2: Customer Demand Dispensing
            d_t = demand_matrix[t]
            dispensed = np.minimum(current_stock, d_t)
            lost = d_t - dispensed
            has_stockout = lost > 0

            current_stock -= dispensed

            # Accumulate dispensing metrics
            day_dispensed_sum = float(np.sum(dispensed))
            day_lost_sum = float(np.sum(lost))
            day_demand_sum = float(np.sum(d_t))
            day_stockouts = int(np.sum(has_stockout))

            total_demand_units += day_demand_sum
            fulfilled_units += day_dispensed_sum
            unfulfilled_units += day_lost_sum
            stockout_incidents += day_stockouts

            if day_stockouts > 0:
                stockout_days_set.add(t)

            total_sales_revenue += float(np.sum(dispensed * mrps))
            lost_sales_revenue += float(np.sum(lost * mrps))

            # Stratified category tracking
            for i in range(num_series):
                c = categories[i]
                cat_demand[c] = cat_demand.get(c, 0.0) + d_t[i]
                cat_fulfilled[c] = cat_fulfilled.get(c, 0.0) + dispensed[i]
                if has_stockout[i]:
                    cat_stockouts[c] = cat_stockouts.get(c, 0) + 1

            # Step 3: Evening Replenishment Review
            effective_stock = current_stock + pending_stock
            reorder_mask = effective_stock <= static_rop

            for s_idx in np.where(reorder_mask)[0]:
                q = static_q[s_idx]
                lt = lead_times[s_idx]
                delivery_day = t + lt

                deliveries_queue.setdefault(delivery_day, []).append((s_idx, q))
                pending_stock[s_idx] += q

                total_orders_placed += 1
                total_units_ordered += int(q)
                total_procurement_cost += q * cost_prices[s_idx]

                # Check expedite condition (DoC <= Lead time)
                base_d = base_daily_demand[s_idx]
                doc = current_stock[s_idx] / base_d if base_d > 0 else 999.0
                if doc <= lt:
                    critical_expedite_triggers += 1

            # Step 4: Daily Financial Accounting
            closing_units = float(np.sum(current_stock))
            closing_val = float(np.sum(current_stock * cost_prices))
            daily_closing_units_sum += closing_units
            daily_closing_value_sum += closing_val
            peak_inventory_value = max(peak_inventory_value, closing_val)

        total_series_days = total_days * num_series
        stockout_rate = (stockout_incidents / total_series_days) * 100.0 if total_series_days > 0 else 0.0
        fulfillment_rate = (fulfilled_units / total_demand_units) * 100.0 if total_demand_units > 0 else 100.0
        avg_daily_units = daily_closing_units_sum / float(total_days)
        avg_daily_val = daily_closing_value_sum / float(total_days)

        cat_fulfillment_rates = {
            c: (cat_fulfilled[c] / cat_demand[c] * 100.0) if cat_demand[c] > 0 else 100.0
            for c in cat_demand
        }

        return SimulationKPIs(
            policy_name="Baseline Static Policy",
            total_series_days=total_series_days,
            stockout_incidents=stockout_incidents,
            stockout_days=len(stockout_days_set),
            stockout_rate_pct=stockout_rate,
            total_demand_units=total_demand_units,
            fulfilled_units=fulfilled_units,
            unfulfilled_units=unfulfilled_units,
            fulfillment_rate_pct=fulfillment_rate,
            total_sales_revenue=total_sales_revenue,
            lost_sales_revenue=lost_sales_revenue,
            avg_daily_inventory_units=avg_daily_units,
            avg_daily_inventory_value=avg_daily_val,
            peak_inventory_value=peak_inventory_value,
            total_orders_placed=total_orders_placed,
            total_units_ordered=total_units_ordered,
            total_procurement_cost=total_procurement_cost,
            critical_expedite_triggers=critical_expedite_triggers,
            category_fulfillment=cat_fulfillment_rates,
            category_stockouts=cat_stockouts,
        )

    def _simulate_remedisync_policy(
        self,
        total_days: int,
        num_series: int,
        initial_stock: np.ndarray,
        demand_matrix: np.ndarray,
        forecast_matrix: np.ndarray,
        lead_times: np.ndarray,
        pack_sizes: np.ndarray,
        z_scores: np.ndarray,
        mrps: np.ndarray,
        cost_prices: np.ndarray,
        categories: List[str],
        sigma_e: float,
        lead_time_std: float = 0.25,
    ) -> SimulationKPIs:
        """Execute discrete-event simulation under RemediSync ML-Driven Dynamic Policy."""
        current_stock = initial_stock.copy()
        pending_stock = np.zeros(num_series, dtype=np.float64)

        # Pending order arrivals queue: delivery_day -> list of (series_idx, qty)
        deliveries_queue: Dict[int, List[Tuple[int, float]]] = {}

        # Metric accumulators
        stockout_incidents = 0
        stockout_days_set = set()
        total_demand_units = 0.0
        fulfilled_units = 0.0
        unfulfilled_units = 0.0
        total_sales_revenue = 0.0
        lost_sales_revenue = 0.0
        total_orders_placed = 0
        total_units_ordered = 0
        total_procurement_cost = 0.0
        critical_expedite_triggers = 0

        daily_closing_units_sum = 0.0
        daily_closing_value_sum = 0.0
        peak_inventory_value = 0.0

        cat_demand: Dict[str, float] = {}
        cat_fulfilled: Dict[str, float] = {}
        cat_stockouts: Dict[str, int] = {}

        for t in range(total_days):
            # Step 1: Morning Delivery Ingestion
            arriving = deliveries_queue.pop(t, [])
            for s_idx, qty in arriving:
                current_stock[s_idx] += qty
                pending_stock[s_idx] = max(0.0, pending_stock[s_idx] - qty)

            # Step 2: Customer Demand Dispensing
            d_t = demand_matrix[t]
            dispensed = np.minimum(current_stock, d_t)
            lost = d_t - dispensed
            has_stockout = lost > 0

            current_stock -= dispensed

            # Accumulate dispensing metrics
            day_dispensed_sum = float(np.sum(dispensed))
            day_lost_sum = float(np.sum(lost))
            day_demand_sum = float(np.sum(d_t))
            day_stockouts = int(np.sum(has_stockout))

            total_demand_units += day_demand_sum
            fulfilled_units += day_dispensed_sum
            unfulfilled_units += day_lost_sum
            stockout_incidents += day_stockouts

            if day_stockouts > 0:
                stockout_days_set.add(t)

            total_sales_revenue += float(np.sum(dispensed * mrps))
            lost_sales_revenue += float(np.sum(lost * mrps))

            # Stratified category tracking
            for i in range(num_series):
                c = categories[i]
                cat_demand[c] = cat_demand.get(c, 0.0) + d_t[i]
                cat_fulfilled[c] = cat_fulfilled.get(c, 0.0) + dispensed[i]
                if has_stockout[i]:
                    cat_stockouts[c] = cat_stockouts.get(c, 0) + 1

            # Step 3: Evening Replenishment Review with Dynamic Formulas
            # ML forecasted daily velocity: d_hat
            d_hat = forecast_matrix[t]
            effective_stock = current_stock + pending_stock

            # Dynamic Safety Stock: SS = Z * sqrt(L * sigma_e^2 + d_hat^2 * sigma_L^2)
            variance = (lead_times.astype(float) * (sigma_e**2)) + (
                (d_hat**2) * (lead_time_std**2)
            )
            ss = z_scores * np.sqrt(np.maximum(0.0, variance))

            # Dynamic Reorder Point: ROP = (d_hat * L) + SS
            rop = (d_hat * lead_times.astype(float)) + ss

            # Reorder deficit: Q_raw = max(0, (d_hat * 7) + SS - effective_stock)
            target_level = (d_hat * 7.0) + ss
            reorder_mask = effective_stock <= rop

            # Compute orders
            for s_idx in np.where(reorder_mask)[0]:
                raw_deficit = max(0.0, target_level[s_idx] - effective_stock[s_idx])
                if raw_deficit <= 0.0:
                    continue

                pack_size = pack_sizes[s_idx]
                packs = int(math.ceil(raw_deficit / float(pack_size)))
                q = float(packs * pack_size)

                lt = lead_times[s_idx]
                delivery_day = t + lt

                deliveries_queue.setdefault(delivery_day, []).append((s_idx, q))
                pending_stock[s_idx] += q

                total_orders_placed += 1
                total_units_ordered += int(q)
                total_procurement_cost += q * cost_prices[s_idx]

                # Check Days of Cover & Expedite Alert
                daily_v = d_hat[s_idx]
                doc = current_stock[s_idx] / daily_v if daily_v > 0 else 999.0
                if doc <= lt:
                    critical_expedite_triggers += 1

            # Step 4: Daily Financial Accounting
            closing_units = float(np.sum(current_stock))
            closing_val = float(np.sum(current_stock * cost_prices))
            daily_closing_units_sum += closing_units
            daily_closing_value_sum += closing_val
            peak_inventory_value = max(peak_inventory_value, closing_val)

        total_series_days = total_days * num_series
        stockout_rate = (stockout_incidents / total_series_days) * 100.0 if total_series_days > 0 else 0.0
        fulfillment_rate = (fulfilled_units / total_demand_units) * 100.0 if total_demand_units > 0 else 100.0
        avg_daily_units = daily_closing_units_sum / float(total_days)
        avg_daily_val = daily_closing_value_sum / float(total_days)

        cat_fulfillment_rates = {
            c: (cat_fulfilled[c] / cat_demand[c] * 100.0) if cat_demand[c] > 0 else 100.0
            for c in cat_demand
        }

        return SimulationKPIs(
            policy_name="RemediSync Dynamic Policy",
            total_series_days=total_series_days,
            stockout_incidents=stockout_incidents,
            stockout_days=len(stockout_days_set),
            stockout_rate_pct=stockout_rate,
            total_demand_units=total_demand_units,
            fulfilled_units=fulfilled_units,
            unfulfilled_units=unfulfilled_units,
            fulfillment_rate_pct=fulfillment_rate,
            total_sales_revenue=total_sales_revenue,
            lost_sales_revenue=lost_sales_revenue,
            avg_daily_inventory_units=avg_daily_units,
            avg_daily_inventory_value=avg_daily_val,
            peak_inventory_value=peak_inventory_value,
            total_orders_placed=total_orders_placed,
            total_units_ordered=total_units_ordered,
            total_procurement_cost=total_procurement_cost,
            critical_expedite_triggers=critical_expedite_triggers,
            category_fulfillment=cat_fulfillment_rates,
            category_stockouts=cat_stockouts,
        )

    def run_simulation(
        self,
        start_date: str = "2026-07-01",
        end_date: str = "2026-09-23",
        initial_stock_days: float = 10.0,
    ) -> Dict[str, Any]:
        """Run parallel discrete-event simulation of both policies over test horizon.

        Args:
            start_date: Out-of-time test start date.
            end_date: Out-of-time test end date.
            initial_stock_days: Days of historical baseline demand for starting stock.

        Returns:
            Dictionary with baseline KPIs, remedisync KPIs, and delta comparisons.
        """
        prep = self.prepare_simulation_data(start_date=start_date, end_date=end_date)

        total_days = prep["total_days"]
        num_series = prep["num_series"]
        lead_times = prep["lead_times"]
        pack_sizes = prep["pack_sizes"]
        mrps = prep["mrps"]
        cost_prices = prep["cost_prices"]
        categories = prep["categories"]
        z_scores = prep["z_scores"]
        base_daily = prep["base_daily_demand"]
        demand_matrix = prep["demand_matrix"]
        forecast_matrix = prep["forecast_matrix"]
        sigma_e = prep["sigma_e"]

        # 1. Initialize identical starting inventory for both policies
        initial_stock = np.maximum(
            pack_sizes.astype(float),
            np.ceil(initial_stock_days * base_daily),
        )

        # 2. Run Baseline Static Policy
        kpi_baseline = self._simulate_baseline_policy(
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

        # 3. Run RemediSync ML-Driven Dynamic Policy
        kpi_remedisync = self._simulate_remedisync_policy(
            total_days=total_days,
            num_series=num_series,
            initial_stock=initial_stock,
            demand_matrix=demand_matrix,
            forecast_matrix=forecast_matrix,
            lead_times=lead_times,
            pack_sizes=pack_sizes,
            z_scores=z_scores,
            mrps=mrps,
            cost_prices=cost_prices,
            categories=categories,
            sigma_e=sigma_e,
        )

        # 4. Compute relative improvement deltas: (RemediSync - Baseline) / Baseline
        stockout_delta_pct = (
            ((kpi_remedisync.stockout_incidents - kpi_baseline.stockout_incidents)
            / max(1, kpi_baseline.stockout_incidents))
            * 100.0
        )
        fulfillment_gain_pct = (
            kpi_remedisync.fulfillment_rate_pct - kpi_baseline.fulfillment_rate_pct
        )
        lost_sales_savings_inr = (
            kpi_baseline.lost_sales_revenue - kpi_remedisync.lost_sales_revenue
        )
        capital_delta_pct = (
            ((kpi_remedisync.avg_daily_inventory_value - kpi_baseline.avg_daily_inventory_value)
            / max(1.0, kpi_baseline.avg_daily_inventory_value))
            * 100.0
        )
        expedite_delta_pct = (
            ((kpi_remedisync.critical_expedite_triggers - kpi_baseline.critical_expedite_triggers)
            / max(1, kpi_baseline.critical_expedite_triggers))
            * 100.0
        )

        return {
            "metadata": {
                "start_date": start_date,
                "end_date": end_date,
                "total_days": total_days,
                "num_series": num_series,
                "total_series_days": total_days * num_series,
                "initial_stock_days": initial_stock_days,
                "sigma_e": sigma_e,
            },
            "baseline": kpi_baseline.to_dict(),
            "remedisync": kpi_remedisync.to_dict(),
            "deltas": {
                "stockout_delta_pct": float(round(stockout_delta_pct, 2)),
                "fulfillment_gain_pct": float(round(fulfillment_gain_pct, 2)),
                "lost_sales_savings_inr": float(round(lost_sales_savings_inr, 2)),
                "working_capital_delta_pct": float(round(capital_delta_pct, 2)),
                "expedite_delta_pct": float(round(expedite_delta_pct, 2)),
            },
        }

    def format_scorecard(self, results: Dict[str, Any]) -> str:
        """Format a rich terminal comparison scorecard.

        Args:
            results: Simulation results dictionary from run_simulation().

        Returns:
            Formatted multiline ASCII scorecard string.
        """
        meta = results["metadata"]
        b = results["baseline"]
        r = results["remedisync"]
        d = results["deltas"]

        lines = [
            "=" * 90,
            "               REMEDISYNC: BACKTESTING & POLICY SIMULATION SCORECARD",
            "=" * 90,
            f" Simulation Horizon: {meta['start_date']} to {meta['end_date']} ({meta['total_days']} days | {meta['total_series_days']:,} series-days)",
            f" Scope: {meta['num_series']} series (129 SKUs across 4 Assam Pharmacy Branches)",
            f" Initial Shelf Stock: {meta['initial_stock_days']} days baseline buffer | Residual Sigma_e: {meta['sigma_e']:.2f} units",
            "-" * 90,
            f"{'Operational Metric':<36} | {'Baseline (Min-Max)':<18} | {'RemediSync (ML)':<18} | {'Impact / Delta':<14}",
            "-" * 90,
            f"{'Stockout Incidents':<36} | {b['stockout_incidents']:<18,d} | {r['stockout_incidents']:<18,d} | {d['stockout_delta_pct']:>+6.1f}%",
            f"{'Stockout Days (>=1 incident)':<36} | {b['stockout_days']:<18,d} | {r['stockout_days']:<18,d} | {((r['stockout_days'] - b['stockout_days'])/max(1,b['stockout_days'])*100):>+6.1f}%",
            f"{'Stockout Rate (% series-days)':<36} | {b['stockout_rate_pct']:<17.2f}% | {r['stockout_rate_pct']:<17.2f}% | {(r['stockout_rate_pct'] - b['stockout_rate_pct']):>+6.2f} pp",
            f"{'Prescription Fulfillment Rate':<36} | {b['fulfillment_rate_pct']:<17.2f}% | {r['fulfillment_rate_pct']:<17.2f}% | {d['fulfillment_gain_pct']:>+6.2f} pp",
            f"{'Unfulfilled Lost Sales (Units)':<36} | {b['unfulfilled_units']:<18,.0f} | {r['unfulfilled_units']:<18,.0f} | {((r['unfulfilled_units'] - b['unfulfilled_units'])/max(1.0,b['unfulfilled_units'])*100):>+6.1f}%",
            f"{'Lost Sales Revenue (INR)':<36} | INR {b['lost_sales_revenue']:<14,.0f} | INR {r['lost_sales_revenue']:<14,.0f} | INR {r['lost_sales_revenue'] - b['lost_sales_revenue']:>+9,.0f}",
            f"{'Total Realized Sales (INR)':<36} | INR {b['total_sales_revenue']:<14,.0f} | INR {r['total_sales_revenue']:<14,.0f} | INR {r['total_sales_revenue']-b['total_sales_revenue']:>+9,.0f}",
            f"{'Avg Daily Inventory Value':<36} | INR {b['avg_daily_inventory_value']:<14,.0f} | INR {r['avg_daily_inventory_value']:<14,.0f} | {d['working_capital_delta_pct']:>+6.1f}%",
            f"{'Peak Working Capital Tied':<36} | INR {b['peak_inventory_value']:<14,.0f} | INR {r['peak_inventory_value']:<14,.0f} | {((r['peak_inventory_value']-b['peak_inventory_value'])/max(1.0,b['peak_inventory_value'])*100):>+6.1f}%",
            f"{'Total Purchase Orders Dispatched':<36} | {b['total_orders_placed']:<18,d} | {r['total_orders_placed']:<18,d} | {((r['total_orders_placed']-b['total_orders_placed'])/max(1,b['total_orders_placed'])*100):>+6.1f}%",
            f"{'Total Units Purchased':<36} | {b['total_units_ordered']:<18,d} | {r['total_units_ordered']:<18,d} | {((r['total_units_ordered']-b['total_units_ordered'])/max(1,b['total_units_ordered'])*100):>+6.1f}%",
            f"{'Emergency Expedite Alerts (DoC<=L)':<36} | {b['critical_expedite_triggers']:<18,d} | {r['critical_expedite_triggers']:<18,d} | {d['expedite_delta_pct']:>+6.1f}%",
            "-" * 90,
            " Therapeutic Criticality Tier Breakdown (Prescription Fulfillment):",
        ]

        # Therapeutic category breakdown
        chronic_cats = ["Cardiovascular", "Antidiabetic", "Respiratory", "Endocrine"]
        acute_cats = ["Antibiotic", "Analgesic", "Gastrointestinal", "Antiallergic"]
        otc_cats = ["Nutritional", "Probiotic", "Laxative", "Antacid"]

        def _mean_fulfillment(kpi_dict: Dict[str, Any], cat_group: List[str]) -> float:
            rates = [kpi_dict["category_fulfillment"].get(c, 0.0) for c in cat_group if c in kpi_dict["category_fulfillment"]]
            return float(np.mean(rates)) if rates else 0.0

        b_chronic = _mean_fulfillment(b, chronic_cats)
        r_chronic = _mean_fulfillment(r, chronic_cats)
        b_acute = _mean_fulfillment(b, acute_cats)
        r_acute = _mean_fulfillment(r, acute_cats)
        b_otc = _mean_fulfillment(b, otc_cats)
        r_otc = _mean_fulfillment(r, otc_cats)

        lines.extend([
            f"   * Chronic / Life-Saving (Target >=98%): Baseline {b_chronic:.2f}%  ->  RemediSync {r_chronic:.2f}% ({r_chronic - b_chronic:>+5.2f} pp)",
            f"   * Acute Prescription    (Target >=95%): Baseline {b_acute:.2f}%  ->  RemediSync {r_acute:.2f}% ({r_acute - b_acute:>+5.2f} pp)",
            f"   * Discretionary / OTC   (Target >=90%): Baseline {b_otc:.2f}%  ->  RemediSync {r_otc:.2f}% ({r_otc - b_otc:>+5.2f} pp)",
            "=" * 90,
        ])

        return "\n".join(lines)

    def export_results(
        self,
        results: Dict[str, Any],
        output_path: str = "data/processed/simulation_results.json",
    ) -> Path:
        """Export simulation results and scorecard to JSON file.

        Args:
            results: Simulation results dictionary.
            output_path: Target JSON file path.

        Returns:
            Path to written JSON file.
        """
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        return out_p


def main() -> None:
    """CLI execution entrypoint for policy simulation."""
    print("Initializing RemediSync Discrete-Event Policy Simulator...")
    sim = PolicySimulator()
    print("Executing historical backtest (2026-07-01 to 2026-09-23 across 516 series)...")
    results = sim.run_simulation()
    scorecard = sim.format_scorecard(results)
    print("\n" + scorecard)
    out_file = sim.export_results(results)
    print(f"\n[SUCCESS] Simulation results persisted to: {out_file.resolve()}\n")


if __name__ == "__main__":
    main()
