from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_run_agent_low_risk_completes():
    response = client.post('/v1/agent/run', json={'user_id': 'u1', 'prompt': 'Schedule a meeting next week'})
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'completed'


def test_run_agent_delete_requires_approval_and_audit():
    response = client.post('/v1/agent/run', json={'user_id': 'u1', 'prompt': 'Delete all meetings'})
    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'awaiting_human_approval'
    assert body['pending_approval'] is not None

    approval = client.post(f"/v1/agent/runs/{body['run_id']}/approve", json={'approved': False, 'approver_id': 'manager-1', 'action_hash': body['pending_approval']['action_hash']})
    assert approval.status_code == 200
    assert approval.json()['decision'] == 'denied'

    audit = client.get(f"/v1/agent/runs/{body['run_id']}/audit")
    assert audit.status_code == 200
    assert any(event == 'approval:denied' for event in audit.json()['events'])
