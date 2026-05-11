#!/usr/bin/env bash
set -euo pipefail

# Local/CI preflight checks before UAT sign-off.
python -m compileall app tests
pytest -q

echo "Preflight checks passed."
