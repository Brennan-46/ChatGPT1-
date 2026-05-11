#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR=${REPORT_DIR:-./reports}
mkdir -p "$REPORT_DIR"
TS=$(date -u +"%Y%m%dT%H%M%SZ")
REPORT="$REPORT_DIR/go_live_gate_${TS}.md"

exec > >(tee "$REPORT")
exec 2>&1

echo "# Go-Live Gate Report"
echo
echo "Timestamp (UTC): $TS"
echo

echo "## 1) Staging migrate"
./scripts/staging_migrate.sh

echo "## 2) Staging smoke"
./scripts/smoke_staging.sh

echo "## 3) Multi-tenant UAT"
./scripts/uat_go_live.sh

echo "## 4) Backup validation"
./scripts/backup_db.sh ./backups

echo "## 5) Checklist pointers"
echo "- Complete UAT_SIGNOFF.md"
echo "- Review ROLLBACK_PLAN.md"
echo "- Mark RELEASE_CHECKLIST.md items"

echo
echo "Go-live gate completed successfully."
echo "Report: $REPORT"
