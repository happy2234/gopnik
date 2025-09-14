# Data Models Guide

This guide covers all the data models and structures used in Gopnik for representing documents, processing results, and audit information.

## 📊 Overview

Gopnik uses a comprehensive set of data models to ensure type safety, validation, and serialization across all components:

- **PII Detection Models**: Represent detected personally identifiable information
- **Document Models**: Represent documents and their structure
- **Processing Models**: Track processing operations and results
- **Audit Models**: Provide forensic-grade audit trails
- **Profile Models**: Configure redaction behavior

## 🔍 PII Detection Models

### PIIType Enum

Supported PII types with automatic classification:

```python
from gopnik.models import PIIType

# Visual PII types
visual_types = PIIType.visual_types()  # [FACE, SIGNATURE, BARCODE, QR_CODE]

# Text PII types  
text_types = PIIType.text_types()  # [NAME, EMAIL, PHONE, etc.]

# Sensitive PII types
sensitive_types = PIIType.sensitive_types()  # [SSN, CREDIT_CARD, etc.]
```

### BoundingBox Class

Represents coordinate regions with validation:

```python
from gopnik.models import BoundingBox

# Create bounding box
bbox = BoundingBox(x1=10, y1=20, x2=100, y2=200)

# Properties
print(f"Width: {bbox.width}, Height: {bbox.height}")
print(f"Area: {bbox.area}, Center: {bbox.center}")

# Overlap detection
bbox2 = BoundingBox(50, 50, 150, 150)
overlaps = bbox.overlaps_with(bbox2, threshold=0.5)
iou_score = bbox.intersection_over_union(bbox2)
```

### PIIDetection Class

Represents individual PII detections:

```python
from gopnik.models import PIIDetection, PIIType, BoundingBox

detection = PIIDetection(
    type=PIIType.FACE,
    bounding_box=BoundingBox(0, 0, 100, 100),
    confidence=0.95,
    text_content=None,  # For visual PII
    page_number=0,
    detection_method="cv"
)

# Properties
print(f"Is visual PII: {detection.is_visual_pii}")
print(f"Is sensitive: {detection.is_sensitive}")

# Serialization
json_str = detection.to_json()
restored = PIIDetection.from_json(json_str)
```

### PIIDetectionCollection Class

Manages collections of detections:

```python
from gopnik.models import PIIDetectionCollection

collection = PIIDetectionCollection(detections=[detection])

# Filtering
face_detections = collection.get_by_type(PIIType.FACE)
high_conf = collection.get_high_confidence(threshold=0.8)
page_detections = collection.get_by_page(0)

# Processing
duplicates_removed = collection.remove_duplicates(iou_threshold=0.7)
collection.filter_by_confidence(0.7)

# Statistics
stats = collection.get_statistics()
print(f"Total detections: {stats['total_detections']}")
```

## 📄 Document Models

### DocumentFormat Enum

Automatic format detection:

```python
from gopnik.models import DocumentFormat

# From file path
format = DocumentFormat.from_path("document.pdf")  # DocumentFormat.PDF

# From MIME type
format = DocumentFormat.from_mime_type("image/png")  # DocumentFormat.PNG
```

### PageInfo Class

Represents document page information:

```python
from gopnik.models import PageInfo

page = PageInfo(
    page_number=0,
    width=800,
    height=600,
    dpi=150.0,
    rotation=0,
    text_content="Extracted text content"
)

# Properties
print(f"Aspect ratio: {page.aspect_ratio}")
print(f"Area: {page.area} pixels")
```

### Document Class

Comprehensive document representation:

```python
from gopnik.models import Document, DocumentFormat, PageInfo
from pathlib import Path

# Create document
doc = Document(
    path=Path("document.pdf"),
    format=DocumentFormat.PDF
)

# Add pages
page = PageInfo(page_number=0, width=800, height=600)
doc.add_page(page)

# Properties
print(f"Page count: {doc.page_count}")
print(f"File size: {doc.file_size} bytes")
print(f"Is multi-page: {doc.is_multi_page}")

# Integrity validation
is_valid = doc.validate_integrity()

# Serialization
doc_dict = doc.to_dict()
restored = Document.from_dict(doc_dict)
```

