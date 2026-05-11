from fastapi import APIRouter, Depends, Header

from app.core.db import SessionLocal
from app.core.run_store import SQLRunStore
from app.metrics import snapshot
from app.security import enforce_api_key

router = APIRouter(dependencies=[Depends(enforce_api_key)])


def _tenant(x_tenant_id: str = Header(default="default")) -> str:
    return x_tenant_id or "default"


@router.get('/metrics')
def metrics() -> dict[str, int]:
    return snapshot()


@router.get('/alerts')
def alerts(tenant_id: str = Depends(_tenant)) -> dict:
    with SessionLocal() as session:
        stats = SQLRunStore(session).pending_approval_stats(tenant_id=tenant_id)
    metrics = snapshot()
    alerts_out = []
    if metrics.get('auth_failures_total', 0) > 10:
        alerts_out.append('high_auth_failures')
    if metrics.get('rate_limiter_unavailable_total', 0) > 0:
        alerts_out.append('rate_limiter_unavailable')
    if stats['oldest_age_seconds'] > 900:
        alerts_out.append('stale_pending_approvals')
    return {"alerts": alerts_out, "pending_approval": stats, "metrics": metrics}
