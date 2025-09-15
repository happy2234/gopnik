# Document Processing Core

The Document Processing Core is the heart of Gopnik's deidentification system, providing a comprehensive pipeline for analyzing, detecting PII, and redacting documents while maintaining forensic-grade audit trails.

## 🏗️ Architecture Overview

The core consists of three main components working together:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Document        │───▶│ AI Detection    │───▶│ Redaction       │
│ Analyzer        │    │ Engine          │    │ Engine          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Structure       │    │ PII Detections  │    │ Redacted        │
│ Analysis        │    │ & Confidence    │    │ Document        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📄 Document Analyzer

The `DocumentAnalyzer` handles parsing and structure analysis for various document formats.

### Supported Formats
- **PDF**: Multi-page documents with text extraction
- **Images**: PNG, JPEG, TIFF, BMP with metadata preservation
- **Structure Preservation**: Layout, fonts, and formatting maintained

### Key Features
```python
from gopnik.core.analyzer import DocumentAnalyzer

analyzer = DocumentAnalyzer()

# Analyze document structure
document = analyzer.analyze_document(Path("document.pdf"))
print(f"Pages: {document.page_count}")
print(f"Format: {document.format}")
print(f"Structure: {document.structure}")

# Extract individual pages
pages = analyzer.extract_pages(Path("document.pdf"))
for page in pages:
    print(f"Page {page['page_number']}: {page['width']}x{page['height']}")
```

### Document Structure Analysis
- **Page-by-Page Processing**: Efficient handling of large documents
- **Metadata Extraction**: File properties, creation dates, author info
- **Layout Analysis**: Text distribution, orientation detection
- **Integrity Validation**: File hash calculation and verification

## 🤖 AI Detection Integration

The processor coordinates multiple AI engines for comprehensive PII detection.

### AI Engine Types
1. **Computer Vision Engine**: Visual PII detection (faces, signatures, barcodes)
2. **NLP Engine**: Text PII detection (names, emails, addresses, SSNs)
3. **Hybrid Engine**: Intelligent fusion of CV and NLP results

### Detection Pipeline
```python
from gopnik.core.processor import DocumentProcessor
from gopnik.ai.hybrid_engine import HybridAIEngine

# Initialize processor with AI engine
processor = DocumentProcessor()
ai_engine = HybridAIEngine()
processor.set_ai_engine(ai_engine)

# Process document
result = processor.process_document(
    input_path=Path("document.pdf"),
    profile=redaction_profile
)

print(f"Detections: {result.detection_count}")
for detection in result.detections:
    print(f"- {detection.type}: {detection.confidence:.2f}")
```

## 🎨 Redaction Engine

The `RedactionEngine` applies redactions while preserving document layout and structure.

### Redaction Styles

#### Solid Redaction
- **Black/White Blocks**: Complete obscuration of PII
- **Use Case**: Maximum privacy, legal compliance
- **Example**: `[████████]` for sensitive data

#### Pixelated Redaction
- **Pixelation Effect**: Partial visibility with privacy protection
- **Use Case**: Maintaining document readability while protecting PII
- **Configurable**: Pixel size based on content area

#### Blur Redaction
- **Gaussian Blur**: Aesthetic redaction with smooth appearance
- **Use Case**: Professional documents, presentations
- **Configurable**: Blur radius based on content size

### Redaction Configuration
```python
from gopnik.models.profiles import RedactionProfile, RedactionStyle

# Create custom redaction profile
profile = RedactionProfile(
    name="custom_profile",
    description="Custom redaction settings",
    text_rules={
        "name": True,      # Redact names
        "email": True,     # Redact emails
        "phone": False     # Don't redact phone numbers
    },
    redaction_style=RedactionStyle.PIXELATED,
    confidence_threshold=0.8
)

# Apply redactions
redacted_path = redaction_engine.apply_redactions(
    document_path=Path("document.pdf"),
    detections=pii_detections,
    profile=profile
)
```

## 🔄 Document Processor Coordinator

The `DocumentProcessor` orchestrates the entire processing pipeline.

### Processing Workflow

1. **Document Validation**: Format support, file integrity
2. **Structure Analysis**: Page extraction, metadata collection
3. **PII Detection**: AI engine coordination
4. **Redaction Application**: Style-based redaction
5. **Audit Logging**: Cryptographic audit trail creation
6. **Result Generation**: Comprehensive processing results

