from datetime import datetime, timedelta, timezone

from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.db import Base


class RunRecord(Base):
    __tablename__ = "agent_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), default="default", index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    stop_reason: Mapped[str] = mapped_column(String(128), nullable=False)
    trace: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PendingAction(Base):
    __tablename__ = "pending_actions"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), default="default", index=True)
    step_id: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    action_hash: Mapped[str] = mapped_column(String(128), default="")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc) + timedelta(hours=1))


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tenant_id: Mapped[str] = mapped_column(String(128), default="default", index=True)
    event: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SQLRunStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_run(self, run_id: str, tenant_id: str, status: str, stop_reason: str, trace: list[str]) -> None:
        record = self.session.get(RunRecord, run_id)
        trace_payload = "|".join(trace)
        if record:
            record.tenant_id = tenant_id
            record.status = status
            record.stop_reason = stop_reason
            record.trace = trace_payload
            record.updated_at = datetime.now(timezone.utc)
        else:
            record = RunRecord(run_id=run_id, tenant_id=tenant_id, status=status, stop_reason=stop_reason, trace=trace_payload)
            self.session.add(record)
        self.session.commit()

    def get_run(self, run_id: str, tenant_id: str) -> RunRecord | None:
        record = self.session.get(RunRecord, run_id)
        if record and record.tenant_id == tenant_id:
            return record
        return None

    def add_pending_action(self, run_id: str, tenant_id: str, step_id: str, description: str, action_hash: str) -> None:
        pending = PendingAction(
            run_id=run_id,
            tenant_id=tenant_id,
            step_id=step_id,
            description=description,
            status="pending",
            action_hash=action_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self.session.merge(pending)
        self.session.commit()

    def resolve_pending_action(self, run_id: str, tenant_id: str, approved: bool, action_hash: str) -> PendingAction | None:
        pending = self.session.get(PendingAction, run_id)
        now = datetime.now(timezone.utc)
        if not pending or pending.tenant_id != tenant_id or pending.action_hash != action_hash or pending.expires_at < now:
            return None
        pending.status = "approved" if approved else "denied"
        self.session.add(AuditEvent(id=f"{run_id}:{pending.status}:{now.timestamp()}", run_id=run_id, tenant_id=tenant_id, event=f"approval:{pending.status}"))
        self.session.commit()
        return pending


    def get_pending_action(self, run_id: str, tenant_id: str) -> PendingAction | None:
        pending = self.session.get(PendingAction, run_id)
        if pending and pending.tenant_id == tenant_id:
            return pending
        return None


    def pending_approval_stats(self, tenant_id: str) -> dict[str, float]:
        rows = self.session.scalars(select(PendingAction).where(PendingAction.tenant_id == tenant_id, PendingAction.status == "pending")).all()
        if not rows:
            return {"count": 0.0, "oldest_age_seconds": 0.0}
        now = datetime.now(timezone.utc)
        oldest = min((now - r.expires_at + timedelta(hours=1)).total_seconds() for r in rows)
        return {"count": float(len(rows)), "oldest_age_seconds": float(max(oldest, 0.0))}

    def list_audit_events(self, run_id: str, tenant_id: str) -> list[str]:
        rows = self.session.scalars(select(AuditEvent).where(AuditEvent.run_id == run_id, AuditEvent.tenant_id == tenant_id)).all()
        return [r.event for r in rows]