## ⚙️ Processing Models

### ProcessingStatus Enum

Track processing states:

```python
from gopnik.models import ProcessingStatus

status = ProcessingStatus.IN_PROGRESS
# Values: PENDING, IN_PROGRESS, COMPLETED, FAILED, CANCELLED
```

### ProcessingMetrics Class

Performance tracking:

```python
from gopnik.models import ProcessingMetrics

metrics = ProcessingMetrics(
    total_time=10.5,
    detection_time=3.2,
    redaction_time=5.1,
    pages_processed=5,
    detections_found=12
)

# Calculated properties
print(f"Pages per second: {metrics.pages_per_second}")
print(f"Detections per page: {metrics.detections_per_page}")
```

### ProcessingResult Class

Complete processing operation results:

```python
from gopnik.models import ProcessingResult, ProcessingStatus

result = ProcessingResult(
    document_id=doc.id,
    input_document=doc,
    detections=collection,
    audit_log=audit_log,
    status=ProcessingStatus.COMPLETED
)

# Status management
result.mark_completed(success=True)
result.mark_failed("Error message")
result.add_warning("Warning message")

# Detection access
face_detections = result.get_detections_by_type('face')
high_conf = result.get_high_confidence_detections(0.8)
page_detections = result.get_detections_by_page(0)

# Summary
summary = result.get_summary()
print(f"Success: {result.success}")
print(f"Processing time: {result.processing_time}s")
```

### BatchProcessingResult Class

Batch operation tracking:

```python
from gopnik.models import BatchProcessingResult
from pathlib import Path

batch = BatchProcessingResult(
    input_directory=Path("/input"),
    output_directory=Path("/output"),
    results=[result1, result2, result3],
    started_at=datetime.now(),
    total_documents=3
)

# Statistics
print(f"Success rate: {batch.success_rate}%")
print(f"Failed documents: {batch.failed_documents}")

# Result filtering
failed_results = batch.get_failed_results()
successful_results = batch.get_successful_results()

# Statistics
stats = batch.get_statistics()
```

## 📋 Audit Models

### AuditOperation & AuditLevel Enums

Operation and severity classification:

```python
from gopnik.models import AuditOperation, AuditLevel

# Operations
op = AuditOperation.DOCUMENT_REDACTION
level = AuditLevel.INFO
```

### SystemInfo Class

System context for audits:

```python
from gopnik.models import SystemInfo

system_info = SystemInfo()
print(f"Hostname: {system_info.hostname}")
print(f"Platform: {system_info.platform}")
print(f"Gopnik version: {system_info.gopnik_version}")
```

### AuditLog Class

Comprehensive audit logging:

```python
from gopnik.models import AuditLog, AuditOperation, AuditLevel

# Create audit logs
audit = AuditLog.create_document_operation(
    operation=AuditOperation.DOCUMENT_REDACTION,
    document_id="doc_123",
    user_id="user_456",
    profile_name="healthcare"
)

# Add information
audit.add_detection_summary(detections)
audit.add_file_path("/path/to/document.pdf")
audit.add_warning("Low confidence detection")
audit.set_processing_metrics(5.2, 256.5)

# Create child logs
child_log = audit.create_child_log(
    operation=AuditOperation.PII_DETECTION
)

# Integrity
content_hash = audit.get_content_hash()
is_signed = audit.is_signed()

# Status checks
is_error = audit.is_error()
is_warning = audit.is_warning()

# Serialization
audit_dict = audit.to_dict()
json_str = audit.to_json()
csv_row = audit.to_csv_row()
```

### AuditTrail Class

Collections of audit logs:

