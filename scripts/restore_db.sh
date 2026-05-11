#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup.sql>"
  exit 1
fi

BACKUP_FILE=$1
if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

docker compose -f docker-compose.staging.yml exec -T postgres psql -U agent -d agent < "$BACKUP_FILE"
echo "Restore complete from $BACKUP_FILE"
