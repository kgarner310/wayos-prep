#!/bin/bash
set -o pipefail

echo "=== WAYOS PREP STARTUP ==="
echo "PORT=${PORT:-8000}"
echo "APP_ENV=${APP_ENV:-development}"
echo "DATABASE_URL configured: $([ -n "$DATABASE_URL" ] && echo 'yes' || echo 'no')"
echo "REDIS_URL configured: $([ -n "$REDIS_URL" ] && echo 'yes' || echo 'no')"
echo "CORS_ORIGINS=${CORS_ORIGINS:-not set}"

# Test DB connectivity before migrations
if [ -n "$DATABASE_URL" ]; then
  DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|.*@([^:/]+).*|\1|')
  echo "Database host: $DB_HOST"

  # DNS resolution check (helps debug Railway internal networking)
  if command -v getent &>/dev/null; then
    echo "DNS resolution for $DB_HOST:"
    getent ahostsv4 "$DB_HOST" 2>&1 | head -1 || echo "  IPv4 DNS lookup failed for $DB_HOST"
    getent ahostsv6 "$DB_HOST" 2>&1 | head -1 || echo "  IPv6 DNS lookup failed for $DB_HOST"
  fi

  # Quick TCP connectivity test
  if command -v timeout &>/dev/null; then
    DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|.*:([0-9]+)/.*|\1|')
    echo "Testing TCP connection to $DB_HOST:${DB_PORT:-5432}..."
    timeout 5 bash -c "echo > /dev/tcp/$DB_HOST/${DB_PORT:-5432}" 2>&1 && echo "  TCP connection OK" || echo "  TCP connection FAILED"
  fi
fi

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
