from fastapi.testclient import TestClient

from app.api.main import app
from app.core.config import settings


client = TestClient(app)


def test_resume_requires_prior_approval(monkeypatch):
    monkeypatch.setattr(settings, 'api_key', 'secret-key')

    run = client.post(
        '/v1/agent/run',
        json={'user_id': 'u3', 'prompt': 'Delete all meetings'},
        headers={'x-api-key': 'secret-key'},
    )
    assert run.status_code == 200
    body = run.json()

    # resume before approval should fail
    resume = client.post(
        f"/v1/agent/runs/{body['run_id']}/resume",
        json={'user_id': 'u3', 'prompt': 'resume'},
        headers={'x-api-key': 'secret-key'},
    )
    assert resume.status_code == 200
    assert resume.json()['stop_reason'] == 'not_approved'


def test_resume_after_approval(monkeypatch):
    monkeypatch.setattr(settings, 'api_key', 'secret-key')

    run = client.post(
        '/v1/agent/run',
        json={'user_id': 'u4', 'prompt': 'Delete all meetings'},
        headers={'x-api-key': 'secret-key'},
    )
    body = run.json()

    approve = client.post(
        f"/v1/agent/runs/{body['run_id']}/approve",
        json={
            'approved': True,
            'approver_id': 'approver-1',
            'action_hash': body['pending_approval']['action_hash'],
        },
        headers={'x-api-key': 'secret-key'},
    )
    assert approve.status_code == 200

    resume = client.post(
        f"/v1/agent/runs/{body['run_id']}/resume",
        json={'user_id': 'u4', 'prompt': 'resume'},
        headers={'x-api-key': 'secret-key'},
    )
    assert resume.status_code == 200
    assert resume.json()['status'] in {'completed', 'awaiting_human_approval'}
