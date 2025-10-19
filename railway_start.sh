#!/bin/bash

echo "=== Railway Deployment Starting ==="
echo "Python version:"
python --version

echo ""
echo "Environment variables:"
echo "PORT: $PORT"
echo "SECRET_KEY: ${SECRET_KEY:0:10}... (hidden)"
echo "DATA_BACKEND: $DATA_BACKEND"

echo ""
echo "=== Starting Gunicorn ==="
exec gunicorn --bind 0.0.0.0:$PORT \
  --workers 1 \
  --threads 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  --preload \
  app:app
