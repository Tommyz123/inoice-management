#!/usr/bin/env python3
"""
Tesseract OCR diagnostic script for Render deployment.
Tests if Tesseract is installed and working correctly.
"""

import sys
import subprocess

def test_tesseract():
    """Test if Tesseract OCR is installed and working."""
    print("=" * 60)
    print("TESSERACT OCR DIAGNOSTIC TEST")
    print("=" * 60)

    # Test 1: Check if tesseract command exists
    print("\n1. Checking if tesseract command exists...")
    try:
        result = subprocess.run(
            ["which", "tesseract"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"   ✓ Tesseract found at: {result.stdout.strip()}")
        else:
            print("   ✗ Tesseract command not found")
            return False
    except Exception as e:
        print(f"   ✗ Error checking tesseract: {e}")
        return False

    # Test 2: Check tesseract version
    print("\n2. Checking tesseract version...")
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"   Version output:\n{result.stdout}")
        print(f"   {result.stderr}")
    except Exception as e:
        print(f"   ✗ Error getting version: {e}")
        return False

    # Test 3: Check installed language data
    print("\n3. Checking installed language data...")
    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "eng" in result.stdout:
            print(f"   ✓ English language data found")
            print(f"   Available languages:\n{result.stdout}")
        else:
            print(f"   ✗ English language data NOT found")
            print(f"   Available languages:\n{result.stdout}")
            return False
    except Exception as e:
        print(f"   ✗ Error checking languages: {e}")
        return False

    # Test 4: Check pytesseract import
    print("\n4. Checking pytesseract Python library...")
    try:
        import pytesseract
        print(f"   ✓ pytesseract imported successfully")
        print(f"   Version: {pytesseract.__version__ if hasattr(pytesseract, '__version__') else 'unknown'}")
    except ImportError as e:
        print(f"   ✗ Failed to import pytesseract: {e}")
        return False

    # Test 5: Test OCR with simple text image
    print("\n5. Testing OCR functionality...")
    try:
        from PIL import Image, ImageDraw, ImageFont

        # Create a simple test image with text
        img = Image.new('RGB', (300, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 40), "TEST 12345", fill='black')

        # Try OCR
        text = pytesseract.image_to_string(img, lang='eng')
        print(f"   OCR output: '{text.strip()}'")

        if text.strip():
            print(f"   ✓ OCR is working!")
            return True
        else:
            print(f"   ✗ OCR returned empty text")
            return False

    except Exception as e:
        print(f"   ✗ OCR test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    success = test_tesseract()

    print("\n" + "=" * 60)
    if success:
        print("RESULT: ✓ Tesseract OCR is working correctly!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("RESULT: ✗ Tesseract OCR has issues")
        print("=" * 60)
        print("\nPossible solutions:")
        print("1. Install tesseract: apt-get install tesseract-ocr")
        print("2. Install language data: apt-get install tesseract-ocr-eng")
        print("3. Install Python library: pip install pytesseract")
        sys.exit(1)

if __name__ == "__main__":
    main()