```python
from gopnik.models import AuditTrail

trail = AuditTrail(
    id="trail_123",
    name="Document Processing Trail",
    logs=[audit1, audit2, audit3]
)

# Filtering
upload_logs = trail.get_logs_by_operation(AuditOperation.DOCUMENT_UPLOAD)
doc_logs = trail.get_logs_by_document("doc_123")
user_logs = trail.get_logs_by_user("user_456")
error_logs = trail.get_error_logs()

# Time-based filtering
recent_logs = trail.get_logs_in_timeframe(start_time, end_time)

# Chain analysis
chain_logs = trail.get_chain_logs("chain_123")
processing_chain = trail.get_document_processing_chain("doc_123")

# Integrity validation
is_valid, issues = trail.validate_integrity()

# Statistics
stats = trail.get_statistics()

# Export
trail.export_to_csv(Path("audit_trail.csv"))
```

## 🛠️ Utility Functions

### Validation Functions

```python
from gopnik.models import (
    validate_processing_result, validate_audit_log_integrity,
    validate_detection_confidence, validate_coordinates
)

# Validate processing result
is_valid, errors = validate_processing_result(result)

# Validate audit log
is_valid, issues = validate_audit_log_integrity(audit_log)

# Validate detection data
is_valid_conf = validate_detection_confidence(0.85)
is_valid_coords = validate_coordinates((10, 20, 100, 200))
```

### Processing Functions

```python
from gopnik.models import (
    merge_processing_results, create_processing_summary_report,
    merge_overlapping_detections, filter_detections_by_confidence
)

# Merge results
merged_stats = merge_processing_results([result1, result2, result3])

# Create report
report = create_processing_summary_report([result1, result2])

# Process detections
unique_detections = merge_overlapping_detections(detections, iou_threshold=0.7)
high_conf_detections = filter_detections_by_confidence(detections, 0.8)
```

### Audit Functions

```python
from gopnik.models import (
    create_document_processing_audit_chain, merge_audit_trails,
    filter_audit_logs
)

# Create processing chain
chain_logs = create_document_processing_audit_chain(
    document_id="doc_123",
    user_id="user_456",
    profile_name="healthcare"
)

# Merge trails
merged_trail = merge_audit_trails([trail1, trail2])

# Filter logs
filtered_logs = filter_audit_logs(
    logs,
    operation=AuditOperation.DOCUMENT_REDACTION,
    user_id="user_456",
    start_time=start_time
)
```

## 📊 Serialization Support

All models support multiple serialization formats:

### JSON Serialization

```python
# To JSON
json_str = model.to_json()

# From JSON
restored_model = ModelClass.from_json(json_str)
```

### Dictionary Serialization

```python
# To dictionary
model_dict = model.to_dict()

# From dictionary
restored_model = ModelClass.from_dict(model_dict)
```

### CSV Export (Audit Logs)

```python
# CSV headers
headers = AuditLog.get_csv_headers()

# CSV row
row = audit_log.to_csv_row()

# Export trail to CSV
trail.export_to_csv(Path("audit_export.csv"))
```

## 🔒 Security Features

### Integrity Validation

- **Document integrity**: SHA-256 hash validation
- **Audit log integrity**: Content hashing and signature support
- **Chain validation**: Parent-child relationship verification

### Cryptographic Support

- **Hash generation**: SHA-256 for content integrity
- **Signature support**: Digital signature placeholders
- **Secure IDs**: UUID4 for unique identification

### Privacy Protection

- **Data validation**: Input sanitization and validation
- **Secure serialization**: Safe JSON/dict conversion
- **Memory protection**: Secure data handling patterns

## 📈 Performance Considerations

### Efficient Operations

- **Lazy loading**: Properties calculated on demand
- **Batch operations**: Collection-level processing
- **Memory management**: Efficient data structures

### Scalability Features

- **Streaming support**: Large dataset handling
- **Pagination**: Result set management
- **Caching**: Computed property caching

## 🧪 Testing

All models include comprehensive test coverage:

```bash
# Run model tests
python -m pytest tests/test_pii_models.py -v
python -m pytest tests/test_processing_models.py -v
python -m pytest tests/test_audit_models.py -v
```

## 📚 Examples

See the test files for comprehensive usage examples:

- `tests/test_pii_models.py`: PII detection examples
- `tests/test_processing_models.py`: Processing workflow examples
- `tests/test_audit_models.py`: Audit trail examples

---

**💡 Tip**: All models are designed to be immutable where possible and provide comprehensive validation to ensure data integrity throughout the processing pipeline.