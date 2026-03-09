#!/bin/bash
set -e
python -c "from app.workers.settings import WorkerSettings; WorkerSettings.configure(); import arq; arq.run_worker(WorkerSettings)"
