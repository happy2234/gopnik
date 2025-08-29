#!/usr/bin/env python3
"""Validate Gopnik setup."""

import importlib.util
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(
            f"❌ Python version {version.major}.{version.minor} not supported. Need 3.8+"
        )
        return False


def check_dependencies():
    """Check if dependencies are installed."""
    package_map = {
        # Core
        "numpy": "numpy",
        "pandas": "pandas",
        "opencv-python": "cv2",
        "pillow": "PIL",
        "matplotlib": "matplotlib",
        # OCR
        "easyocr": "easyocr",
        "pytesseract": "pytesseract",
        # NLP
        "spacy": "spacy",
        "transformers": "transformers",
        "torch": "torch",
        "datasets": "datasets",
        # Computer Vision
        "ultralytics": "ultralytics",
        "supervision": "supervision",
        # Document Processing
        "PyPDF2": "PyPDF2",
        "pdf2image": "pdf2image",
        "python-docx": "docx",
        # API & Web
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "streamlit": "streamlit",
        # CLI
        "click": "click",
        "rich": "rich",
        "typer": "typer",
        # Testing
        "pytest": "pytest",
        "pytest-cov": "pytest_cov",
        "pytest-asyncio": "pytest_asyncio",
        # Development
        "black": "black",
        "isort": "isort",
        "flake8": "flake8",
        "mypy": "mypy",
        "pre-commit": "pre_commit",
        # Logging & Monitoring
        "loguru": "loguru",
        "pydantic": "pydantic",
        # Security
        "cryptography": "cryptography",
    }

    missing = []
    for pkg, import_name in package_map.items():
        spec = importlib.util.find_spec(import_name)
        if spec is None:
            missing.append(pkg)
        else:
            print(f"✅ {pkg}")

    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        return False

    return True


def check_directory_structure():
    """Check project directory structure."""
    required_dirs = ["src/gopnik/core", "tests", "docs", "data", "models", "configs"]

    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ Missing directory: {dir_path}/")
            return False

    return True


def check_git_repo():
    """Check Git repository status."""
    try:
        subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
        print("✅ Git repository initialized")
        return True
    except subprocess.CalledProcessError:
        print("❌ Git repository not initialized")
        return False


def main():
    """Run all validation checks."""
    print("🔍 Validating Gopnik Phase 0 Setup...\n")

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directory Structure", check_directory_structure),
        ("Git Repository", check_git_repo),
    ]

    all_passed = True
    for name, check_func in checks:
        print(f"\n📋 Checking {name}:")
        if not check_func():
            all_passed = False

    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 All checks passed! Phase 0 setup complete.")
        print("Next: Implement Phase 1 - Core Engine")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
