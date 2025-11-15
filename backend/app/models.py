"""Pydantic models for the MetaboAI backend."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, confloat, conint, validator


class ActivityType(str, Enum):
    """Supported activity types for heuristic tuning."""

    RUN = "run"
    RIDE = "ride"
    SWIM = "swim"
    OTHER = "other"


class EstimationRequest(BaseModel):
    """Structured request body for the substrate estimation endpoint."""

    average_hr: conint(gt=0) = Field(..., description="Average heart rate during the session (bpm).")
    duration_minutes: confloat(gt=0) = Field(..., description="Duration of the session in minutes.")
    activity_type: ActivityType = Field(ActivityType.RUN, description="Type of endurance activity performed.")
    body_mass_kg: Optional[confloat(gt=0)] = Field(
        None,
        description="Body mass in kilograms. Used to refine calorie estimation when available.",
    )
    resting_hr: conint(gt=0) = Field(60, description="Resting heart rate (bpm).")
    max_hr: conint(gt=0) = Field(190, description="Estimated max heart rate (bpm).")

    @validator("max_hr")
    def validate_max_hr(cls, value: int, values: dict[str, object]) -> int:
        resting_hr = values.get("resting_hr")
        if resting_hr is not None and value <= resting_hr:
            raise ValueError("max_hr must be greater than resting_hr")
        return value


class EstimationResult(BaseModel):
    """Numeric substrate utilisation estimate for a workout."""

    intensity: float = Field(..., description="Relative intensity on a 0-1 scale based on heart rate reserve.")
    total_kcal: float = Field(..., description="Estimated total kilocalories expended.")
    carbohydrate_grams: float = Field(..., description="Estimated grams of carbohydrate oxidised during the session.")
    fat_grams: float = Field(..., description="Estimated grams of fat oxidised during the session.")


class RecommendationConfig(BaseModel):
    """Optional configuration for the narrative recommendation step."""

    carb_focus: bool = Field(
        False, description="If true, highlight carbohydrate considerations for upcoming key sessions."
    )
    recovery_emphasis: bool = Field(
        False, description="If true, add additional recovery context for the post-session summary."
    )


class Recommendation(BaseModel):
    """Natural language recommendation payload for the client UI."""

    pre_session: str
    during_session: str
    post_session: str
    notes: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Combined numeric and text response for the UI."""

    estimation: EstimationResult
    recommendation: Recommendation


class RecommendationRequest(BaseModel):
    """Request payload for narrative fueling guidance."""

    session: EstimationRequest
    config: RecommendationConfig | None = None

