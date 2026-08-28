#!/usr/bin/env bash
# Post-create script for the dev container.
set -euo pipefail

echo "== Installing backend dependencies =="
cd /workspace/backend
pip install -e ".[dev]"

echo "== Installing audio-agent dependencies =="
cd /workspace/audio-agent
pip install -e .

echo "== Running database migrations =="
cd /workspace/backend
alembic upgrade head

echo "== Dev container ready =="
