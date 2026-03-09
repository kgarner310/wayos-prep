#!/bin/bash
set -o pipefail

echo "=== WAYOS PREP STARTUP ==="
echo "PORT=${PORT:-8000}"
echo "APP_ENV=${APP_ENV:-development}"
echo "DATABASE_URL configured: $([ -n "$DATABASE_URL" ] && echo 'yes' || echo 'no')"
echo "REDIS_URL configured: $([ -n "$REDIS_URL" ] && echo 'yes' || echo 'no')"

# Only run migrations/seeding if DATABASE_URL is explicitly set (not the localhost default)
if [ -n "$DATABASE_URL" ] && echo "$DATABASE_URL" | grep -qv "localhost"; then
  echo "Running database migrations..."
  if alembic upgrade head 2>&1; then
    echo "Migrations complete."
  else
    echo "WARNING: Migrations failed — app will start without them."
  fi

  echo "Seeding data..."
  if python seed_data.py 2>&1; then
    echo "Seeding complete."
  else
    echo "WARNING: Seeding failed — app will start without seed data."
  fi
else
  echo "Skipping migrations — DATABASE_URL not configured for remote database."
fi

echo "Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
