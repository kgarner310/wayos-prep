#!/bin/bash
set -e
alembic upgrade head
python seed_data.py
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
