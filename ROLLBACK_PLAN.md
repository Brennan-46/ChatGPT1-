# Rollback Plan

## Triggers
- Elevated auth failures, rate-limiter outages, or persistent 5xx errors.
- Broken HITL flow (approve/resume mismatch).
- Integration provider outage causing sustained business impact.

## Immediate Actions
1. Freeze incoming automation by setting `AGENT_KILL_SWITCH=true`.
2. Route traffic to previous stable release image/tag.
3. Disable new tenant API key rotation set and restore prior active keys.

## Database Rollback
1. Restore latest known-good PostgreSQL backup:
   - `./scripts/restore_db.sh ./backups/<good_backup>.sql`
2. Re-apply schema at stable target if required via Alembic.

## Verification
1. Run `./scripts/smoke_staging.sh`.
2. Validate `/v1/health`, `/v1/metrics`, `/v1/alerts`.
3. Run one HITL cycle and confirm audit visibility.

## Communication
- Publish incident summary and rollback status to ops channel.
- Record root cause and corrective action in postmortem.
