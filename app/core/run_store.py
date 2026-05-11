from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class PendingAction:
    run_id: str
    step_id: str
    description: str
    status: str = "pending"


@dataclass
class RunRecord:
    run_id: str
    status: str
    stop_reason: str
    trace: list[str] = field(default_factory=list)


class InMemoryRunStore:
    def __init__(self) -> None:
        self.runs: dict[str, RunRecord] = {}
        self.pending_actions: dict[str, PendingAction] = {}
        self.audit: dict[str, list[str]] = defaultdict(list)

    def upsert_run(self, record: RunRecord) -> None:
        self.runs[record.run_id] = record

    def get_run(self, run_id: str) -> RunRecord | None:
        return self.runs.get(run_id)

    def add_pending_action(self, pending: PendingAction) -> None:
        self.pending_actions[pending.run_id] = pending

    def resolve_pending_action(self, run_id: str, approved: bool) -> PendingAction | None:
        pending = self.pending_actions.get(run_id)
        if not pending:
            return None
        pending.status = "approved" if approved else "denied"
        self.audit[run_id].append(f"approval:{pending.status}")
        return pending
