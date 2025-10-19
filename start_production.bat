@echo off
REM Invoice Management System - Production Startup Script for Windows

echo ========================================
echo Invoice Management System
echo Starting Production Server...
echo ========================================
echo.

REM Check if waitress is installed
pip show waitress >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Waitress not found. Installing...
    pip install waitress
    echo.
)

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found!
    echo [INFO] Creating default .env file...
    (
        echo SECRET_KEY=change-me-to-random-string
        echo DEBUG=False
        echo USE_SUPABASE_STORAGE=false
        echo DATA_BACKEND=sqlite
    ) > .env
    echo [INFO] .env file created. Please edit it with your configuration.
    echo.
)

REM Create uploads directory if it doesn't exist
if not exist uploads mkdir uploads

echo [INFO] Starting server on http://0.0.0.0:8000
echo [INFO] Press Ctrl+C to stop the server
echo.

REM Start the server
waitress-serve --host=0.0.0.0 --port=8000 --threads=4 app:app
