"""
Setup configuration for Gopnik deidentification toolkit.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read version from package
version = "0.1.0"

setup(
    name="gopnik",
    version=version,
    description="AI-powered forensic-grade deidentification toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Gopnik Development Team",
    author_email="dev@gopnik.ai",
    url="https://github.com/happy2234/gopnik",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies
        "pyyaml>=6.0",
        "pydantic>=2.0",
        "click>=8.0",
        
        # Cryptography
        "cryptography>=3.4.8",
        
        # File processing
        "pillow>=9.0.0",
        
        # Logging and utilities
        "colorama>=0.4.4",
        "tqdm>=4.64.0",
    ],
    extras_require={
        "web": [
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
            "python-multipart>=0.0.6",
            "jinja2>=3.1.0",
        ],
        "ai": [
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "transformers>=4.30.0",
            "opencv-python>=4.8.0",
            "numpy>=1.24.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "all": [
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
            "python-multipart>=0.0.6",
            "jinja2>=3.1.0",
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "transformers>=4.30.0",
            "opencv-python>=4.8.0",
            "numpy>=1.24.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "gopnik=gopnik.interfaces.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Legal Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing",
    ],
    keywords="pii deidentification redaction privacy ai forensic",
    project_urls={
        "Bug Reports": "https://github.com/happy2234/gopnik/issues",
        "Source": "https://github.com/happy2234/gopnik",
        "Documentation": "https://gopnik.readthedocs.io/",
    },
)