# Dockerfile for Invoice Management System
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OCR and image processing
# Minimal dependencies for Render compatibility
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download English language data for Tesseract manually
# This ensures eng.traineddata is available even if tesseract-ocr-eng package doesn't exist
RUN mkdir -p /usr/share/tesseract-ocr/4.00/tessdata && \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata \
         -O /usr/share/tesseract-ocr/4.00/tessdata/eng.traineddata || \
    wget -q https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata \
         -O /usr/share/tesseract-ocr/5/tessdata/eng.traineddata || \
    echo "Warning: Could not download eng.traineddata"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy application files
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Create uploads directory
RUN mkdir -p uploads && chmod 755 uploads

# Expose port
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Run with gunicorn via start script
# Default: 1 worker for Render free tier (512MB RAM)
# Override with GUNICORN_WORKERS environment variable for paid plans
CMD ["./start.sh"]
