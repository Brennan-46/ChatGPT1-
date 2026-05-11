#!/usr/bin/env bash
set -euo pipefail

API_URL=${API_URL:-http://localhost:8000/v1}
TENANTS=${TENANTS:-tenant-a,tenant-b}
USERS=${USERS:-uat-user-a,uat-user-b}
API_KEYS_JSON=${TENANT_API_KEYS_JSON:-}

if [[ -z "$API_KEYS_JSON" ]]; then
  echo "TENANT_API_KEYS_JSON must be set with active keys for all tenants."
  exit 1
fi

python - <<'PY'
import json, os, sys, subprocess
api = os.environ.get('API_URL', 'http://localhost:8000/v1')
tenants = [t.strip() for t in os.environ.get('TENANTS','tenant-a,tenant-b').split(',') if t.strip()]
users = [u.strip() for u in os.environ.get('USERS','uat-user-a,uat-user-b').split(',') if u.strip()]
keys = json.loads(os.environ['TENANT_API_KEYS_JSON'])

def req(method, path, tenant, key, payload=None):
    cmd = ['curl','-fsS','-X',method,
           '-H','content-type: application/json',
           '-H',f'x-tenant-id: {tenant}',
           '-H',f'x-api-key: {key}',
           f'{api}{path}']
    if payload is not None:
        cmd.extend(['-d', json.dumps(payload)])
    out = subprocess.check_output(cmd).decode()
    return json.loads(out) if out.strip().startswith('{') else out

for i, tenant in enumerate(tenants):
    user = users[i % len(users)]
    key = keys[tenant]['active_key']
    # health/metrics check
    req('GET','/metrics',tenant,key)

    # calendar smoke (real OAuth creds must be configured in env)
    cal = req('POST','/agent/run',tenant,key,{'user_id':user,'prompt':'Schedule a 30 minute meeting tomorrow'})
    assert cal['status'] in ('completed','awaiting_human_approval')

    # slack smoke (real token must be configured in env)
    msg = req('POST','/agent/run',tenant,key,{'user_id':user,'prompt':'Send slack message: UAT ping'})
    assert msg['status'] in ('completed','awaiting_human_approval')

    # destructive HITL full cycle
    run = req('POST','/agent/run',tenant,key,{'user_id':user,'prompt':'Delete all meetings'})
    assert run['status'] == 'awaiting_human_approval'
    run_id = run['run_id']
    action_hash = run['pending_approval']['action_hash']

    req('POST',f'/agent/runs/{run_id}/approve',tenant,key,{
        'approved': True,
        'approver_id': f'{user}-approver',
        'action_hash': action_hash,
    })

    resumed = req('POST',f'/agent/runs/{run_id}/resume',tenant,key,{'user_id':user,'prompt':'resume'})
    assert resumed['status'] in ('completed','awaiting_human_approval')

    audit = req('GET',f'/agent/runs/{run_id}/audit',tenant,key)
    assert 'events' in audit

print('UAT go-live script completed successfully across tenants.')
PY
