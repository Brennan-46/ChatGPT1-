# Release Checklist (Phase 1)

## Safety & Policy
- [ ] Destructive actions require HITL and valid action hash.
- [ ] Pending approvals expire and cannot be replayed.
- [ ] API key auth enabled in target environment.

## Integrations
- [ ] Google Calendar OAuth credentials configured.
- [ ] Slack bot token configured with least privilege.
- [ ] Circuit-breaker and retry behavior validated in staging.

## Data & Persistence
- [ ] Alembic migrations applied in staging (`./scripts/staging_migrate.sh`).
- [ ] Tenant isolation checks pass.
- [ ] Backup and restore procedure validated (`./scripts/backup_db.sh`, `./scripts/restore_db.sh`).

## Observability
- [ ] `/v1/metrics` returns runtime counters.
- [ ] Correlation ID propagated in responses.
- [ ] Structured logs available in log pipeline.

## Validation
- [ ] `python -m compileall app tests` succeeds.
- [ ] `pytest -q` succeeds in CI.
- [ ] Staging smoke test passes (`./scripts/smoke_staging.sh`).
- [ ] UAT multi-tenant run passes (`./scripts/uat_go_live.sh`).

## Go-Live Gate
- [ ] `UAT_SIGNOFF.md` completed and approved.
- [ ] `ROLLBACK_PLAN.md` reviewed by on-call engineer.
- [ ] Release tag frozen and deployment window approved.
