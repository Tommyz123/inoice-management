# Setup Guide - Invoice Management System

This guide helps you set up the Invoice Management System with OCR support for local development.

## 🚨 Required System Dependencies

The OCR feature requires **Tesseract OCR** and additional libraries to be installed on your system.

---

## 📦 Quick Installation

### Option 1: Automated Installation (Recommended)

Run the installation script:

```bash
chmod +x install_dependencies.sh
./install_dependencies.sh
```

This script automatically:
- Detects your operating system
- Installs Tesseract OCR with language packs
- Installs OpenCV dependencies
- Installs Python dependencies
- Verifies the installation

---

### Option 2: Manual Installation

#### For Ubuntu/Debian

```bash
# Update package list
sudo apt-get update

# Install Tesseract OCR and language packs
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra

# Install OpenCV dependencies
sudo apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev

# Install Python dependencies
pip install -r requirements.txt
```

#### For macOS

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Tesseract with all language packs
brew install tesseract tesseract-lang

# Install Python dependencies
pip install -r requirements.txt
```

#### For Windows

1. Download Tesseract installer from:
   https://github.com/UB-Mannheim/tesseract/wiki

2. During installation, make sure to select:
   - English language pack
   - Chinese (Simplified) language pack
   - Chinese (Traditional) language pack

3. Add Tesseract to PATH:
   - Default location: `C:\Program Files\Tesseract-OCR`
   - Add to System Environment Variables

4. Install Python dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

---

## ✅ Verify Installation

After installation, verify everything is working:

```bash
# Check Tesseract version
tesseract --version

# List available languages (should show eng, chi_sim, chi_tra)
tesseract --list-langs

# Test Python imports
python3 -c "import pytesseract, cv2, PIL, numpy; print('✅ All imports successful!')"
```

---

## 🐳 Docker Installation (Alternative)

If you prefer Docker, no manual installation is needed:

```bash
# Build the Docker image
docker-compose build

# Run the application
docker-compose up
```

All dependencies are automatically installed in the Docker container.

---

## 🧪 Test OCR Functionality

After installation, test the OCR feature:

1. Start the application:
   ```bash
   python3 app.py
   ```

2. Open browser: `http://localhost:5000`

3. Upload a test invoice (PDF or image)

4. Check if OCR auto-fills the fields

---

## 🔧 Troubleshooting

### Issue: "tesseract not found"

**Solution:**
- Make sure Tesseract is in your PATH
- On Linux/Mac: `which tesseract`
- On Windows: Check Environment Variables

### Issue: "Cannot process image files: pytesseract library not installed"

**Solution:**
```bash
pip install pytesseract Pillow opencv-python-headless numpy
```

### Issue: "TesseractNotFoundError"

**Solution:**
- Reinstall Tesseract OCR
- Set TESSERACT_CMD environment variable:
  ```bash
  export TESSERACT_CMD=/usr/bin/tesseract  # Linux/Mac
  set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe  # Windows
  ```

### Issue: OCR accuracy is poor

**Solutions:**
1. Make sure Chinese language packs are installed:
   ```bash
   tesseract --list-langs | grep chi
   ```
   Should show: `chi_sim` and `chi_tra`

2. Ensure image quality is good (300+ DPI recommended)

3. Check if OpenCV is installed:
   ```bash
   python3 -c "import cv2; print(cv2.__version__)"
   ```

### Issue: "ImportError: libGL.so.1"

**Solution (Ubuntu/Debian):**
```bash
sudo apt-get install libgl1-mesa-glx
```

---

## 📋 Required Python Packages

From `requirements.txt`:

```txt
Flask>=3.0.0
PyMuPDF>=1.23.0
SQLAlchemy>=2.0.0
supabase>=2.0.0
python-dotenv>=1.0.0
psycopg[binary]>=3.1.0
Werkzeug>=3.0.0
gunicorn>=21.2.0
requests>=2.31.0
pytesseract>=0.3.10      # OCR wrapper
Pillow>=10.0.0           # Image handling
opencv-python-headless>=4.8.0  # Image preprocessing
numpy>=1.24.0            # Array operations
```

---

## 🌐 Language Support

Currently supported OCR languages:
- **English** (eng)
- **Chinese Simplified** (chi_sim) - 简体中文
- **Chinese Traditional** (chi_tra) - 繁體中文

To add more languages:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr-[lang]
```

**macOS:**
```bash
brew install tesseract-lang
```

Available languages: https://github.com/tesseract-ocr/tessdata

---

## 🎯 Next Steps

After successful installation:

1. ✅ Configure environment variables (optional):
   - Copy `.env.example` to `.env`
   - Set `SECRET_KEY`, database settings, etc.

2. ✅ Initialize database:
   ```bash
   python3 app.py  # Auto-creates database on first run
   ```

3. ✅ Upload test invoices to verify OCR

4. ✅ Deploy to production (Docker recommended)

---

## 📞 Support

If you encounter issues:
1. Check this guide's troubleshooting section
2. Review `OCR_IMPROVEMENTS.md` for technical details
3. Open an issue on GitHub with error logs

---

## ✨ Success!

Once everything is installed, you should see:
- ✅ Tesseract OCR working
- ✅ Python dependencies imported
- ✅ OCR auto-filling invoice fields
- ✅ Image preprocessing improving accuracy

Enjoy the enhanced OCR capabilities! 🚀
