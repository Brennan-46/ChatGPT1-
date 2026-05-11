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
- `POST /v1/agent/runs/{run_id}/approve`

## What changed in this step

- Persisted run status and pending approvals in SQLite (`data/agent.db`) via SQLAlchemy.
- Added audit-event persistence for approval decisions.
- Kept HITL policy gate for destructive verbs.

## Run tests

```bash
pytest -q
```
