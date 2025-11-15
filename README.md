# MetaboAI MVP

MetaboAI is an AI-assisted metabolic training companion for endurance athletes. The MVP
showcases a narrow end-to-end loop:

1. Ingest a workout (manual form or Garmin CSV export)
2. Estimate carbohydrate and fat usage using a physiology heuristic
3. Deliver plain-English fueling guidance across pre/during/post windows

## Project structure

```
backend/
  app/
    main.py            # FastAPI entrypoint
    physiology.py      # Heart-rate based substrate estimation heuristics
    recommendations.py # Narrative fueling guidance builder
    ingest.py          # CSV parsing helper for manual exports
frontend/
  index.html           # Lightweight UI for manual entry + file uploads
requirements.txt
```

## Getting started

Install dependencies and run the API locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload
```

Open the frontend (e.g. using VS Code Live Server or `python -m http.server`) and submit data via
`http://localhost:8000`. The UI automatically targets localhost when running from a local machine.

## API overview

### `POST /estimate`

Accepts an `EstimationRequest` payload:

```json
{
  "average_hr": 152,
  "duration_minutes": 68,
  "activity_type": "run",
  "body_mass_kg": 63,
  "resting_hr": 55,
  "max_hr": 188
}
```

Returns estimated intensity, kcal, carbohydrate grams, and fat grams.

### `POST /recommendation`

Wraps the estimation output with narrative fueling guidance. Optional `RecommendationConfig` flags
can emphasise carbohydrate focus or recovery notes. The request body nests the session data under a
`session` key:

```json
{
  "session": {
    "average_hr": 160,
    "duration_minutes": 75,
    "activity_type": "ride",
    "resting_hr": 55,
    "max_hr": 190
  }
}
```

### `POST /ingest/csv`

Accepts a Garmin-style CSV upload containing `heart_rate` and `elapsed_time` columns and returns an
`EstimationResult` using default athlete parameters.

## Testing

Run the test suite with:

```bash
pytest
```

## Syncing to your own Git remote

The project history already contains all application files (backend FastAPI service, frontend UI,
tests, and local Pydantic shim). To publish them to your own repository, point this working tree at
your remote and push:

```bash
git remote add origin <your-remote-url>
git push -u origin work
```

If you prefer a different branch name, replace `work` in the commands above. After pushing, all
directories shown in this README (`backend/`, `frontend/`, `tests/`, etc.) will be visible in your
hosted repository.

