# AI Engine Architecture

Gopnik's AI detection system uses a multi-modal approach combining Computer Vision (CV) and Natural Language Processing (NLP) to achieve comprehensive PII detection across diverse document types.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Hybrid AI Engine                        │
│  ┌─────────────────┐              ┌─────────────────┐      │
│  │ Computer Vision │              │ NLP Engine      │      │
│  │ Engine          │              │                 │      │
│  │                 │              │                 │      │
│  │ • Face Detection│              │ • Named Entity  │      │
│  │ • Signature     │              │   Recognition   │      │
│  │ • Barcode/QR    │              │ • Pattern       │      │
│  │ • Visual PII    │              │   Matching      │      │
│  └─────────────────┘              └─────────────────┘      │
│           │                                │               │
│           └────────────┬───────────────────┘               │
│                        │                                   │
│                ┌───────▼────────┐                          │
│                │ Result Fusion  │                          │
│                │ & Confidence   │                          │
│                │ Scoring        │                          │
│                └────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## 🖼️ Computer Vision Engine

The CV engine specializes in detecting visual PII elements that appear as images or graphical content.

### Supported Visual PII Types
- **Faces**: Human face detection and recognition
- **Signatures**: Handwritten signature identification
- **Barcodes**: 1D barcode detection (Code 128, Code 39, etc.)
- **QR Codes**: 2D QR code detection and reading
- **Custom Visual Elements**: Extensible for domain-specific visual PII

### Implementation Details
```python
from gopnik.ai.cv_engine import ComputerVisionEngine

# Initialize CV engine
cv_engine = ComputerVisionEngine()

# Configure detection parameters
cv_engine.configure({
    'face_detection': {
        'enabled': True,
        'confidence_threshold': 0.7,
        'model': 'haar_cascade'  # or 'dnn', 'mtcnn'
    },
    'signature_detection': {
        'enabled': True,
        'confidence_threshold': 0.8,
        'min_contour_area': 500
    },
    'barcode_detection': {
        'enabled': True,
        'formats': ['code128', 'code39', 'qr']
    }
})

# Detect visual PII
detections = cv_engine.detect_pii(document_data)
```

### Face Detection
- **Multiple Models**: Haar Cascade, DNN, MTCNN support
- **Confidence Scoring**: Adjustable thresholds for precision/recall
- **Bounding Box Accuracy**: Precise face localization
- **Performance Optimized**: Efficient processing for batch operations

### Signature Detection
- **Contour Analysis**: Advanced shape detection algorithms
- **Handwriting Recognition**: Distinguishes signatures from regular text
- **Size Filtering**: Configurable minimum/maximum signature sizes
- **False Positive Reduction**: Advanced filtering techniques

### Barcode/QR Code Detection
- **Multi-Format Support**: Various 1D and 2D barcode formats
- **Content Extraction**: Reads barcode content for validation
- **Orientation Handling**: Detects codes at various angles
- **Quality Assessment**: Confidence scoring based on decode success

## 📝 Natural Language Processing Engine

The NLP engine handles text-based PII detection using advanced language models and pattern recognition.

### Supported Text PII Types
- **Personal Names**: First names, last names, full names
- **Contact Information**: Email addresses, phone numbers
- **Addresses**: Street addresses, postal codes, geographic locations
- **Identification Numbers**: SSNs, passport numbers, driver licenses
- **Financial Information**: Credit card numbers, bank accounts
- **Medical Information**: Medical record numbers, insurance IDs
- **Custom Patterns**: Configurable regex and ML-based detection

### Implementation Details
```python
from gopnik.ai.nlp_engine import NLPEngine

# Initialize NLP engine
nlp_engine = NLPEngine()

# Configure detection parameters
nlp_engine.configure({
    'models': {
        'ner_model': 'en_core_web_sm',  # spaCy model
        'custom_model': None
    },
    'detection_rules': {
        'names': {
            'enabled': True,
            'confidence_threshold': 0.8,
            'use_context': True
        },
        'emails': {
            'enabled': True,
            'pattern_validation': True
        },
        'phones': {
            'enabled': True,
            'formats': ['us', 'international'],
            'confidence_threshold': 0.9
        }
    }
})

# Detect text PII
detections = nlp_engine.detect_pii(document_text)
```

