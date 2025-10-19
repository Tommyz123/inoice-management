#!/bin/bash

# Invoice Management System - Production Startup Script for Linux/Mac

echo "========================================"
echo "Invoice Management System"
echo "Starting Production Server..."
echo "========================================"
echo ""

# Check if gunicorn is installed
if ! pip show gunicorn &> /dev/null; then
    echo "[INFO] Gunicorn not found. Installing..."
    pip install gunicorn
    echo ""
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[WARNING] .env file not found!"
    echo "[INFO] Creating default .env file..."
    cat > .env << EOF
SECRET_KEY=change-me-to-random-string
DEBUG=False
USE_SUPABASE_STORAGE=false
DATA_BACKEND=sqlite
EOF
    echo "[INFO] .env file created. Please edit it with your configuration."
    echo ""
fi

# Create uploads directory if it doesn't exist
mkdir -p uploads
chmod 755 uploads

# Get the number of CPU cores
WORKERS=$(($(nproc) * 2 + 1))

echo "[INFO] Starting server on http://0.0.0.0:8000"
echo "[INFO] Workers: $WORKERS"
echo "[INFO] Press Ctrl+C to stop the server"
echo ""

# Start the server
gunicorn --bind 0.0.0.0:8000 \
         --workers $WORKERS \
         --timeout 120 \
         --access-logfile - \
         --error-logfile - \
         app:app
