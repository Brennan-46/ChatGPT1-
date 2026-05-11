#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=${1:-./backups}
mkdir -p "$BACKUP_DIR"
TS=$(date -u +"%Y%m%dT%H%M%SZ")
OUT="$BACKUP_DIR/agent_${TS}.sql"

docker compose -f docker-compose.staging.yml exec -T postgres pg_dump -U agent -d agent > "$OUT"
echo "Backup written to $OUT"
