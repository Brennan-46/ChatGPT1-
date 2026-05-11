from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.agent_core import AgentCore
from app.core.db import SessionLocal
from app.core.models import (
    AgentRunRequest,
    AgentRunResponse,
    AgentRunStatusResponse,
    ApprovalRequest,
    AuditEventsResponse,
)
from app.core.run_store import SQLRunStore
from app.security import enforce_api_key, enforce_rate_limit

router = APIRouter(dependencies=[Depends(enforce_api_key)])


def _tenant(x_tenant_id: str = Header(default="default")) -> str:
    return x_tenant_id or "default"


@router.post("/agent/run", response_model=AgentRunResponse)
def run_agent(request: AgentRunRequest, tenant_id: str = Depends(_tenant)) -> AgentRunResponse:
    enforce_rate_limit(f"{tenant_id}:{request.user_id}")
    with SessionLocal() as session:
        return AgentCore(run_store=SQLRunStore(session)).run(request, tenant_id=tenant_id)


@router.get("/agent/runs/{run_id}", response_model=AgentRunStatusResponse)
def run_status(run_id: str, tenant_id: str = Depends(_tenant)) -> AgentRunStatusResponse:
    enforce_rate_limit(f"{tenant_id}:run-status:{run_id}")
    with SessionLocal() as session:
        store = SQLRunStore(session)
        record = store.get_run(run_id, tenant_id=tenant_id)
        if not record:
            raise HTTPException(status_code=404, detail="Run not found")
        trace = record.trace.split("|") if record.trace else []
        return AgentRunStatusResponse(run_id=record.run_id, status=record.status, stop_reason=record.stop_reason, trace=trace)


@router.get("/agent/runs/{run_id}/audit", response_model=AuditEventsResponse)
def run_audit(run_id: str, tenant_id: str = Depends(_tenant)) -> AuditEventsResponse:
    enforce_rate_limit(f"{tenant_id}:run-audit:{run_id}")
    with SessionLocal() as session:
        store = SQLRunStore(session)
        record = store.get_run(run_id, tenant_id=tenant_id)
        if not record:
            raise HTTPException(status_code=404, detail="Run not found")
        return AuditEventsResponse(run_id=run_id, events=store.list_audit_events(run_id, tenant_id=tenant_id))


@router.post("/agent/runs/{run_id}/approve")
def approve(run_id: str, payload: ApprovalRequest, tenant_id: str = Depends(_tenant)) -> dict[str, str]:
    enforce_rate_limit(f"{tenant_id}:{payload.approver_id}")
    with SessionLocal() as session:
        pending = SQLRunStore(session).resolve_pending_action(
            run_id=run_id,
            tenant_id=tenant_id,
            approved=payload.approved,
            action_hash=payload.action_hash,
        )
        if not pending:
            raise HTTPException(status_code=404, detail="Run not awaiting approval")
        return {"run_id": run_id, "decision": pending.status, "approver_id": payload.approver_id}


@router.post("/agent/runs/{run_id}/resume", response_model=AgentRunResponse)
def resume(run_id: str, request: AgentRunRequest, tenant_id: str = Depends(_tenant)) -> AgentRunResponse:
    enforce_rate_limit(f"{tenant_id}:{request.user_id}:resume")
    with SessionLocal() as session:
        return AgentCore(run_store=SQLRunStore(session)).resume_approved_action(run_id=run_id, user_id=request.user_id, tenant_id=tenant_id)
