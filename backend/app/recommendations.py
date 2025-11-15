"""Generate friendly fueling recommendations based on estimation results."""
from __future__ import annotations

from datetime import timedelta

from .models import EstimationRequest, EstimationResult, Recommendation, RecommendationConfig


def _format_duration(minutes: float) -> str:
    duration = timedelta(minutes=float(minutes))
    total_minutes = int(duration.total_seconds() // 60)
    hours, minutes_part = divmod(total_minutes, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes_part}m")
    return " ".join(parts)


def _carb_range(grams: float, intensity: float) -> tuple[int, int]:
    base = grams
    low = max(20, int(base * (0.7 if intensity < 0.7 else 0.85)))
    high = int(base * (1.1 if intensity < 0.8 else 1.25))
    return low, max(low + 5, high)


def build_recommendation(
    request: EstimationRequest,
    estimation: EstimationResult,
    config: RecommendationConfig | None = None,
) -> Recommendation:
    """Convert numeric results into session-specific fueling guidance."""

    config = config or RecommendationConfig()

    duration_text = _format_duration(request.duration_minutes)
    carb_low, carb_high = _carb_range(estimation.carbohydrate_grams, estimation.intensity)

    pre_session = (
        f"Aim for {int(carb_low * 0.3)}-{int(carb_high * 0.35)} g of carbs 1-2 h pre-session "
        f"to top up glycogen before this {duration_text} workout."
    )

    mid_session = (
        f"Carry {carb_low}-{carb_high} g of carbohydrate to cover the planned workload. "
        "Sip fluids regularly, adding electrolytes if the session is longer than 75 minutes."
    )

    post_session = (
        f"Refuel within 45 min with {int(estimation.carbohydrate_grams)} g carbs and "
        f"{int(estimation.carbohydrate_grams * 0.25)} g protein. "
        "Pair carbs with a lean protein source to speed up recovery."
    )

    notes_parts: list[str] = []
    if estimation.intensity >= 0.85:
        notes_parts.append(
            "High intensity detected — ensure last night's dinner included starch and consider a recovery shake."
        )
    if config.recovery_emphasis:
        notes_parts.append("Prioritize sleep and a balanced meal with colorful veg to support adaptation.")
    if config.carb_focus and estimation.carbohydrate_grams > 120:
        notes_parts.append("Consider a gel every 20 min to stay ahead of carb demand.")

    notes = " ".join(notes_parts) or None

    return Recommendation(pre_session=pre_session, during_session=mid_session, post_session=post_session, notes=notes)

