#!/usr/bin/env bash
# Run Alembic database migrations inside the backend container.
set -euo pipefail

COMPOSE="docker compose"
if [ -f compose.yml ] || [ -f docker-compose.yml ]; then
  COMPOSE="docker compose"
fi

${COMPOSE} exec backend alembic upgrade head
