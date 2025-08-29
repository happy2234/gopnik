#!/usr/bin/env python3
"""
Gopnik - AI Toolkit for Forensic-Grade Visual & Textual Deidentification
"""

import os

from setuptools import find_packages, setup

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="gopnik",
    version="0.1.0",
    author="Gaurav Kumar",
    author_email="your.email@example.com",
    description="AI Toolkit for Forensic-Grade Visual & Textual Deidentification",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/timecracker/gopnik-toolkit",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Legal Industry",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
        "Topic :: Text Processing",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.1.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
            "mypy>=0.971",
        ],
        "gui": [
            "tkinter",
            "customtkinter>=5.0.0",
        ],
        "web": [
            "streamlit>=1.12.0",
            "fastapi>=0.78.0",
            "uvicorn>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gopnik=gopnik.cli.main:main",
        ],
    },
)
