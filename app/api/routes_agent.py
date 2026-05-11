from fastapi import APIRouter, HTTPException

from app.core.agent_core import AgentCore
from app.core.models import AgentRunRequest, AgentRunResponse, AgentRunStatusResponse, ApprovalRequest
from app.core.run_store import InMemoryRunStore

router = APIRouter()
run_store = InMemoryRunStore()
agent = AgentCore(run_store=run_store)


@router.post("/agent/run", response_model=AgentRunResponse)
def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    return agent.run(request)


@router.get("/agent/runs/{run_id}", response_model=AgentRunStatusResponse)
def run_status(run_id: str) -> AgentRunStatusResponse:
    record = run_store.get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return AgentRunStatusResponse(run_id=record.run_id, status=record.status, stop_reason=record.stop_reason, trace=record.trace)


@router.post("/agent/runs/{run_id}/approve")
def approve(run_id: str, payload: ApprovalRequest) -> dict[str, str]:
    pending = run_store.resolve_pending_action(run_id=run_id, approved=payload.approved)
    if not pending:
        raise HTTPException(status_code=404, detail="Run not awaiting approval")
    return {"run_id": run_id, "decision": pending.status, "approver_id": payload.approver_id}
