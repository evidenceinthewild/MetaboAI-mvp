"""Utilities for ingesting simple CSV workout exports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import csv


@dataclass
class WorkoutSummary:
    """Lightweight summary extracted from a workout file."""

    average_hr: float
    duration_minutes: float


def parse_manual_csv(data: Iterable[str]) -> Optional[WorkoutSummary]:
    """Parse a Garmin-style CSV export to average HR and duration."""

    reader = csv.DictReader(data)
    hr_keys = ("heart_rate", "HeartRate", "AverageHeartRate", "avg_hr")
    elapsed_keys = ("elapsed_time", "seconds", "elapsed", "total_elapsed_time")

    hr_values: list[float] = []
    elapsed_seconds = 0.0

    for row in reader:
        hr_value: Optional[float] = None
        for key in hr_keys:
            try:
                raw = row.get(key)
                if raw is None:
                    continue
                hr_value = float(raw)
                break
            except (TypeError, ValueError):
                continue

        if hr_value is None:
            continue
        hr_values.append(hr_value)

        for key in elapsed_keys:
            try:
                raw = row.get(key)
                if raw is None:
                    continue
                elapsed_seconds = max(elapsed_seconds, float(raw))
                break
            except (TypeError, ValueError):
                continue

    if not hr_values or elapsed_seconds <= 0:
        return None

    avg_hr = sum(hr_values) / len(hr_values)
    duration_minutes = elapsed_seconds / 60.0
    return WorkoutSummary(average_hr=avg_hr, duration_minutes=duration_minutes)

