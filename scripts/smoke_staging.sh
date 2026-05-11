#!/usr/bin/env bash
set -euo pipefail

API_URL=${API_URL:-http://localhost:8000/v1}
API_KEY=${API_KEY:-}
TENANT=${TENANT:-default}

if [[ -z "$API_KEY" ]]; then
  echo "Set API_KEY env var before running smoke tests."
  exit 1
fi

H=( -H "content-type: application/json" -H "x-api-key: $API_KEY" -H "x-tenant-id: $TENANT" )

echo "[1] health"
curl -fsS "$API_URL/health" >/dev/null

echo "[2] destructive run to produce pending approval"
RUN_RESP=$(curl -fsS "${H[@]}" -d '{"user_id":"smoke-user","prompt":"Delete all meetings"}' "$API_URL/agent/run")
RUN_ID=$(python - <<PY
import json
r=json.loads('''$RUN_RESP''')
print(r['run_id'])
PY
)
HASH=$(python - <<PY
import json
r=json.loads('''$RUN_RESP''')
print(r['pending_approval']['action_hash'])
PY
)

echo "[3] approve"
curl -fsS "${H[@]}" -d "{\"approved\":true,\"approver_id\":\"smoke-approver\",\"action_hash\":\"$HASH\"}" "$API_URL/agent/runs/$RUN_ID/approve" >/dev/null

echo "[4] resume"
curl -fsS "${H[@]}" -d '{"user_id":"smoke-user","prompt":"resume"}' "$API_URL/agent/runs/$RUN_ID/resume" >/dev/null

echo "[5] audit"
curl -fsS "${H[@]}" "$API_URL/agent/runs/$RUN_ID/audit" >/dev/null

echo "Smoke tests passed."
