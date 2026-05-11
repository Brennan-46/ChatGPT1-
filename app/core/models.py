from typing import Any, Literal
from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    user_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)


class ApprovalRequest(BaseModel):
    approved: bool
    approver_id: str = Field(min_length=1)
    action_hash: str = Field(min_length=1)


class PlanStep(BaseModel):
    step_id: str
    description: str
    risk: Literal["low", "medium", "high", "restricted"] = "low"


class AgentRunResponse(BaseModel):
    run_id: str
    status: Literal["completed", "in_progress", "awaiting_human_approval", "failed", "blocked"]
    stop_reason: str
    final_answer: str | None = None
    plan: list[PlanStep] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)
    pending_approval: dict[str, Any] | None = None


class AgentRunStatusResponse(BaseModel):
    run_id: str
    status: str
    stop_reason: str
    trace: list[str] = Field(default_factory=list)


class AuditEventsResponse(BaseModel):
    run_id: str
    events: list[str] = Field(default_factory=list)
