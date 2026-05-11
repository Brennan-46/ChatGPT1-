from fastapi import APIRouter, HTTPException

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

router = APIRouter()


@router.post("/agent/run", response_model=AgentRunResponse)
def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    with SessionLocal() as session:
        return AgentCore(run_store=SQLRunStore(session)).run(request)


@router.get("/agent/runs/{run_id}", response_model=AgentRunStatusResponse)
def run_status(run_id: str) -> AgentRunStatusResponse:
    with SessionLocal() as session:
        store = SQLRunStore(session)
        record = store.get_run(run_id)
        if not record:
            raise HTTPException(status_code=404, detail="Run not found")
        trace = record.trace.split("|") if record.trace else []
        return AgentRunStatusResponse(run_id=record.run_id, status=record.status, stop_reason=record.stop_reason, trace=trace)


@router.get("/agent/runs/{run_id}/audit", response_model=AuditEventsResponse)
def run_audit(run_id: str) -> AuditEventsResponse:
    with SessionLocal() as session:
        store = SQLRunStore(session)
        record = store.get_run(run_id)
        if not record:
            raise HTTPException(status_code=404, detail="Run not found")
        return AuditEventsResponse(run_id=run_id, events=store.list_audit_events(run_id))


@router.post("/agent/runs/{run_id}/approve")
def approve(run_id: str, payload: ApprovalRequest) -> dict[str, str]:
    with SessionLocal() as session:
        pending = SQLRunStore(session).resolve_pending_action(run_id=run_id, approved=payload.approved)
        if not pending:
            raise HTTPException(status_code=404, detail="Run not awaiting approval")
        return {"run_id": run_id, "decision": pending.status, "approver_id": payload.approver_id}
