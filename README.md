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

## Run tests

```bash
pytest -q
```
