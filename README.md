# Gopnik - AI Toolkit for Forensic-Grade Visual & Textual Deidentification

[![CI/CD Pipeline](https://github.com/timecracker/gopnik-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/timecracker/gopnik-toolkit/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/timecracker/gopnik-toolkit/branch/main/graph/badge.svg)](https://codecov.io/gh/timecracker/gopnik-toolkit)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

Gopnik is a privacy-first, multi-platform, open-source toolkit for automated forensic-grade redaction of textual and visual personally identifiable information (PII). It integrates AI-powered OCR, NLP, and computer vision models to provide comprehensive deidentification capabilities for legal, medical, and government workflows.

## Features

- **AI-Powered Detection**: OCR + NLP + Computer Vision for comprehensive PII detection
- **Forensic-Grade Logging**: Complete audit trails with bounding boxes, timestamps, and hashes
- **Multi-Platform**: Desktop GUI, CLI, and Web interfaces
- **Privacy-First**: Offline-first architecture for sensitive data processing
- **Multilingual Support**: Supports Indic scripts and multiple languages
- **Open Source**: MIT licensed with extensive documentation

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/timecracker/gopnik-toolkit.git
cd gopnik-toolkit

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run basic test
gopnik --version
