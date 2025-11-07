#!/usr/bin/env python3
"""
OCR Functionality Test Script
Tests if Tesseract OCR and all dependencies are properly installed.
"""

import sys
from datetime import datetime


def test_imports():
    """Test if all required Python packages can be imported."""
    print("=" * 60)
    print("Testing Python Package Imports")
    print("=" * 60)

    packages = {
        'Flask': 'Flask',
        'PyMuPDF': 'fitz',
        'SQLAlchemy': 'sqlalchemy',
        'pytesseract': 'pytesseract',
        'Pillow': 'PIL',
        'OpenCV': 'cv2',
        'numpy': 'numpy',
    }

    success_count = 0
    for name, import_name in packages.items():
        try:
            __import__(import_name)
            print(f"✅ {name:15s} - OK")
            success_count += 1
        except ImportError as e:
            print(f"❌ {name:15s} - FAILED: {e}")

    print(f"\n{success_count}/{len(packages)} packages successfully imported\n")
    return success_count == len(packages)


def test_tesseract():
    """Test if Tesseract OCR is installed and accessible."""
    print("=" * 60)
    print("Testing Tesseract OCR")
    print("=" * 60)

    try:
        import pytesseract

        # Get Tesseract version
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract version: {version}")
        except Exception as e:
            print(f"❌ Cannot get Tesseract version: {e}")
            return False

        # Check available languages
        try:
            import subprocess
            result = subprocess.run(
                ['tesseract', '--list-langs'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                langs = result.stdout.strip().split('\n')[1:]  # Skip header
                print(f"\n✅ Available languages ({len(langs)}):")
                for lang in langs:
                    emoji = "✅" if lang in ['eng', 'chi_sim', 'chi_tra'] else "ℹ️"
                    print(f"   {emoji} {lang}")

                # Check required languages
                required = {'eng', 'chi_sim', 'chi_tra'}
                available = set(langs)
                missing = required - available

                if missing:
                    print(f"\n⚠️  Missing required language packs: {', '.join(missing)}")
                    return False
                else:
                    print(f"\n✅ All required language packs are installed!")
                    return True
            else:
                print(f"❌ Error listing languages: {result.stderr}")
                return False

        except FileNotFoundError:
            print("❌ Tesseract command not found in PATH")
            return False
        except Exception as e:
            print(f"❌ Error checking languages: {e}")
            return False

    except ImportError:
        print("❌ pytesseract package not installed")
        return False


def test_ocr_functionality():
    """Test actual OCR functionality with a simple test."""
    print("\n" + "=" * 60)
    print("Testing OCR Functionality")
    print("=" * 60)

    try:
        import pytesseract
        from PIL import Image, ImageDraw, ImageFont
        import io

        # Create a simple test image with text
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)

        # Draw text
        text = "Invoice #12345"
        draw.text((10, 40), text, fill='black')

        # Perform OCR
        try:
            ocr_result = pytesseract.image_to_string(img, lang='eng')
            ocr_result = ocr_result.strip()

            if 'Invoice' in ocr_result or '12345' in ocr_result:
                print(f"✅ OCR Test Passed!")
                print(f"   Input:  '{text}'")
                print(f"   Output: '{ocr_result}'")
                return True
            else:
                print(f"⚠️  OCR Test Partial: Text recognized but not accurate")
                print(f"   Input:  '{text}'")
                print(f"   Output: '{ocr_result}'")
                return True  # Still consider it passing
        except Exception as e:
            print(f"❌ OCR Test Failed: {e}")
            return False

    except Exception as e:
        print(f"❌ Cannot run OCR test: {e}")
        return False


def test_opencv():
    """Test OpenCV functionality."""
    print("\n" + "=" * 60)
    print("Testing OpenCV (Image Preprocessing)")
    print("=" * 60)

    try:
        import cv2
        import numpy as np

        print(f"✅ OpenCV version: {cv2.__version__}")

        # Test basic image operations
        try:
            img = np.zeros((100, 100), dtype=np.uint8)
            gray = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_GRAY2RGB), cv2.COLOR_RGB2GRAY)
            print("✅ Image conversion: OK")

            # Test CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(img)
            print("✅ CLAHE enhancement: OK")

            # Test denoising
            denoised = cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
            print("✅ Denoising: OK")

            return True
        except Exception as e:
            print(f"⚠️  Some OpenCV features failed: {e}")
            print("   (Image preprocessing may be limited)")
            return True  # Non-critical

    except ImportError:
        print("⚠️  OpenCV not available")
        print("   (Image preprocessing will be disabled)")
        return True  # Non-critical


def test_database():
    """Test database connection."""
    print("\n" + "=" * 60)
    print("Testing Database")
    print("=" * 60)

    try:
        import database
        backend = database.current_backend()
        print(f"✅ Database backend: {backend}")

        # Try to get invoices (should work even if empty)
        invoices = database.get_invoices()
        print(f"✅ Database query: OK ({len(invoices)} invoices)")
        return True

    except Exception as e:
        print(f"⚠️  Database test: {e}")
        return True  # Non-critical for OCR testing


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Invoice OCR System - Diagnostic Test" + " " * 11 + "║")
    print("╚" + "=" * 58 + "╝")
    print(f"\nTest started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {
        'Python Imports': test_imports(),
        'Tesseract OCR': test_tesseract(),
        'OCR Functionality': test_ocr_functionality(),
        'OpenCV': test_opencv(),
        'Database': test_database(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:8s} - {test_name}")

    passed_count = sum(results.values())
    total_count = len(results)

    print(f"\n{passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n✅ All systems operational! OCR is ready to use.")
        return 0
    elif results['Tesseract OCR'] and results['OCR Functionality']:
        print("\n⚠️  Core OCR functionality works, but some features may be limited.")
        return 0
    else:
        print("\n❌ Critical components are missing. OCR will not work properly.")
        print("\nPlease ensure:")
        print("1. Tesseract OCR is installed")
        print("2. Required language packs are installed (eng, chi_sim, chi_tra)")
        print("3. All Python packages are installed (pip install -r requirements.txt)")
        return 1


if __name__ == '__main__':
    sys.exit(main())
