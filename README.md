# Business Agent MVP

## Quick setup

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
uvicorn app.api.main:app --reload
```

## API endpoints

- `GET /v1/health`
- `GET /v1/metrics`
- `GET /v1/alerts`
- `POST /v1/agent/run`
- `GET /v1/agent/runs/{run_id}`
- `GET /v1/agent/runs/{run_id}/audit`
- `POST /v1/agent/runs/{run_id}/approve`
- `POST /v1/agent/runs/{run_id}/resume`

## Security headers

Provide `x-api-key` and `x-tenant-id`.

### Per-tenant key rotation
Set `TENANT_API_KEYS_JSON` as JSON map:

```json
{
  "tenant-a": {"active_key": "key-1", "next_key": "key-2"}
}
```

## Staging deployment + go-live gate

```bash
docker compose -f docker-compose.staging.yml up --build -d
./scripts/staging_migrate.sh
API_KEY=your-key ./scripts/smoke_staging.sh
TENANT_API_KEYS_JSON='{"tenant-a":{"active_key":"..."},"tenant-b":{"active_key":"..."}}' ./scripts/uat_go_live.sh
./scripts/go_live_gate.sh
```

Complete `UAT_SIGNOFF.md` and review `ROLLBACK_PLAN.md` before production cutover.
