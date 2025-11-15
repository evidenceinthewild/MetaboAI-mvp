"""Heuristic physiology model for substrate utilisation estimates."""
from __future__ import annotations

from typing import Tuple

from .models import ActivityType, EstimationRequest, EstimationResult


# Activity-specific adjustment factors tuned for heuristic realism.
_ACTIVITY_ENERGY_FACTORS = {
    ActivityType.RUN: 1.0,
    ActivityType.RIDE: 0.9,
    ActivityType.SWIM: 1.05,
    ActivityType.OTHER: 0.85,
}


def _heart_rate_reserve_fraction(request: EstimationRequest) -> float:
    """Calculate intensity as a fraction of heart rate reserve."""

    reserve = max(request.max_hr - request.resting_hr, 1)
    relative_intensity = (request.average_hr - request.resting_hr) / reserve
    return max(0.0, min(relative_intensity, 1.1))


def _energy_burn_rate(intensity: float, activity: ActivityType, body_mass_kg: float | None) -> float:
    """Estimate calories per minute using a simple zone-based curve."""

    base_factor = _ACTIVITY_ENERGY_FACTORS.get(activity, 0.9)

    # Baseline metabolic cost in kcal/min.
    base_kcal = 3.5 * base_factor

    # Intensity curve: low intensity = mostly fat, moderate/high increases carbs.
    if intensity < 0.55:
        multiplier = 3.0
    elif intensity < 0.7:
        multiplier = 6.0
    elif intensity < 0.85:
        multiplier = 9.0
    else:
        multiplier = 11.0

    # Adjust for athlete size when available.
    size_factor = 1.0
    if body_mass_kg:
        size_factor = body_mass_kg / 70.0

    return base_kcal + multiplier * intensity * base_factor * size_factor


def _substrate_split(intensity: float) -> Tuple[float, float]:
    """Return (carb_fraction, fat_fraction) based on intensity."""

    if intensity < 0.5:
        return 0.35, 0.65
    if intensity < 0.65:
        return 0.5, 0.5
    if intensity < 0.8:
        return 0.65, 0.35
    if intensity < 0.95:
        return 0.8, 0.2
    return 0.9, 0.1


def estimate_substrate(request: EstimationRequest) -> EstimationResult:
    """Compute a coarse substrate utilisation estimate for a workout."""

    intensity = _heart_rate_reserve_fraction(request)
    kcal_per_min = _energy_burn_rate(intensity, request.activity_type, request.body_mass_kg)
    total_kcal = kcal_per_min * request.duration_minutes

    carb_fraction, fat_fraction = _substrate_split(intensity)
    carb_grams = (total_kcal * carb_fraction) / 4.0
    fat_grams = (total_kcal * fat_fraction) / 9.0

    return EstimationResult(
        intensity=round(float(intensity), 3),
        total_kcal=round(float(total_kcal), 1),
        carbohydrate_grams=round(float(carb_grams), 1),
        fat_grams=round(float(fat_grams), 1),
    )

