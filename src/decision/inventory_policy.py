"""Deterministic retail pharmacy inventory policy calculator.

Implements standard supply chain operations research formulas: service level
z-score mapping, dynamic safety stock sizing, reorder point thresholds,
days of inventory cover, pack-size ceiling rounding, and plain-English rationale.
"""

import math
from typing import Dict, Tuple


class InventoryPolicy:
    """Operational inventory control policy and replenishment arithmetic engine."""

    # Cycle Service Level (CSL) Z-score mappings by clinical category criticality
    SERVICE_LEVEL_Z_SCORES: Dict[str, float] = {
        "CRITICAL": 2.05,  # 98.0% CSL: Cardiovascular, Antidiabetic, Respiratory
        "ACUTE": 1.65,  # 95.0% CSL: Antibiotic, Analgesic, Gastrointestinal
        "DISCRETIONARY": 1.28,  # 90.0% CSL: Nutritional, OTC, Antacid, Topical
    }

    # Clinical category criticality classification
    CATEGORY_CRITICALITY_MAP: Dict[str, str] = {
        # Life-saving / Chronic prescription therapeutics (98% CSL)
        "Cardiovascular": "CRITICAL",
        "Antidiabetic": "CRITICAL",
        "Respiratory": "CRITICAL",
        "Endocrine": "CRITICAL",
        # Acute clinical prescription medications (95% CSL)
        "Antibiotic": "ACUTE",
        "Analgesic": "ACUTE",
        "Antipyretic": "ACUTE",
        "Gastrointestinal": "ACUTE",
        "Antiallergic": "ACUTE",
        "Antiemetic": "ACUTE",
        "Antispasmodic": "ACUTE",
        "Antifungal": "ACUTE",
        "Antigout": "ACUTE",
        "Ophthalmic": "ACUTE",
        "Hepatoprotective": "ACUTE",
        # Discretionary OTC & Supplements (90% CSL)
        "Nutritional": "DISCRETIONARY",
        "Probiotic": "DISCRETIONARY",
        "Laxative": "DISCRETIONARY",
        "Antiseptic": "DISCRETIONARY",
    }

    @classmethod
    def get_service_level_z(cls, category: str) -> float:
        """Resolve cycle service level Z-score for a given therapeutic category.

        Args:
            category: Therapeutic drug category name.

        Returns:
            Z-score corresponding to target service level.
        """
        tier = cls.CATEGORY_CRITICALITY_MAP.get(category, "ACUTE")
        return cls.SERVICE_LEVEL_Z_SCORES[tier]

    @classmethod
    def calculate_safety_stock(
        cls,
        daily_demand: float,
        lead_time_days: float,
        sigma_e: float,
        category: str,
        lead_time_std: float = 0.25,
    ) -> float:
        """Calculate dynamic safety stock protecting against demand and lead-time variance.

        Formula: SS = Z * sqrt(L * sigma_e^2 + D_hat^2 * sigma_L^2)

        Args:
            daily_demand: Forecasted average daily customer demand (units).
            lead_time_days: Expected supplier replenishment lead time in days (L).
            sigma_e: Standard deviation of forecast error (units).
            category: Therapeutic drug category for CSL Z-score mapping.
            lead_time_std: Standard deviation of distributor lead time in days (sigma_L).

        Returns:
            Calibrated safety stock buffer (float units).
        """
        if daily_demand < 0:
            raise ValueError("daily_demand must be non-negative.")
        if lead_time_days < 0:
            raise ValueError("lead_time_days must be non-negative.")
        if sigma_e < 0:
            raise ValueError("sigma_e must be non-negative.")

        z = cls.get_service_level_z(category)
        variance = (lead_time_days * (sigma_e**2)) + ((daily_demand**2) * (lead_time_std**2))
        return float(z * math.sqrt(max(0.0, variance)))

    @classmethod
    def calculate_reorder_point(
        cls,
        daily_demand: float,
        lead_time_days: float,
        safety_stock: float,
    ) -> float:
        """Calculate Reorder Point (ROP) threshold.

        Formula: ROP = (D_hat * L) + SS

        Args:
            daily_demand: Forecasted average daily customer demand.
            lead_time_days: Expected supplier replenishment lead time.
            safety_stock: Calibrated safety stock buffer.

        Returns:
            Reorder point inventory threshold.
        """
        lead_time_demand = max(0.0, daily_demand) * max(0.0, lead_time_days)
        return float(lead_time_demand + max(0.0, safety_stock))

    @classmethod
    def calculate_days_of_cover(
        cls,
        current_stock: float,
        daily_demand: float,
    ) -> float:
        """Calculate remaining days of inventory cover on hand before physical stockout.

        Args:
            current_stock: Physical stock on hand.
            daily_demand: Expected daily customer demand velocity.

        Returns:
            Days of cover (float). Returns 999.0 if demand is zero and stock > 0.
        """
        if daily_demand <= 0.0:
            return 999.0 if current_stock > 0 else 0.0
        return float(max(0.0, current_stock) / daily_demand)

    @classmethod
    def classify_urgency(
        cls,
        current_stock: float,
        pending_order: float,
        rop: float,
        days_of_cover: float,
        lead_time_days: float,
    ) -> str:
        """Classify operational replenishment urgency into one of 4 standard tiers.

        - CRITICAL: Physical stockout expected before shipment can arrive (DoC <= Lead Time).
        - REORDER: Total effective inventory (S + P) is at or below ROP.
        - HEALTHY: Effective stock above ROP and cover within optimal operating band.
        - OVERSTOCKED: Inventory cover exceeds 21 days or stock > 3 * ROP.

        Args:
            current_stock: Units currently on shelf (S).
            pending_order: Units in-transit from supplier (P).
            rop: Calibrated reorder point threshold.
            days_of_cover: Days until physical shelf reaches zero.
            lead_time_days: Supplier delivery lead time in days.

        Returns:
            Urgency string ('CRITICAL', 'REORDER', 'HEALTHY', or 'OVERSTOCKED').
        """
        effective_stock = current_stock + pending_order

        # 1. Critical: Stockout will occur before distributor shipment can arrive
        if current_stock <= 0.0 or days_of_cover <= lead_time_days:
            return "CRITICAL"

        # 2. Reorder: Effective inventory breached the reorder point
        if effective_stock <= rop:
            return "REORDER"

        # 3. Overstocked: Working capital trapped (> 21 days cover or > 3x ROP)
        if days_of_cover > 21.0 or (rop > 0 and current_stock > (3.0 * rop)):
            return "OVERSTOCKED"

        # 4. Healthy: Operating normally within optimal buffer cover
        return "HEALTHY"

    @classmethod
    def calculate_reorder_quantity(
        cls,
        daily_demand: float,
        safety_stock: float,
        current_stock: float,
        pending_order: float,
        units_per_pack: int,
        rop: float,
        review_period_days: float = 7.0,
    ) -> Tuple[int, int]:
        """Compute recommended purchase order quantity rounded to commercial manufacturer pack sizes.

        Formula:
            If (S + P) > ROP: Q = 0
            Else: Q_raw = max(0, (D_hat * T) + SS - (S + P))
            Q_units = ceil(Q_raw / B_size) * B_size
            Q_packs = Q_units / B_size

        Args:
            daily_demand: Forecasted daily demand velocity.
            safety_stock: Calibrated safety buffer.
            current_stock: Physical stock on hand (S).
            pending_order: In-transit pending stock (P).
            units_per_pack: Commercial pack size (B_size, e.g. 10 or 15 tablets/pack).
            rop: Reorder point threshold.
            review_period_days: Periodic review horizon (T, default 7 days).

        Returns:
            Tuple of (order_units, order_packs). Both are integers >= 0.
        """
        effective_stock = current_stock + pending_order
        pack_size = max(1, units_per_pack)

        # If effective stock is above ROP, no purchase order is triggered
        if effective_stock > rop:
            return 0, 0

        target_level = (daily_demand * review_period_days) + safety_stock
        raw_deficit = max(0.0, target_level - effective_stock)

        if raw_deficit <= 0.0:
            return 0, 0

        # Round up to whole commercial shipper packs
        packs = math.ceil(raw_deficit / pack_size)
        units = packs * pack_size
        return int(units), int(packs)

    @classmethod
    def generate_rationale(
        cls,
        brand_name: str,
        current_stock: int,
        days_of_cover: float,
        lead_time_days: float,
        predicted_7d_demand: float,
        safety_stock: int,
        rop: int,
        order_units: int,
        order_packs: int,
        urgency: str,
        pending_order: int = 0,
    ) -> str:
        """Formulate a transparent, plain-English explanation for floor pharmacists.

        Args:
            brand_name: Commercial trade name of medicine.
            current_stock: Units currently on shelf.
            days_of_cover: Days until physical stockout.
            lead_time_days: Supplier delivery turnaround.
            predicted_7d_demand: 7-day cumulative forecasted demand.
            safety_stock: Buffer units.
            rop: Reorder point threshold.
            order_units: Recommended units to purchase.
            order_packs: Recommended packs to purchase.
            urgency: Classified operational urgency.
            pending_order: Incoming units already in transit.

        Returns:
            Concise, human-readable explanatory sentence.
        """
        gap = max(0.0, lead_time_days - days_of_cover)

        if urgency == "CRITICAL":
            if pending_order > 0 and order_packs == 0:
                return (
                    f"{brand_name}: Current stock ({current_stock} units) covers only {days_of_cover:.1f} days, "
                    f"but supplier shipment ({lead_time_days:.1f}d lead) has {pending_order} units in transit. "
                    f"Expedite incoming delivery to avoid {gap:.1f}-day stockout gap."
                )
            return (
                f"{brand_name}: Current stock ({current_stock} units) covers only {days_of_cover:.1f} days; "
                f"supplier takes {lead_time_days:.1f} days to deliver (stockout gap: {gap:.1f} days). "
                f"Reorder {order_packs} packs ({order_units} units) immediately."
            )

        if urgency == "REORDER":
            return (
                f"{brand_name}: Effective stock on hand ({current_stock} units) breached ROP ({rop} units). "
                f"Predicted 7-day demand is {predicted_7d_demand:.1f} units with {safety_stock} units safety buffer. "
                f"Reorder {order_packs} packs ({order_units} units)."
            )

        if urgency == "OVERSTOCKED":
            return (
                f"{brand_name}: Shelf stock ({current_stock} units) provides {days_of_cover:.1f} days of cover "
                f"(exceeds 21-day ceiling). Do not reorder; preserve working capital."
            )

        # HEALTHY
        return (
            f"{brand_name}: Stock level ({current_stock} units) is healthy with {days_of_cover:.1f} days of cover "
            f"(above ROP {rop} units). No reorder required today."
        )
