from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.db import Base
from app.core.run_store import SQLRunStore


def test_run_store_persists_run_and_audit_entries():
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as session:  # type: Session
        store = SQLRunStore(session)
        store.upsert_run('run-1', 'tenant-a', 'completed', 'completed', ['a', 'b'])
        record = store.get_run('run-1', tenant_id='tenant-a')
        assert record is not None
        assert record.status == 'completed'
        assert record.trace == 'a|b'

        store.add_pending_action('run-2', 'tenant-a', 'step-1', 'delete something')
        pending = store.resolve_pending_action('run-2', tenant_id='tenant-a', approved=False)
        assert pending is not None
        assert pending.status == 'denied'

        events = store.list_audit_events('run-2', tenant_id='tenant-a')
        assert 'approval:denied' in events