### Named Entity Recognition (NER)
- **Pre-trained Models**: spaCy, transformers-based models
- **Custom Training**: Domain-specific model fine-tuning
- **Context Awareness**: Considers surrounding text for accuracy
- **Multi-language Support**: Handles various languages and scripts

### Pattern Matching
- **Regex Patterns**: Optimized regular expressions for common PII
- **Validation Logic**: Format validation for detected patterns
- **False Positive Filtering**: Advanced filtering to reduce noise
- **Custom Patterns**: User-defined pattern support

### Advanced Text Processing
- **Tokenization**: Intelligent text segmentation
- **Normalization**: Text cleaning and standardization
- **OCR Integration**: Handles OCR-extracted text with noise
- **Layout Awareness**: Considers document structure in detection

## 🔄 Hybrid AI Engine

The Hybrid engine intelligently combines CV and NLP results for maximum accuracy and coverage.

### Fusion Strategies

#### Confidence-Based Fusion
```python
from gopnik.ai.hybrid_engine import HybridAIEngine

hybrid_engine = HybridAIEngine()

# Configure fusion parameters
hybrid_engine.configure({
    'fusion_strategy': 'confidence_weighted',
    'cv_weight': 0.6,
    'nlp_weight': 0.4,
    'confidence_threshold': 0.75,
    'overlap_handling': 'merge_high_confidence'
})
```

#### Spatial Correlation
- **Overlap Detection**: Identifies overlapping detections from CV and NLP
- **Spatial Validation**: Validates text detections against visual elements
- **Coordinate Mapping**: Maps text positions to image coordinates
- **Conflict Resolution**: Handles conflicting detections intelligently

#### Result Aggregation
- **Duplicate Removal**: Eliminates redundant detections
- **Confidence Boosting**: Increases confidence for correlated detections
- **Gap Filling**: Uses one engine to fill gaps in the other
- **Quality Assessment**: Overall detection quality scoring

### Implementation Example
```python
from gopnik.ai.hybrid_engine import HybridAIEngine
from gopnik.models.processing import Document

# Initialize hybrid engine
hybrid_engine = HybridAIEngine()

# Process document with both engines
document = Document.from_path("document.pdf")
detections = hybrid_engine.detect_pii(document)

# Analyze results
print(f"Total detections: {len(detections)}")
for detection in detections:
    print(f"- {detection.type}: {detection.confidence:.2f} ({detection.detection_method})")
```

## 🎯 Detection Accuracy & Performance

### Accuracy Metrics
- **Precision**: Percentage of detected PII that is actually PII
- **Recall**: Percentage of actual PII that is detected
- **F1-Score**: Harmonic mean of precision and recall
- **Confidence Calibration**: Alignment between confidence scores and accuracy

### Performance Benchmarks
```python
# Performance monitoring
from gopnik.ai.hybrid_engine import HybridAIEngine

engine = HybridAIEngine()
stats = engine.get_performance_stats()

print(f"Average processing time: {stats['avg_processing_time']:.2f}s")
print(f"Detections per second: {stats['detections_per_second']:.1f}")
print(f"Memory usage: {stats['memory_usage_mb']:.1f} MB")
```

### Optimization Strategies
1. **Model Selection**: Choose appropriate models for use case
2. **Batch Processing**: Process multiple documents efficiently
3. **Caching**: Cache model loading and preprocessing
4. **Parallel Processing**: Utilize multiple CPU cores
5. **GPU Acceleration**: Leverage GPU for deep learning models

## 🔧 Configuration & Customization

### Engine Configuration
```python
# Comprehensive configuration example
config = {
    'cv_engine': {
        'face_detection': {
            'enabled': True,
            'model': 'mtcnn',
            'confidence_threshold': 0.8,
            'min_face_size': (30, 30)
        },
        'signature_detection': {
            'enabled': True,
            'confidence_threshold': 0.7,
            'contour_analysis': True
        }
    },
    'nlp_engine': {
        'ner_model': 'en_core_web_lg',
        'custom_patterns': {
            'employee_id': r'EMP\d{6}',
            'project_code': r'PRJ-[A-Z]{3}-\d{4}'
        },
        'confidence_threshold': 0.75
    },
    'hybrid_fusion': {
        'strategy': 'weighted_average',
        'cv_weight': 0.6,
        'nlp_weight': 0.4,
        'overlap_threshold': 0.3
    }
}

hybrid_engine.configure(config)
```

