import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.core.models import AgentRunRequest, AgentRunResponse, PlanStep
from app.core.policy_engine import approval_context, requires_human_approval
from app.core.run_store import SQLRunStore
from app.core.tool_registry import TOOLS, select_tool
from app.memory.memory import MemoryStore
from app.observability_logging import log_event


class GraphState(TypedDict):
    step: PlanStep
    final_answer: str
    trace: list[str]
    status: str
    stop_reason: str


@dataclass
class AgentState:
    run_id: str
    trace: list[str] = field(default_factory=list)
    plan: list[PlanStep] = field(default_factory=list)


class AgentCore:
    def __init__(self, run_store: SQLRunStore) -> None:
        self.memory = MemoryStore()
        self.run_store = run_store
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(GraphState)
        graph.add_node("plan", self._graph_plan)
        graph.add_node("act", self._graph_act)
        graph.add_node("reflect", self._graph_reflect)
        graph.set_entry_point("plan")
        graph.add_edge("plan", "act")
        graph.add_edge("act", "reflect")
        graph.add_edge("reflect", END)
        return graph.compile()

    def _plan(self, prompt: str) -> list[PlanStep]:
        chunks = [c.strip() for c in prompt.split(" and ") if c.strip()]
        plan: list[PlanStep] = []
        for i, chunk in enumerate(chunks or [prompt], start=1):
            risk = "restricted" if any(w in chunk.lower() for w in ["delete", "drop", "remove"]) else "low"
            plan.append(PlanStep(step_id=str(i), description=chunk, risk=risk))
        return plan

    def _graph_plan(self, state: GraphState) -> GraphState:
        state["trace"].append("plan_created")
        return state

    def _graph_act(self, state: GraphState) -> GraphState:
        step = state["step"]
        if requires_human_approval(step):
            state["trace"].append("awaiting_human_approval")
            state["status"] = "awaiting_human_approval"
            state["stop_reason"] = "awaiting_human_approval"
            return state
        tool_name = select_tool(step.description)
        if tool_name and tool_name in TOOLS:
            state["final_answer"] = TOOLS[tool_name]({"request": step.description})
            state["trace"].append(f"tool_called:{tool_name}")
        else:
            state["final_answer"] = f"Plan step completed without external tools: {step.description}"
            state["trace"].append("no_tool_needed")
        state["status"] = "completed"
        state["stop_reason"] = "completed"
        return state

    def _graph_reflect(self, state: GraphState) -> GraphState:
        state["trace"].append("reflect_checked")
        return state

    def run(self, request: AgentRunRequest, tenant_id: str = "default") -> AgentRunResponse:
        run_id = str(uuid.uuid4())
        return self._execute_plan(run_id, request.user_id, self._plan(request.prompt), tenant_id)

    def resume_approved_action(self, run_id: str, user_id: str, tenant_id: str = "default") -> AgentRunResponse:
        pending = self.run_store.get_pending_action(run_id=run_id, tenant_id=tenant_id)
        if not pending or pending.status != "approved":
            return AgentRunResponse(run_id=run_id, status="failed", stop_reason="not_approved", final_answer="No approved pending action to resume.")
        step = PlanStep(step_id=pending.step_id, description=pending.description, risk="low")
        return self._execute_plan(run_id, user_id, [step], tenant_id, allow_reapproval=False)

    def _execute_plan(self, run_id: str, user_id: str, plan: list[PlanStep], tenant_id: str, allow_reapproval: bool = True) -> AgentRunResponse:
        if settings.agent_kill_switch:
            log_event("run_blocked", run_id=run_id, reason="kill_switch")
            return AgentRunResponse(run_id=run_id, status="blocked", stop_reason="kill_switch", final_answer="Agent execution blocked by kill switch.")

        start = time.time()
        state = AgentState(run_id=run_id, plan=plan)
        retrieved_context = self.memory.retrieve(user_id, " ".join([p.description for p in plan]), top_k=2)
        if retrieved_context:
            state.trace.append("memory_retrieved")

        graph_state: GraphState = {"step": state.plan[0], "final_answer": "", "trace": state.trace, "status": "in_progress", "stop_reason": ""}
        answers: list[str] = []
        for step in state.plan:
            graph_state["step"] = step
            result = self.graph.invoke(graph_state)
            state.trace = result["trace"]
            if time.time() - start > settings.max_runtime_seconds:
                return self._finalize(state, tenant_id, "failed", "timeout")
            if allow_reapproval and result["status"] == "awaiting_human_approval":
                action_hash = hashlib.sha256(f"{step.step_id}:{step.description}".encode()).hexdigest()
                self.run_store.add_pending_action(run_id=run_id, tenant_id=tenant_id, step_id=step.step_id, description=step.description, action_hash=action_hash)
                self.run_store.upsert_run(run_id=run_id, tenant_id=tenant_id, status="awaiting_human_approval", stop_reason="awaiting_human_approval", trace=state.trace.copy())
                context = approval_context(step)
                context["action_hash"] = action_hash
                return AgentRunResponse(run_id=run_id, status="awaiting_human_approval", stop_reason="awaiting_human_approval", plan=state.plan, trace=state.trace, pending_approval=context)
            answers.append(result["final_answer"])

        final_answer = "\n".join([a for a in answers if a])
        if retrieved_context:
            final_answer = f"{final_answer}\n\nRelevant memory:\n{' | '.join(retrieved_context)}"
        self.memory.store_interaction(user_id, f"Prompt: {' and '.join([p.description for p in plan])}\nAnswer: {final_answer}")
        state.trace.append("memory_stored")
        response = AgentRunResponse(run_id=run_id, status="completed", stop_reason="completed", final_answer=final_answer, plan=state.plan, trace=state.trace)
        self.run_store.upsert_run(run_id=run_id, tenant_id=tenant_id, status=response.status, stop_reason=response.stop_reason, trace=state.trace.copy())
        return response

    def _finalize(self, state: AgentState, tenant_id: str, status: str, reason: str) -> AgentRunResponse:
        response = AgentRunResponse(run_id=state.run_id, status=status, stop_reason=reason, plan=state.plan, trace=state.trace)
        self.run_store.upsert_run(run_id=state.run_id, tenant_id=tenant_id, status=status, stop_reason=reason, trace=state.trace.copy())
        log_event("run_stopped", run_id=state.run_id, reason=reason)
        return response
