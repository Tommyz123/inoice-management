#!/bin/bash

# Installation script for Invoice Management System dependencies
# This script installs Tesseract OCR and other system dependencies

set -e

echo "=========================================="
echo "Invoice Management System - Dependency Installer"
echo "=========================================="
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/debian_version ]; then
        OS="debian"
    elif [ -f /etc/redhat-release ]; then
        OS="redhat"
    else
        OS="linux"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    OS="unknown"
fi

echo "Detected OS: $OS"
echo ""

# Install based on OS
case $OS in
    debian)
        echo "Installing dependencies for Debian/Ubuntu..."
        sudo apt-get update
        sudo apt-get install -y \
            tesseract-ocr \
            tesseract-ocr-eng \
            tesseract-ocr-chi-sim \
            tesseract-ocr-chi-tra \
            libgl1-mesa-glx \
            libglib2.0-0 \
            libsm6 \
            libxext6 \
            libxrender-dev \
            python3-pip \
            python3-venv
        echo "✅ System dependencies installed successfully!"
        ;;

    redhat)
        echo "Installing dependencies for RedHat/CentOS/Fedora..."
        sudo dnf install -y tesseract tesseract-langpack-eng tesseract-langpack-chi_sim tesseract-langpack-chi_tra mesa-libGL glib2
        echo "✅ System dependencies installed successfully!"
        ;;

    macos)
        echo "Installing dependencies for macOS..."
        if ! command -v brew &> /dev/null; then
            echo "❌ Homebrew not found. Please install Homebrew first:"
            echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
        brew install tesseract tesseract-lang
        echo "✅ System dependencies installed successfully!"
        ;;

    *)
        echo "❌ Unsupported operating system: $OSTYPE"
        echo ""
        echo "Please install Tesseract OCR manually:"
        echo "  - Tesseract OCR: https://github.com/tesseract-ocr/tesseract"
        echo "  - Language packs: eng, chi_sim, chi_tra"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Installing Python dependencies..."
echo "=========================================="
echo ""

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    echo "✅ Python dependencies installed successfully!"
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

echo ""
echo "=========================================="
echo "Verifying installation..."
echo "=========================================="
echo ""

# Verify Tesseract
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract version:"
    tesseract --version | head -1
    echo ""
    echo "✅ Available languages:"
    tesseract --list-langs 2>&1 | grep -E "(eng|chi_sim|chi_tra)"
else
    echo "❌ Tesseract not found in PATH"
    exit 1
fi

echo ""

# Test Python imports
python3 -c "
import sys
try:
    import pytesseract
    print('✅ pytesseract imported successfully')
except ImportError as e:
    print(f'❌ pytesseract import failed: {e}')
    sys.exit(1)

try:
    import cv2
    print('✅ opencv-python imported successfully')
except ImportError as e:
    print(f'❌ opencv-python import failed: {e}')
    sys.exit(1)

try:
    import PIL
    print('✅ Pillow imported successfully')
except ImportError as e:
    print(f'❌ Pillow import failed: {e}')
    sys.exit(1)

try:
    import numpy
    print('✅ numpy imported successfully')
except ImportError as e:
    print(f'❌ numpy import failed: {e}')
    sys.exit(1)
"

echo ""
echo "=========================================="
echo "✅ All dependencies installed successfully!"
echo "=========================================="
echo ""
echo "You can now run the application:"
echo "  python3 app.py"
echo ""
echo "Or with Docker:"
echo "  docker-compose up"
echo ""