### Single Document Processing
```python
from gopnik.core.processor import DocumentProcessor
from gopnik.models.profiles import RedactionProfile

processor = DocumentProcessor()

# Process single document
result = processor.process_document(
    input_path=Path("document.pdf"),
    profile=RedactionProfile.from_yaml(Path("profiles/healthcare.yaml"))
)

# Check results
if result.success:
    print(f"✅ Processing completed successfully")
    print(f"📄 Output: {result.output_path}")
    print(f"🔍 Detections: {result.detection_count}")
    print(f"⏱️ Time: {result.processing_time:.2f}s")
else:
    print(f"❌ Processing failed: {result.errors}")
```

### Batch Processing
```python
# Process entire directory
batch_result = processor.batch_process(
    input_dir=Path("./documents"),
    profile=redaction_profile
)

print(f"📊 Batch Results:")
print(f"  Total: {batch_result.total_documents}")
print(f"  Successful: {batch_result.processed_documents}")
print(f"  Failed: {batch_result.failed_documents}")
print(f"  Success Rate: {batch_result.success_rate:.1f}%")
```

## 📊 Performance Metrics

The processor provides comprehensive performance monitoring:

### Processing Metrics
- **Total Time**: End-to-end processing duration
- **Detection Time**: AI engine processing time
- **Redaction Time**: Redaction application time
- **I/O Time**: File reading/writing time
- **Memory Usage**: Peak memory consumption
- **Pages per Second**: Processing throughput

### Statistics Tracking
```python
# Get processing statistics
stats = processor.get_processing_statistics()
print(f"Documents processed: {stats['total_processed']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
print(f"Average time: {stats['average_processing_time']:.2f}s")

# Health check
health = processor.health_check()
print(f"Status: {health['status']}")
print(f"Components: {health['components']}")
```

## 🔒 Security & Audit Integration

### Audit Logging
Every processing operation generates cryptographically signed audit logs:

```python
# Audit information in processing result
audit_log = result.audit_log
print(f"Operation: {audit_log.operation}")
print(f"Timestamp: {audit_log.timestamp}")
print(f"Signature: {audit_log.signature}")
print(f"Document Hash: {audit_log.input_hash}")
```

### Document Validation
```python
# Validate processed document integrity
is_valid = processor.validate_document(
    document_path=Path("redacted.pdf"),
    audit_path=Path("audit.json")
)

if is_valid:
    print("✅ Document integrity verified")
else:
    print("❌ Document integrity check failed")
```

## 🛠️ Configuration & Customization

### Custom AI Engine Integration
```python
from gopnik.core.interfaces import AIEngineInterface

class CustomAIEngine(AIEngineInterface):
    def detect_pii(self, document_data):
        # Custom PII detection logic
        return detections
    
    def get_supported_types(self):
        return ["custom_pii_type"]
    
    def configure(self, config):
        # Custom configuration
        pass

# Use custom engine
processor.set_ai_engine(CustomAIEngine())
```

### Error Handling
```python
from gopnik.models.errors import DocumentProcessingError

try:
    result = processor.process_document(input_path, profile)
except DocumentProcessingError as e:
    print(f"Processing error: {e}")
    # Handle specific error types
```

## 🧪 Testing & Validation

The core includes comprehensive test coverage:

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow validation
- **Performance Tests**: Memory and processing efficiency
- **Security Tests**: Cryptographic validation

```bash
# Run core component tests
pytest tests/test_document_analyzer.py -v
pytest tests/test_redaction_engine.py -v
pytest tests/test_document_processor.py -v

# Run integration tests
pytest tests/test_ai_integration.py -v
```

## 📈 Best Practices

### Performance Optimization
1. **Batch Processing**: Use batch mode for multiple documents
2. **Memory Management**: Process large documents page-by-page
3. **AI Engine Selection**: Choose appropriate engine for use case
4. **Profile Optimization**: Tune confidence thresholds

### Security Considerations
1. **Audit Logging**: Always enable audit trails for compliance
2. **Document Validation**: Verify integrity after processing
3. **Secure Storage**: Protect processed documents and audit logs
4. **Access Control**: Implement proper access controls

### Error Recovery
1. **Graceful Degradation**: Continue processing on non-critical errors
2. **Retry Logic**: Implement retry for transient failures
3. **Logging**: Comprehensive error logging for debugging
4. **Monitoring**: Track processing success rates and performance

## 🔗 Related Documentation

- **[AI Engine Architecture](AI-Engine-Architecture)**: Detailed AI engine documentation
- **[Redaction Styles Guide](Redaction-Styles-Guide)**: Redaction style configuration
- **[Audit Trail Analysis](Audit-Trail-Analysis)**: Working with audit logs
- **[Performance Optimization](Performance-Optimization)**: Performance tuning guide
- **[API Reference](https://happy2234.github.io/gopnik/api/)**: Complete API documentation

---

The Document Processing Core provides a robust, scalable, and secure foundation for enterprise-grade document deidentification with comprehensive audit trails and forensic validation capabilities.