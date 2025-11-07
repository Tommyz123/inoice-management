#!/bin/bash

# Gunicorn startup script with configurable workers
# Default to 1 worker for Render free tier (512MB RAM)
# Override with GUNICORN_WORKERS environment variable for paid plans

WORKERS=${GUNICORN_WORKERS:-1}
TIMEOUT=${GUNICORN_TIMEOUT:-120}
PORT=${PORT:-8000}

echo "Starting Gunicorn with ${WORKERS} worker(s) on port ${PORT}..."
echo "Timeout: ${TIMEOUT}s"

exec gunicorn \
    --bind 0.0.0.0:${PORT} \
    --workers ${WORKERS} \
    --timeout ${TIMEOUT} \
    --access-logfile - \
    --error-logfile - \
    app:app
