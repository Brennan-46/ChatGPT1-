from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import settings


client = TestClient(app)


def test_agent_run_requires_api_key_when_configured(monkeypatch):
    monkeypatch.setattr(settings, 'api_key', 'secret-key')

    unauthorized = client.post('/v1/agent/run', json={'user_id': 'u1', 'prompt': 'Schedule a meeting'})
    assert unauthorized.status_code == 401

    authorized = client.post(
        '/v1/agent/run',
        json={'user_id': 'u1', 'prompt': 'Schedule a meeting'},
        headers={'x-api-key': 'secret-key'},
    )
    assert authorized.status_code == 200
    body = authorized.json()
    assert {'run_id', 'status', 'stop_reason', 'trace'}.issubset(set(body.keys()))


def test_run_status_and_audit_contract(monkeypatch):
    monkeypatch.setattr(settings, 'api_key', 'secret-key')
    response = client.post(
        '/v1/agent/run',
        json={'user_id': 'u2', 'prompt': 'Delete all meetings'},
        headers={'x-api-key': 'secret-key'},
    )
    assert response.status_code == 200
    run_id = response.json()['run_id']

    status = client.get(f'/v1/agent/runs/{run_id}', headers={'x-api-key': 'secret-key'})
    assert status.status_code == 200
    assert {'run_id', 'status', 'stop_reason', 'trace'}.issubset(set(status.json().keys()))

    audit = client.get(f'/v1/agent/runs/{run_id}/audit', headers={'x-api-key': 'secret-key'})
    assert audit.status_code == 200
    assert {'run_id', 'events'}.issubset(set(audit.json().keys()))
