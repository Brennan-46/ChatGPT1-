#!/usr/bin/env bash
set -euo pipefail

# Run alembic migrations against staging DB from docker compose network.
docker compose -f docker-compose.staging.yml run --rm api alembic upgrade head
