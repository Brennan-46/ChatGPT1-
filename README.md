# Business Agent MVP

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.api.main:app --reload
```

## API endpoints

- `GET /v1/health`
- `POST /v1/agent/run`
- `GET /v1/agent/runs/{run_id}`
- `GET /v1/agent/runs/{run_id}/audit`
- `POST /v1/agent/runs/{run_id}/approve`

## Production-hardening added in this step

- Database engine now uses configurable `DATABASE_URL` (instead of hardcoded path).
- Added durable audit retrieval endpoint for operator visibility.
- Added Google Calendar integration module scaffold with least-privilege behavior (find/create only, no delete API).

## Run tests

```bash
pytest -q
```


## Google Calendar OAuth user flow

Set `GOOGLE_CALENDAR_CREDENTIALS_JSON` to authorized-user JSON from Google OAuth token exchange and set `GOOGLE_CALENDAR_ID` (default `primary`).
