import time
import uuid
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.models import AgentRunRequest, AgentRunResponse, PlanStep
from app.core.policy_engine import approval_context, requires_human_approval
from app.core.run_store import SQLRunStore
from app.core.tool_registry import TOOLS, select_tool
from app.memory.memory import MemoryStore
from app.observability_logging import log_event


@dataclass
class AgentState:
    run_id: str
    trace: list[str] = field(default_factory=list)
    plan: list[PlanStep] = field(default_factory=list)


class AgentCore:
    def __init__(self, run_store: SQLRunStore) -> None:
        self.memory = MemoryStore()
        self.run_store = run_store

    def _plan(self, prompt: str) -> list[PlanStep]:
        risk = "restricted" if any(w in prompt.lower() for w in ["delete", "drop", "remove"]) else "low"
        return [PlanStep(step_id="1", description=prompt, risk=risk)]

    def run(self, request: AgentRunRequest) -> AgentRunResponse:
        run_id = str(uuid.uuid4())
        if settings.agent_kill_switch:
            log_event("run_blocked", run_id=run_id, reason="kill_switch")
            return AgentRunResponse(run_id=run_id, status="blocked", stop_reason="kill_switch", final_answer="Agent execution blocked by kill switch.")

        start = time.time()
        state = AgentState(run_id=run_id)
        state.plan = self._plan(request.prompt)
        state.trace.append("plan_created")

        final_answer = ""
        tool_calls = 0

        for idx, step in enumerate(state.plan):
            if idx >= settings.max_iterations:
                return self._finalize(state, "failed", "max_iterations")
            if time.time() - start > settings.max_runtime_seconds:
                return self._finalize(state, "failed", "timeout")
            if requires_human_approval(step):
                state.trace.append("awaiting_human_approval")
                self.run_store.add_pending_action(run_id=run_id, step_id=step.step_id, description=step.description)
                self.run_store.upsert_run(run_id=run_id, status="awaiting_human_approval", stop_reason="awaiting_human_approval", trace=state.trace.copy())
                return AgentRunResponse(run_id=run_id, status="awaiting_human_approval", stop_reason="awaiting_human_approval", plan=state.plan, trace=state.trace, pending_approval=approval_context(step))

            tool_name = select_tool(step.description)
            if tool_name and tool_name in TOOLS:
                tool_calls += 1
                if tool_calls > settings.max_tool_calls_per_run:
                    return self._finalize(state, "failed", "max_tool_calls")
                final_answer = TOOLS[tool_name]({"request": step.description})
                state.trace.append(f"tool_called:{tool_name}")
            else:
                final_answer = f"Plan step completed without external tools: {step.description}"
                state.trace.append("no_tool_needed")

        self.memory.store_interaction(request.user_id, f"Prompt: {request.prompt}\nAnswer: {final_answer}")
        state.trace.append("memory_stored")
        response = AgentRunResponse(run_id=run_id, status="completed", stop_reason="completed", final_answer=final_answer, plan=state.plan, trace=state.trace)
        self.run_store.upsert_run(run_id=run_id, status=response.status, stop_reason=response.stop_reason, trace=state.trace.copy())
        log_event("run_completed", run_id=run_id, status=response.status)
        return response

    def _finalize(self, state: AgentState, status: str, reason: str) -> AgentRunResponse:
        response = AgentRunResponse(run_id=state.run_id, status=status, stop_reason=reason, plan=state.plan, trace=state.trace)
        self.run_store.upsert_run(run_id=state.run_id, status=status, stop_reason=reason, trace=state.trace.copy())
        log_event("run_stopped", run_id=state.run_id, reason=reason)
        return response
