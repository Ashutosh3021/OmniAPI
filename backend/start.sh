#!/bin/bash
# Start the API server.
#
# The Celery workers are separate processes on purpose: they are deployed as
# their own services (see render.yaml and docker-compose.yml) so a slow
# webhook endpoint cannot compete with the API for CPU or memory. Starting
# them here as well would run two workers on the same queue.
set -e

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
