"""Custom exceptions for Gopnik."""


class GopnikException(Exception):
    """Base exception for Gopnik."""

    pass


class OCRError(GopnikException):
    """OCR processing error."""

    pass


class PIIDetectionError(GopnikException):
    """PII detection error."""

    pass


class RedactionError(GopnikException):
    """Document redaction error."""

    pass


class ModelLoadError(GopnikException):
    """Model loading error."""

    pass


class ValidationError(GopnikException):
    """Input validation error."""

    pass
