from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.core.run_store import SQLRunStore


def test_tenant_isolation_for_run_reads():
    engine = create_engine('sqlite:///:memory:', future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as session:
        store = SQLRunStore(session)
        store.upsert_run('run-tenant', 'tenant-a', 'completed', 'completed', ['ok'])
        assert store.get_run('run-tenant', tenant_id='tenant-a') is not None
        assert store.get_run('run-tenant', tenant_id='tenant-b') is None
