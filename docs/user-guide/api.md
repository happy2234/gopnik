# REST API Guide

Gopnik provides a comprehensive REST API for programmatic integration with your applications and services. The API offers all the functionality available in the CLI with additional features for web-based applications.

## 🚀 Getting Started

### Starting the API Server

```bash
# Start API server on default port (8000)
gopnik api

# Start on custom host and port
gopnik api --host 0.0.0.0 --port 8080

# Start in development mode with auto-reload
gopnik api --reload --log-level debug
```

### Using Python

```python
from gopnik.interfaces.api.app import run_server

# Start server programmatically
run_server(host="localhost", port=8000, reload=False)
```

## 📖 API Documentation

Once the server is running, you can access:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

## 🔍 Health and Status Endpoints

### Health Check

Get comprehensive system health information:

```bash
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "document_analyzer": "available",
    "redaction_engine": "available",
    "audit_logger": "available",
    "integrity_validator": "available",
    "ai_engine": "available",
    "audit_system": "not_configured"
  },
  "supported_formats": ["pdf", "png", "jpeg", "tiff", "bmp"],
  "statistics": {
    "total_processed": 150,
    "successful_processed": 147,
    "failed_processed": 3,
    "success_rate": 98.0,
    "average_processing_time": 2.5
  },
  "warnings": ["AI engine not configured - PII detection will be skipped"]
}
```

### Simple Status

Basic status check for monitoring:

```bash
GET /api/v1/status
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "gopnik-api"
}
```

## 📄 Document Processing Endpoints

### Single Document Processing

Process a single document with PII redaction:

```bash
POST /api/v1/process
Content-Type: multipart/form-data

file: [document file]
profile_name: "healthcare_hipaa"
confidence_threshold: 0.8
output_format: "pdf"
```

**Response:**
```json
{
  "id": "proc_123456789",
  "document_id": "doc_987654321",
  "status": "completed",
  "success": true,
  "detections": [
    {
      "id": "det_001",
      "type": "name",
      "confidence": 0.95,
      "bounding_box": {
        "x1": 100,
        "y1": 200,
        "x2": 300,
        "y2": 220,
        "width": 200,
        "height": 20,
        "area": 4000
      },
      "text_content": "[REDACTED]",
      "page_number": 0,
      "detection_method": "nlp"
    }
  ],
  "metrics": {
    "total_time": 3.2,
    "detection_time": 1.8,
    "redaction_time": 1.1,
    "io_time": 0.3,
    "pages_processed": 5,
    "detections_found": 12,
    "pages_per_second": 1.56
  },
  "errors": [],
  "warnings": [],
  "profile_name": "healthcare_hipaa",
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:30:03Z",
  "output_available": true
}
```

### Batch Processing

Process multiple documents from an uploaded archive:

```bash
POST /api/v1/batch
Content-Type: multipart/form-data

archive: [zip/tar file containing documents]
profile_name: "default"
recursive: true
confidence_threshold: 0.7
```

**Response:**
```json
{
  "id": "batch_123456789",
  "total_documents": 25,
  "processed_documents": 23,
  "failed_documents": 2,
  "success_rate": 92.0,
  "results": [
    {
      "id": "proc_001",
      "document_id": "doc_001",
      "status": "completed",
      "success": true,
      "detections": [...],
      "metrics": {...}
    }
  ],
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:35:00Z",
  "is_completed": true
}
```

### Async Job Tracking

For large files, processing is handled asynchronously:

```bash
# Get job status
GET /api/v1/jobs/{job_id}

# List all jobs
GET /api/v1/jobs?page=1&page_size=20&status=running
```

**Job Response:**
```json
{
  "job_id": "job_123456789",
  "status": "running",
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:01Z",
  "completed_at": null,
  "progress": 65.5,
  "result": null,
  "error": null
}
```

## 👤 Profile Management Endpoints

### List Profiles

Get all available redaction profiles:

```bash
GET /api/v1/profiles
```

**Response:**
```json
[
  {
    "name": "default",
    "description": "Default redaction profile",
    "visual_rules": {
      "face": true,
      "signature": true,
      "barcode": false
    },
    "text_rules": {
      "name": true,
      "email": true,
      "phone": true,
      "ssn": true
    },
    "redaction_style": "solid_black",
    "confidence_threshold": 0.7,
    "multilingual_support": ["en", "es", "fr"],
    "version": "1.0"
  }
]
```

### Get Profile

Get details of a specific profile:

```bash
GET /api/v1/profiles/{profile_name}
```

### Create Profile

Create a new redaction profile:

