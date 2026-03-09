#!/bin/bash

echo "Running database migrations..."
if alembic upgrade head; then
  echo "Migrations complete."
else
  echo "WARNING: Migrations failed — app will start without them."
fi

echo "Seeding data..."
if python seed_data.py; then
  echo "Seeding complete."
else
  echo "WARNING: Seeding failed — app will start without seed data."
fi

exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
