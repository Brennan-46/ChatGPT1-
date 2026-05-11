import json

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.security import enforce_api_key, enforce_rate_limit


def test_tenant_key_rotation_accepts_active_and_next(monkeypatch):
    payload = {
        "tenant-a": {"active_key": "key-1", "next_key": "key-2"}
    }
    monkeypatch.setattr(settings, 'tenant_api_keys_json', json.dumps(payload))

    enforce_api_key(x_api_key='key-1', x_tenant_id='tenant-a')
    enforce_api_key(x_api_key='key-2', x_tenant_id='tenant-a')



def test_tenant_key_rotation_rejects_invalid(monkeypatch):
    payload = {
        "tenant-a": {"active_key": "key-1", "next_key": "key-2"}
    }
    monkeypatch.setattr(settings, 'tenant_api_keys_json', json.dumps(payload))

    with pytest.raises(HTTPException) as exc:
        enforce_api_key(x_api_key='bad-key', x_tenant_id='tenant-a')
    assert exc.value.status_code == 401



def test_rate_limiter_fail_closed_when_redis_unavailable(monkeypatch):
    monkeypatch.setattr(settings, 'rate_limiter_fail_open', False)

    class BrokenPipe:
        def __enter__(self):
            raise RuntimeError('redis unavailable')
        def __exit__(self, exc_type, exc, tb):
            return False

    class BrokenRedis:
        def pipeline(self):
            return BrokenPipe()

    monkeypatch.setattr('app.security._redis_client', BrokenRedis())

    with pytest.raises(HTTPException) as exc:
        enforce_rate_limit('tenant-a:user')
    assert exc.value.status_code == 503