```bash
POST /api/v1/profiles
Content-Type: application/json

{
  "name": "custom_profile",
  "description": "Custom redaction profile for legal documents",
  "visual_rules": {
    "face": true,
    "signature": true
  },
  "text_rules": {
    "name": true,
    "email": true,
    "phone": true
  },
  "redaction_style": "solid_black",
  "confidence_threshold": 0.8,
  "multilingual_support": ["en"]
}
```

### Update Profile

Update an existing profile:

```bash
PUT /api/v1/profiles/{profile_name}
Content-Type: application/json

{
  "description": "Updated description",
  "confidence_threshold": 0.9
}
```

### Delete Profile

Delete a profile:

```bash
DELETE /api/v1/profiles/{profile_name}
```

## ✅ Validation Endpoints

### Document Integrity Validation

Validate document integrity using audit trails:

```bash
GET /api/v1/validate/{document_id}?audit_path=/path/to/audit.json
```

**Response:**
```json
{
  "document_id": "doc_123456789",
  "is_valid": true,
  "validation_timestamp": "2024-01-15T10:30:00Z",
  "integrity_check": true,
  "audit_trail_valid": true,
  "errors": [],
  "warnings": []
}
```

## 🔒 Authentication and Security

### API Key Authentication (Future)

```bash
# Include API key in headers
Authorization: Bearer your-api-key-here
```

### Rate Limiting

The API implements rate limiting to prevent abuse:

- **Processing endpoints**: 10 requests per minute per IP
- **Profile endpoints**: 100 requests per minute per IP
- **Health endpoints**: No limit

### CORS Support

The API includes CORS headers for web application integration:

```javascript
// JavaScript example
fetch('http://localhost:8000/api/v1/health')
  .then(response => response.json())
  .then(data => console.log(data));
```

## 📊 Error Handling

All API endpoints return consistent error responses:

```json
{
  "error": "validation_error",
  "message": "Profile 'nonexistent' not found",
  "details": {
    "available_profiles": ["default", "healthcare_hipaa"],
    "requested_profile": "nonexistent"
  }
}
```

### Common Error Codes

- **400 Bad Request**: Invalid request parameters
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation errors
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

## 🔧 Configuration

### Environment Variables

```bash
# Server configuration
GOPNIK_API_HOST=0.0.0.0
GOPNIK_API_PORT=8000
GOPNIK_API_WORKERS=4

# Security
GOPNIK_API_KEY=your-secret-key
GOPNIK_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Processing
GOPNIK_MAX_FILE_SIZE=100MB
GOPNIK_PROCESSING_TIMEOUT=300
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install gopnik[web]

EXPOSE 8000

CMD ["gopnik", "api", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t gopnik-api .
docker run -p 8000:8000 gopnik-api
```

## 📝 Integration Examples

### Python Client

```python
import requests
import json

# Health check
response = requests.get('http://localhost:8000/api/v1/health')
health = response.json()
print(f"System status: {health['status']}")

# Process document
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    data = {'profile_name': 'healthcare_hipaa'}
    
    response = requests.post(
        'http://localhost:8000/api/v1/process',
        files=files,
        data=data
    )
    
    result = response.json()
    print(f"Processing completed: {result['success']}")
    print(f"Detections found: {len(result['detections'])}")
```

### JavaScript/Node.js Client

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function processDocument() {
  const form = new FormData();
  form.append('file', fs.createReadStream('document.pdf'));
  form.append('profile_name', 'default');
  
  try {
    const response = await axios.post(
      'http://localhost:8000/api/v1/process',
      form,
      { headers: form.getHeaders() }
    );
    
    console.log('Processing result:', response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

processDocument();
```

### cURL Examples

```bash
# Health check
curl -X GET http://localhost:8000/api/v1/health

# Process document
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@document.pdf" \
  -F "profile_name=default"

# List profiles
curl -X GET http://localhost:8000/api/v1/profiles

# Create profile
curl -X POST http://localhost:8000/api/v1/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom",
    "description": "Custom profile",
    "text_rules": {"name": true, "email": true},
    "redaction_style": "solid_black"
  }'
```

## 🚀 Performance Tips

1. **Use appropriate confidence thresholds**: Higher thresholds = faster processing
2. **Batch processing**: More efficient for multiple documents
3. **Async processing**: Use job tracking for large files
4. **Caching**: Profile information is cached for better performance
5. **Resource limits**: Configure appropriate memory and CPU limits

## 📞 Support

- **API Documentation**: Available at `/docs` when server is running
- **GitHub Issues**: [Report API bugs](https://github.com/happy2234/gopnik/issues)
- **Discussions**: [API questions and feedback](https://github.com/happy2234/gopnik/discussions)