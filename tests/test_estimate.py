from pytest import approx

from backend.app.ingest import parse_manual_csv
from backend.app.models import EstimationRequest
from backend.app.physiology import estimate_substrate
from backend.app.recommendations import build_recommendation


def test_estimate_substrate_returns_positive_values():
    request = EstimationRequest(
        average_hr=150,
        duration_minutes=60,
        activity_type="run",
        body_mass_kg=65,
        resting_hr=55,
        max_hr=190,
    )
    result = estimate_substrate(request)
    assert 0 <= result.intensity <= 1.1
    assert result.total_kcal > 0
    assert result.carbohydrate_grams > 0
    assert result.fat_grams > 0


def test_recommendation_includes_all_fields():
    request = EstimationRequest(
        average_hr=160,
        duration_minutes=75,
        activity_type="ride",
        resting_hr=55,
        max_hr=190,
    )
    estimation = estimate_substrate(request)
    rec = build_recommendation(request, estimation)
    assert rec.pre_session
    assert rec.during_session
    assert rec.post_session


def test_parse_manual_csv_handles_basic_export(tmp_path):
    csv_content = """elapsed_time,heart_rate
0,100
60,120
120,130
"""
    csv_path = tmp_path / "workout.csv"
    csv_path.write_text(csv_content)

    summary = parse_manual_csv(csv_path.read_text().splitlines())
    assert summary is not None
    assert summary.average_hr == approx(116.6667, rel=1e-4)
    assert summary.duration_minutes == approx(2)
