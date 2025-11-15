"""FastAPI service powering the MetaboAI MVP."""
from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import ingest, physiology, recommendations
from .models import EstimationRequest, EstimationResult, RecommendationRequest, RecommendationResponse

app = FastAPI(title="MetaboAI MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", summary="Health check")
def health() -> dict[str, str]:
    """Simple health endpoint for deployment checks."""

    return {"status": "ok"}


@app.post("/estimate", response_model=EstimationResult)
def estimate(request: EstimationRequest) -> EstimationResult:
    """Return a substrate utilisation estimate from structured input."""

    return physiology.estimate_substrate(request)


@app.post("/recommendation", response_model=RecommendationResponse)
def recommendation(payload: RecommendationRequest) -> RecommendationResponse:
    """Generate numeric estimates plus coaching language."""

    result = physiology.estimate_substrate(payload.session)
    narrative = recommendations.build_recommendation(payload.session, result, payload.config)
    return RecommendationResponse(estimation=result, recommendation=narrative)


@app.post("/ingest/csv", response_model=EstimationResult)
async def ingest_csv(file: UploadFile = File(...)) -> EstimationResult:
    """Parse a CSV export and return an estimate using defaults."""

    if file.content_type not in {"text/csv", "application/vnd.ms-excel", "application/csv"}:
        raise HTTPException(status_code=415, detail="Unsupported file type; expected CSV export.")

    contents = await file.read()
    decoded = contents.decode("utf-8").splitlines()
    summary = ingest.parse_manual_csv(decoded)
    if summary is None:
        raise HTTPException(status_code=400, detail="Unable to extract heart rate/duration from CSV.")

    request = EstimationRequest(average_hr=summary.average_hr, duration_minutes=summary.duration_minutes)
    return physiology.estimate_substrate(request)

