from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.db import Base


class RunRecord(Base):
    __tablename__ = "agent_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    stop_reason: Mapped[str] = mapped_column(String(128), nullable=False)
    trace: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PendingAction(Base):
    __tablename__ = "pending_actions"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    step_id: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SQLRunStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_run(self, run_id: str, status: str, stop_reason: str, trace: list[str]) -> None:
        record = self.session.get(RunRecord, run_id)
        trace_payload = "|".join(trace)
        if record:
            record.status = status
            record.stop_reason = stop_reason
            record.trace = trace_payload
            record.updated_at = datetime.now(timezone.utc)
        else:
            record = RunRecord(run_id=run_id, status=status, stop_reason=stop_reason, trace=trace_payload)
            self.session.add(record)
        self.session.commit()

    def get_run(self, run_id: str) -> RunRecord | None:
        return self.session.get(RunRecord, run_id)

    def add_pending_action(self, run_id: str, step_id: str, description: str) -> None:
        pending = PendingAction(run_id=run_id, step_id=step_id, description=description, status="pending")
        self.session.merge(pending)
        self.session.commit()

    def resolve_pending_action(self, run_id: str, approved: bool) -> PendingAction | None:
        pending = self.session.get(PendingAction, run_id)
        if not pending:
            return None
        pending.status = "approved" if approved else "denied"
        self.session.add(AuditEvent(id=f"{run_id}:{pending.status}:{datetime.now(timezone.utc).timestamp()}", run_id=run_id, event=f"approval:{pending.status}"))
        self.session.commit()
        return pending

    def list_audit_events(self, run_id: str) -> list[str]:
        rows = self.session.scalars(select(AuditEvent).where(AuditEvent.run_id == run_id)).all()
        return [r.event for r in rows]
