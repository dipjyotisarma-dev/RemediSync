"""
Demand Modeling Engine for RemediSync.

Computes mathematical daily customer demand distributions per [date, branch, medicine]
incorporating:
- Day-of-week seasonality (Monday clinic surges, weekend spikes)
- Early-month payday refill cycles (1st-7th of month for chronic meds)
- Seasonal disease waves (Monsoon water-borne/viral and winter respiratory peaks)
- Branch demographic personality weights
- Loose tablet fractional sales conversions
"""

import numpy as np
from datetime import date
from typing import Dict, Any


def get_day_of_week_multiplier(dt: date) -> float:
    """Returns demand multiplier based on weekday.

    Monday (0) has highest clinic re-opening rush (+25%).
    Saturday (5) has weekend family footfall (+15%).
    Sunday (6) is relatively slower (0.85).
    """
    weekday = dt.weekday()
    multipliers = {
        0: 1.25,  # Monday
        1: 1.05,  # Tuesday
        2: 0.98,  # Wednesday
        3: 0.96,  # Thursday
        4: 1.02,  # Friday
        5: 1.15,  # Saturday
        6: 0.85   # Sunday
    }
    return multipliers.get(weekday, 1.0)


def get_payday_multiplier(dt: date, is_chronic: bool) -> float:
    """Returns demand multiplier for 1st-7th of the month.

    Chronic medicines (Diabetes, BP, Heart, Thyroid) experience a massive
    +30% refill spike when salaries and pensions are disbursed.
    """
    if 1 <= dt.day <= 7:
        return 1.30 if is_chronic else 1.05
    return 1.0


def get_seasonal_multiplier(dt: date, category: str) -> float:
    """Returns seasonal multiplier based on month and therapeutic category.

    - Monsoon (June-August): Surges in Gastrointestinal, Antibiotics, Antipyretics (dengue, water-borne).
    - Winter (November-February): Surges in Respiratory, Cough/Cold, Antiallergics.
    """
    month = dt.month

    # Monsoon season (June - August)
    if month in (6, 7, 8):
        if category in ("Gastrointestinal", "Antibiotic"):
            return 1.30
        if category in ("Antipyretic", "Analgesic"):
            return 1.20

    # Winter season (November - February)
    if month in (11, 12, 1, 2):
        if category in ("Respiratory", "Antiallergic"):
            return 1.35
        if category in ("Antipyretic", "Analgesic"):
            return 1.15

    return 1.0


def compute_expected_daily_demand(
    dt: date,
    branch: Dict[str, Any],
    medicine: Dict[str, Any]
) -> float:
    """Computes the continuous parameter lambda for daily customer demand.

    Lambda = BaseDemand * BranchFactor * DayOfWeekFactor * PaydayFactor * SeasonFactor
    """
    base_demand = float(medicine.get("base_daily_demand", 10.0))
    is_chronic = medicine.get("velocity_class") == "CHRONIC"
    category = medicine.get("category", "")

    # Branch profile weighting
    branch_factor = float(branch.get("chronic_factor" if is_chronic else "acute_factor", 1.0))

    dow_factor = get_day_of_week_multiplier(dt)
    payday_factor = get_payday_multiplier(dt, is_chronic)
    season_factor = get_seasonal_multiplier(dt, category)

    # Scale factor (0.23) calibrates the ~130 SKU catalog so that individual branch
    # daily revenue lands squarely in the authentic INR 50,000 (normal) to INR 65,000-70,000 (peak) range.
    catalog_scale = 0.23

    lambda_demand = base_demand * catalog_scale * branch_factor * dow_factor * payday_factor * season_factor
    return max(0.05, lambda_demand)


def sample_realized_demand(
    lambda_demand: float,
    units_per_pack: int,
    rng: np.random.Generator
) -> float:
    """Samples realized daily customer demand in packs (including loose tablet fractions).

    Uses Poisson distribution for discrete pack demand, with optional random loose tablet
    purchases added as fractional packs.
    """
    integer_packs = int(rng.poisson(lambda_demand))

    # Loose tablets fraction (only applies to blister packs with units_per_pack > 1)
    fractional_packs = 0.0
    if units_per_pack > 1:
        # 30% chance customers buy loose tablets on that day
        if rng.random() < 0.30:
            loose_tablets = rng.integers(1, min(units_per_pack, 6))
            fractional_packs = round(float(loose_tablets) / float(units_per_pack), 2)

    total_demand = float(integer_packs) + fractional_packs
    return round(total_demand, 2)
