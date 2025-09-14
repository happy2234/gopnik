# AI Training Guide

This guide covers training and fine-tuning AI models for PII detection in Gopnik, including recommended datasets and training procedures.

## 🎯 Overview

Gopnik uses multiple AI models for comprehensive PII detection:

- **Computer Vision Models**: For visual PII (faces, signatures, barcodes)
- **Natural Language Processing Models**: For text PII (names, emails, addresses)
- **Hybrid Models**: Combining visual and textual understanding

## 📊 Recommended Training Datasets

### Visual PII Detection

#### SignVeRod Dataset (Recommended)
- **Source**: [Kaggle - SignVeRod Dataset](https://www.kaggle.com/datasets/victordibia/signverod/code)
- **Description**: Signature verification and detection dataset
- **Use Case**: Training signature detection models
- **Format**: Images with bounding box annotations
- **Size**: ~10,000+ signature samples

**Dataset Features:**
- High-quality signature images
- Diverse signature styles and formats
- Bounding box annotations for detection
- Multiple signature instances per document
- Various document backgrounds and contexts

**Usage in Gopnik:**
```python
# Example training configuration for signature detection
signature_config = {
    "dataset": "signverod",
    "model_type": "yolov8",
    "classes": ["signature"],
    "input_size": 640,
    "batch_size": 16,
    "epochs": 100
}
```

#### Additional Visual Datasets

**Face Detection:**
- **WIDER FACE**: Large-scale face detection dataset
- **CelebA**: Celebrity face attributes dataset
- **VGGFace2**: Large-scale face recognition dataset

**Document Analysis:**
- **PubLayNet**: Document layout analysis dataset
- **DocBank**: Document layout analysis with fine-grained token-level annotations
- **FUNSD**: Form understanding in noisy scanned documents

### Text PII Detection

#### Named Entity Recognition (NER) Datasets
- **CoNLL-2003**: Standard NER benchmark
- **OntoNotes 5.0**: Multilingual NER dataset
- **WikiNER**: Automatically annotated NER dataset

#### Privacy-Specific Datasets
- **Enron Email Dataset**: For email PII detection
- **Medical Text Datasets**: For healthcare PII (HIPAA compliance)
- **Legal Document Datasets**: For legal document redaction

## 🛠️ Training Infrastructure

### Model Architecture Recommendations

#### Computer Vision Pipeline
```python
# YOLOv8 for signature detection
model_config = {
    "architecture": "yolov8n",  # or yolov8s, yolov8m, yolov8l, yolov8x
    "input_size": 640,
    "classes": ["signature", "face", "barcode", "qr_code"],
    "pretrained": True,
    "freeze_backbone": False
}
```

#### NLP Pipeline
```python
# LayoutLMv3 for document understanding
nlp_config = {
    "architecture": "layoutlmv3-base",
    "max_sequence_length": 512,
    "classes": ["PERSON", "EMAIL", "PHONE", "ADDRESS", "SSN"],
    "multilingual": True,
    "languages": ["en", "es", "fr", "de", "hi", "ar"]
}
```

### Training Configuration

#### Hardware Requirements
- **Minimum**: 8GB GPU memory, 16GB RAM
- **Recommended**: 24GB GPU memory, 32GB RAM
- **Optimal**: Multi-GPU setup (2x RTX 4090 or A100)

#### Training Parameters
```yaml
# training_config.yaml
signature_detection:
  model: yolov8n
  dataset: signverod
  epochs: 100
  batch_size: 16
  learning_rate: 0.001
  weight_decay: 0.0005
  augmentation:
    rotation: 15
    scaling: 0.2
    brightness: 0.2
    contrast: 0.2
  validation_split: 0.2

text_detection:
  model: layoutlmv3-base
  dataset: custom_pii
  epochs: 50
  batch_size: 8
  learning_rate: 2e-5
  warmup_steps: 1000
  max_grad_norm: 1.0
```

## 📋 Training Procedures

### 1. Data Preparation

#### SignVeRod Dataset Setup
```bash
# Download dataset from Kaggle
kaggle datasets download -d victordibia/signverod

# Extract and organize
unzip signverod.zip -d datasets/signverod/
python scripts/prepare_signverod.py --input datasets/signverod/ --output data/signatures/
```

#### Data Annotation Format
```json
{
  "image_id": "doc_001.jpg",
  "annotations": [
    {
      "id": 1,
      "category_id": 1,
      "category_name": "signature",
      "bbox": [x, y, width, height],
      "area": 12500,
      "iscrowd": 0
    }
  ]
}
```

### 2. Model Training

#### Signature Detection Training
```python
from gopnik.ai.training import SignatureDetectionTrainer

trainer = SignatureDetectionTrainer(
    dataset_path="data/signatures/",
    model_config="configs/signature_yolov8.yaml",
    output_dir="models/signature_detection/"
)

# Train model
trainer.train(
    epochs=100,
    batch_size=16,
    learning_rate=0.001,
    validation_split=0.2
)

# Evaluate model
metrics = trainer.evaluate()
print(f"mAP@0.5: {metrics['map_50']}")
print(f"mAP@0.5:0.95: {metrics['map_50_95']}")
```

#### Text PII Training
```python
from gopnik.ai.training import TextPIITrainer

trainer = TextPIITrainer(
    dataset_path="data/text_pii/",
    model_name="layoutlmv3-base",
    output_dir="models/text_pii/"
)

# Fine-tune model
trainer.fine_tune(
    epochs=50,
    batch_size=8,
    learning_rate=2e-5
)

# Evaluate model
metrics = trainer.evaluate()
print(f"F1 Score: {metrics['f1']}")
print(f"Precision: {metrics['precision']}")
print(f"Recall: {metrics['recall']}")
```

### 3. Model Validation

#### Performance Metrics
- **Precision**: Accuracy of positive predictions
- **Recall**: Coverage of actual positives
- **F1 Score**: Harmonic mean of precision and recall
- **mAP**: Mean Average Precision for object detection
- **IoU**: Intersection over Union for bounding boxes

#### Validation Procedures
```python
# Cross-validation
from sklearn.model_selection import KFold

kfold = KFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = []

for train_idx, val_idx in kfold.split(dataset):
    # Train and validate model
    score = train_and_validate(train_idx, val_idx)
    cv_scores.append(score)

print(f"CV Mean: {np.mean(cv_scores):.3f} (+/- {np.std(cv_scores) * 2:.3f})")
```

## 🔧 Custom Dataset Creation

### Creating Your Own PII Dataset

#### 1. Data Collection
```python
# Synthetic data generation
from gopnik.data.synthetic import DocumentGenerator

generator = DocumentGenerator()

# Generate documents with known PII
synthetic_docs = generator.create_documents(
    count=1000,
    pii_types=["signature", "name", "email", "phone"],
    document_types=["form", "contract", "invoice"]
)
```

#### 2. Annotation Tools
- **LabelImg**: For bounding box annotation
- **CVAT**: Computer Vision Annotation Tool
- **Label Studio**: Multi-modal annotation platform

#### 3. Quality Assurance
```python
# Annotation quality checks
def validate_annotations(annotations):
    issues = []
    
    for ann in annotations:
        # Check bounding box validity
        if ann['bbox'][2] <= 0 or ann['bbox'][3] <= 0:
            issues.append(f"Invalid bbox in {ann['image_id']}")
        
        # Check category consistency
        if ann['category_name'] not in VALID_CATEGORIES:
            issues.append(f"Invalid category in {ann['image_id']}")
    
    return issues
```

## 🚀 Model Deployment

### Model Export and Optimization

#### ONNX Export
```python
# Export trained model to ONNX
import torch.onnx

model.eval()
dummy_input = torch.randn(1, 3, 640, 640)

torch.onnx.export(
    model,
    dummy_input,
    "models/signature_detection.onnx",
    export_params=True,
    opset_version=11,
    input_names=['input'],
    output_names=['output']
)
```

#### TensorRT Optimization
```python
# Optimize for inference
import tensorrt as trt

def build_engine(onnx_path, engine_path):
    logger = trt.Logger(trt.Logger.WARNING)
    builder = trt.Builder(logger)
    network = builder.create_network()
    parser = trt.OnnxParser(network, logger)
    
    # Parse ONNX model
    with open(onnx_path, 'rb') as model:
        parser.parse(model.read())
    
    # Build engine
    config = builder.create_builder_config()
    config.max_workspace_size = 1 << 30  # 1GB
    
    engine = builder.build_engine(network, config)
    
    # Save engine
    with open(engine_path, 'wb') as f:
        f.write(engine.serialize())
```

### Integration with Gopnik

#### Model Registration
```python
# Register trained model
from gopnik.ai.registry import ModelRegistry

registry = ModelRegistry()

registry.register_model(
    name="signature_detector_v1",
    model_path="models/signature_detection.onnx",
    model_type="object_detection",
    pii_types=["signature"],
    confidence_threshold=0.7,
    metadata={
        "training_dataset": "signverod",
        "training_date": "2024-01-15",
        "performance": {"map_50": 0.89, "map_50_95": 0.76}
    }
)
```

#### Model Loading
```python
# Load model in Gopnik
from gopnik.ai.engines import CVEngine

engine = CVEngine()
engine.load_model("signature_detector_v1")

# Use for detection
detections = engine.detect_pii(document_image)
```

## 📊 Performance Monitoring

### Training Metrics Tracking
```python
# Use Weights & Biases for experiment tracking
import wandb

wandb.init(project="gopnik-pii-detection")

# Log training metrics
wandb.log({
    "epoch": epoch,
    "train_loss": train_loss,
    "val_loss": val_loss,
    "map_50": map_50,
    "learning_rate": lr
})
```

### Production Monitoring
```python
# Monitor model performance in production
from gopnik.monitoring import ModelMonitor

monitor = ModelMonitor()

# Track inference metrics
monitor.log_inference(
    model_name="signature_detector_v1",
    inference_time=0.045,
    confidence_scores=[0.89, 0.76, 0.92],
    detection_count=3
)
```

## 🔒 Privacy and Security

### Secure Training Practices
- **Data Encryption**: Encrypt training datasets at rest
- **Access Control**: Limit access to sensitive training data
- **Audit Logging**: Log all training activities
- **Model Versioning**: Track model lineage and changes

### Differential Privacy
```python
# Apply differential privacy during training
from opacus import PrivacyEngine

privacy_engine = PrivacyEngine()
model, optimizer, data_loader = privacy_engine.make_private(
    module=model,
    optimizer=optimizer,
    data_loader=train_loader,
    noise_multiplier=1.0,
    max_grad_norm=1.0,
)
```

## 📚 Resources and References

### Academic Papers
- **"LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking"**
- **"YOLOv8: A New Real-Time Object Detection Algorithm"**
- **"SignVeRod: Signature Verification and Detection in Documents"**

### Training Frameworks
- **Ultralytics YOLOv8**: Object detection framework
- **Hugging Face Transformers**: NLP model library
- **PyTorch Lightning**: Training framework
- **Weights & Biases**: Experiment tracking

### Datasets and Benchmarks
- **SignVeRod**: [Kaggle Dataset](https://www.kaggle.com/datasets/victordibia/signverod/code)
- **WIDER FACE**: Face detection benchmark
- **CoNLL-2003**: NER benchmark
- **PubLayNet**: Document layout analysis

---

**🎯 Next Steps**: Start with the SignVeRod dataset for signature detection, then expand to other PII types based on your specific use cases and requirements.