### Custom Model Integration
```python
from gopnik.core.interfaces import AIEngineInterface

class CustomAIEngine(AIEngineInterface):
    def __init__(self):
        # Load custom model
        self.model = load_custom_model()
    
    def detect_pii(self, document_data):
        # Custom detection logic
        detections = self.model.predict(document_data)
        return self._format_detections(detections)
    
    def get_supported_types(self):
        return ['custom_pii_type']
    
    def configure(self, config):
        # Custom configuration
        self.model.update_config(config)

# Register custom engine
processor.set_ai_engine(CustomAIEngine())
```

## 📊 Monitoring & Analytics

### Detection Analytics
```python
# Get detailed analytics
analytics = hybrid_engine.get_detection_analytics()

print("Detection Statistics:")
print(f"  CV Detections: {analytics['cv_detections']}")
print(f"  NLP Detections: {analytics['nlp_detections']}")
print(f"  Fused Detections: {analytics['fused_detections']}")
print(f"  Confidence Distribution: {analytics['confidence_dist']}")
```

### Performance Monitoring
- **Processing Time**: Track processing duration per document
- **Memory Usage**: Monitor memory consumption patterns
- **Accuracy Metrics**: Track precision/recall over time
- **Error Rates**: Monitor detection failures and errors

### Quality Assurance
- **Confidence Calibration**: Ensure confidence scores reflect accuracy
- **False Positive Analysis**: Identify and reduce false positives
- **Coverage Analysis**: Ensure comprehensive PII detection
- **Bias Detection**: Monitor for detection bias across demographics

## 🧪 Testing & Validation

### Unit Testing
```bash
# Test individual engines
pytest tests/test_cv_engine.py -v
pytest tests/test_nlp_engine.py -v
pytest tests/test_hybrid_engine.py -v

# Test integration
pytest tests/test_ai_integration.py -v
```

### Validation Datasets
- **Synthetic Data**: Generated test documents with known PII
- **Anonymized Real Data**: Real documents with PII removed/replaced
- **Benchmark Datasets**: Standard evaluation datasets
- **Domain-specific Data**: Industry-specific validation sets

### Performance Testing
```python
# Performance benchmarking
from gopnik.ai.testing import PerformanceBenchmark

benchmark = PerformanceBenchmark()
results = benchmark.run_benchmark(
    engine=hybrid_engine,
    test_documents=test_docs,
    metrics=['precision', 'recall', 'f1', 'processing_time']
)

print(f"Benchmark Results: {results}")
```

## 🔗 Integration Examples

### CLI Integration
```bash
# Use specific AI engine
gopnik process --input document.pdf --ai-engine hybrid --profile healthcare

# Configure engine parameters
gopnik process --input document.pdf --cv-confidence 0.8 --nlp-confidence 0.7
```

### API Integration
```python
# REST API usage
import requests

response = requests.post('/api/v1/process', json={
    'document_path': 'document.pdf',
    'ai_engine': 'hybrid',
    'config': {
        'cv_engine': {'face_detection': {'enabled': True}},
        'nlp_engine': {'confidence_threshold': 0.8}
    }
})

result = response.json()
```

### Web Interface Integration
The AI engines are seamlessly integrated into the web interface with real-time configuration and monitoring capabilities.

## 🔗 Related Documentation

- **[Document Processing Core](Document-Processing-Core)**: Core processing pipeline
- **[Redaction Styles Guide](Redaction-Styles-Guide)**: Redaction configuration
- **[Performance Optimization](Performance-Optimization)**: Performance tuning
- **[Custom AI Models](Custom-AI-Models)**: Custom model integration
- **[API Reference](https://happy2234.github.io/gopnik/api/)**: Complete API documentation

---

The AI Engine Architecture provides a flexible, accurate, and scalable foundation for PII detection across diverse document types and use cases.