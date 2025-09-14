"""
Gopnik - AI-powered forensic-grade deidentification toolkit.

An open-source system for automatically detecting and redacting PII from documents
while preserving structure and providing verifiable audit trails.
"""

__version__ = "0.1.0"
__author__ = "Gopnik Development Team"

from .core import DocumentProcessor
from .models import PIIDetection, ProcessingResult, RedactionProfile
from .config import GopnikConfig

__all__ = [
    "DocumentProcessor",
    "PIIDetection", 
    "ProcessingResult",
    "RedactionProfile",
    "GopnikConfig"
]