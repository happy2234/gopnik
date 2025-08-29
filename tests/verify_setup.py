#!/usr/bin/env python3
"""Verify Python 3.11 setup for Gopnik."""

import importlib.util
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major == 3 and version.minor == 11:
        print("✅ Python 3.11 detected")
        return True
    elif version.major == 3 and version.minor >= 8:
        print(
            f"⚠️  Python {version.major}.{version.minor} - should work but 3.11 recommended"
        )
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor} not supported")
        return False


def check_core_packages():
    """Check core packages."""
    core_packages = [
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
        ("matplotlib", "Matplotlib"),
    ]

    all_good = True
    for module, name in core_packages:
        try:
            importlib.import_module(module)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} not installed")
            all_good = False

    return all_good


def check_ml_packages():
    """Check ML packages."""
    ml_packages = [
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("spacy", "spaCy"),
        ("ultralytics", "YOLOv8"),
    ]

    all_good = True
    for module, name in ml_packages:
        try:
            mod = importlib.import_module(module)
            version = getattr(mod, "__version__", "unknown")
            print(f"✅ {name} {version}")
        except ImportError:
            print(f"❌ {name} not installed")
            all_good = False

    return all_good


def check_ocr_setup():
    """Check OCR setup."""
    try:
        import easyocr

        print(f"✅ EasyOCR {easyocr.__version__}")
        ocr_works = True
    except ImportError:
        print("❌ EasyOCR not installed")
        ocr_works = False

    try:
        import pytesseract

        print("✅ PyTesseract installed")

        # Try to get Tesseract version
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract {version} detected")
        except:
            print(
                "⚠️  Tesseract executable not found - you may need to install it separately"
            )
    except ImportError:
        print("❌ PyTesseract not installed")
        ocr_works = False

    return ocr_works


def main():
    """Run all checks."""
    print("🔍 Verifying Python 3.11 Gopnik Setup...\n")

    checks = [
        ("Python Version", check_python_version),
        ("Core Packages", check_core_packages),
        ("ML Packages", check_ml_packages),
        ("OCR Setup", check_ocr_setup),
    ]

    all_passed = True
    for name, check_func in checks:
        print(f"\n📋 Checking {name}:")
        if not check_func():
            all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 Python 3.11 setup verification complete!")
        print("You can now proceed with Gopnik development.")
    else:
        print("❌ Some packages are missing. Install them with:")
        print("pip install -r requirements.txt")


if __name__ == "__main__":
    main()
