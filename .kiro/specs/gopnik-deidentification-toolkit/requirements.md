# Requirements Document

## Introduction

Gopnik is an open-source, AI-powered forensic-grade deidentification toolkit that automatically detects and redacts Personally Identifiable Information (PII) from complex, visually-rich documents while preserving document structure and providing verifiable audit trails. The system serves three distinct user groups through specialized deployment options: a web demo for quick testing, a CLI tool for secure offline processing, and an API for integration into existing workflows.

## Requirements

### Requirement 1: Core PII Detection and Redaction

**User Story:** As a legal professional, I want to automatically detect and redact PII from complex documents, so that I can process sensitive materials quickly and accurately without manual errors.

#### Acceptance Criteria

1. WHEN a document is uploaded THEN the system SHALL detect faces, signatures, barcodes, and other visual PII elements using computer vision
2. WHEN a document contains text THEN the system SHALL identify and redact textual PII (names, emails, phone numbers, addresses, IDs) while preserving document layout
3. WHEN processing multilingual documents THEN the system SHALL support multiple languages including Indic scripts
4. WHEN redaction is complete THEN the system SHALL preserve the original document structure and formatting
5. IF custom redaction profiles are defined THEN the system SHALL apply only the specified redaction rules

### Requirement 2: Web Demo Interface

**User Story:** As a journalist or NGO worker, I want a simple web interface to quickly redact documents, so that I can prepare materials for publication without technical expertise.

#### Acceptance Criteria

1. WHEN accessing the web demo THEN the system SHALL provide a drag-and-drop interface built with Cardio library
2. WHEN uploading files THEN the system SHALL process them temporarily and delete them permanently after processing
3. WHEN using the interface THEN the system SHALL provide a help sidebar with guidance
4. WHEN processing is complete THEN the system SHALL allow download of redacted documents
5. IF the system experiences high traffic THEN Cloudflare protection SHALL prevent abuse through WAF and rate limiting

### Requirement 3: CLI Offline Processing

**User Story:** As a forensic auditor, I want a command-line tool for offline processing, so that I can handle sensitive data in air-gapped environments with full audit trails.

#### Acceptance Criteria

1. WHEN running CLI commands THEN the system SHALL process documents entirely offline without internet connectivity
2. WHEN processing documents THEN the system SHALL generate detailed cryptographic audit logs
3. WHEN validating documents THEN the system SHALL provide a validate command to prove document integrity
4. WHEN processing multiple files THEN the system SHALL support batch processing operations
5. WHEN seeking help THEN the system SHALL provide comprehensive --help documentation for all commands

### Requirement 4: API Integration

**User Story:** As a developer, I want a REST API to integrate deidentification capabilities into my applications, so that I can automate privacy protection in my workflows.

#### Acceptance Criteria

1. WHEN accessing the API THEN the system SHALL provide FastAPI-based REST endpoints
2. WHEN using the API THEN the system SHALL include interactive, auto-generated documentation
3. WHEN making API calls THEN the system SHALL support batch processing for large-scale operations
4. WHEN integrating THEN the system SHALL provide clear error handling and response formats
5. IF authentication is required THEN the system SHALL implement secure API key management

### Requirement 5: Custom Redaction Profiles

**User Story:** As a healthcare administrator, I want to define custom redaction rules, so that I can comply with specific regulatory requirements for different document types.

#### Acceptance Criteria

1. WHEN creating profiles THEN the system SHALL accept YAML/JSON configuration files
2. WHEN defining rules THEN the system SHALL allow specification of PII types to redact (emails, faces, signatures, etc.)
3. WHEN applying profiles THEN the system SHALL process only the specified PII categories
4. WHEN managing profiles THEN the system SHALL support multiple named profiles for different use cases
5. IF profiles conflict THEN the system SHALL provide clear error messages and resolution guidance

### Requirement 6: Audit Trail and Integrity Validation

**User Story:** As a legal team member, I want cryptographic proof that redacted documents haven't been tampered with, so that I can maintain evidence integrity in legal proceedings.

#### Acceptance Criteria

1. WHEN processing documents THEN the system SHALL generate cryptographic hashes and audit logs
2. WHEN validating documents THEN the system SHALL verify integrity using stored cryptographic signatures
3. WHEN audit trails are created THEN the system SHALL record all processing steps with timestamps
4. WHEN validation fails THEN the system SHALL clearly indicate what has been altered
5. IF audit logs are requested THEN the system SHALL provide detailed processing history

### Requirement 7: Hybrid AI Engine

**User Story:** As a system administrator, I want accurate PII detection using multiple AI approaches, so that the system can handle both visual and textual content effectively.

#### Acceptance Criteria

1. WHEN processing visual elements THEN the system SHALL use YOLOv8/Detectron2 for computer vision tasks
2. WHEN processing text THEN the system SHALL use LayoutLMv3/DocTR for layout-aware NLP
3. WHEN combining approaches THEN the system SHALL merge results from both visual and textual analysis
4. WHEN models are updated THEN the system SHALL maintain backward compatibility with existing configurations
5. IF processing fails THEN the system SHALL provide detailed error information about which AI component failed

### Requirement 8: Documentation and User Experience

**User Story:** As any user of the system, I want comprehensive documentation and help, so that I can effectively use all features without confusion.

#### Acceptance Criteria

1. WHEN accessing any version THEN the system SHALL provide version-specific manuals (CLI, Web, API)
2. WHEN using functions THEN the system SHALL include detailed docstrings with examples
3. WHEN testing scenarios THEN the system SHALL provide documented test cases for common use cases
4. WHEN seeking help THEN the system SHALL offer context-appropriate assistance in each interface
5. IF errors occur THEN the system SHALL provide clear, actionable error messages and resolution steps