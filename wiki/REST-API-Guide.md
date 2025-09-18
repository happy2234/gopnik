# REST API Guide

The Gopnik REST API provides programmatic access to all deidentification features with comprehensive endpoints for document processing, profile management, and system monitoring.

## 📖 Complete API Documentation

For comprehensive API documentation, see our **[API Manual](../MANUAL_API.md)** which includes:
- Complete endpoint reference with examples
- Authentication and security
- Client libraries for Python, JavaScript, and more
- Integration patterns and best practices
- Error handling and troubleshooting
- Rate limiting and performance optimization

## 🚀 Quick Start

### Starting the API Server

```bash
# Basic startup
gopnik api

# Custom configuration
gopnik api --host 0.0.0.0 --port 8080 --reload
```

### First API Call

```bash
# Check system health
curl http://localhost:8000/api/v1/health

# Process a document
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@document.pdf" \
  -F "profile_name=default"
```

## 📖 API Documentation

- **Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

## 🔍 Core Endpoints

### Health and Monitoring

```bash
# Comprehensive health check
GET /api/v1/health

# Simple status check
GET /api/v1/status
```

**Health Response Example:**
```json
{
  "status": "healthy",
  "components": {
    "document_analyzer": "available",
    "ai_engine": "available",
    "redaction_engine": "available"
  },
  "supported_formats": ["pdf", "png", "jpeg"],
  "statistics": {
    "total_processed": 150,
    "success_rate": 98.0
  }
}
```

### Document Processing

```bash
# Single document processing
POST /api/v1/process
Content-Type: multipart/form-data

# Batch processing
POST /api/v1/batch
Content-Type: multipart/form-data

# Job status tracking
GET /api/v1/jobs/{job_id}
GET /api/v1/jobs?status=running
```

### Profile Management

```bash
# List all profiles
GET /api/v1/profiles

# Get specific profile
GET /api/v1/profiles/{profile_name}

# Create new profile
POST /api/v1/profiles

# Update profile
PUT /api/v1/profiles/{profile_name}

# Delete profile
DELETE /api/v1/profiles/{profile_name}
```

### Document Validation

```bash
# Validate document integrity
GET /api/v1/validate/{document_id}?audit_path=/path/to/audit.json
```

## 💻 Client Examples

### Python

```python
import requests

# Health check
response = requests.get('http://localhost:8000/api/v1/health')
print(f"Status: {response.json()['status']}")

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
    print(f"Success: {result['success']}")
    print(f"Detections: {len(result['detections'])}")
```

### JavaScript/Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function processDocument() {
  const form = new FormData();
  form.append('file', fs.createReadStream('document.pdf'));
  form.append('profile_name', 'default');
  
  const response = await axios.post(
    'http://localhost:8000/api/v1/process',
    form,
    { headers: form.getHeaders() }
  );
  
  console.log('Result:', response.data);
}
```

### cURL

```bash
# Process document with custom settings
curl -X POST http://localhost:8000/api/v1/process \
  -F "file=@sensitive_document.pdf" \
  -F "profile_name=healthcare_hipaa" \
  -F "confidence_threshold=0.9"

# Create custom profile
curl -X POST http://localhost:8000/api/v1/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "legal_docs",
    "description": "Profile for legal documents",
    "text_rules": {
      "name": true,
      "email": true,
      "phone": true,
      "address": true
    },
    "redaction_style": "solid_black",
    "confidence_threshold": 0.8
  }'
```

## 🔒 Security Features

### CORS Support
- Configurable origins for web applications
- Preflight request handling
- Credential support

### Rate Limiting
- Processing endpoints: 10 requests/minute
- Profile endpoints: 100 requests/minute
- Health endpoints: Unlimited

### Error Handling
Consistent error response format:
```json
{
  "error": "validation_error",
  "message": "Profile not found",
  "details": {
    "available_profiles": ["default", "healthcare"]
  }
}
```

## 🚀 Deployment

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install gopnik[web]

EXPOSE 8000
CMD ["gopnik", "api", "--host", "0.0.0.0"]
```

### Environment Variables

```bash
GOPNIK_API_HOST=0.0.0.0
GOPNIK_API_PORT=8000
GOPNIK_MAX_FILE_SIZE=100MB
GOPNIK_PROCESSING_TIMEOUT=300
```

### Production Setup

```bash
# Using Gunicorn
pip install gunicorn
gunicorn gopnik.interfaces.api.app:app -w 4 -b 0.0.0.0:8000

# Using Docker Compose
version: '3.8'
services:
  gopnik-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOPNIK_API_HOST=0.0.0.0
      - GOPNIK_API_PORT=8000
```

## 📊 Response Formats

### Processing Response

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
        "x1": 100, "y1": 200,
        "x2": 300, "y2": 220
      },
      "page_number": 0,
      "detection_method": "nlp"
    }
  ],
  "metrics": {
    "total_time": 3.2,
    "detection_time": 1.8,
    "pages_processed": 5,
    "detections_found": 12
  },
  "profile_name": "healthcare_hipaa",
  "output_available": true
}
```

### Batch Processing Response

```json
{
  "id": "batch_123456789",
  "total_documents": 25,
  "processed_documents": 23,
  "failed_documents": 2,
  "success_rate": 92.0,
  "results": [...],
  "is_completed": true
}
```

## 🔧 Advanced Features

### Async Job Processing
- Large file processing with job tracking
- Progress monitoring
- Result retrieval when complete

### Profile Inheritance
- Create profiles based on existing ones
- Override specific rules
- Validation and conflict resolution

### Audit Trail Integration
- Automatic audit log generation
- Cryptographic signatures
- Integrity validation endpoints

## 📈 Performance Tips

1. **Use appropriate confidence thresholds**
2. **Batch process multiple documents**
3. **Monitor job queues for large files**
4. **Cache profile configurations**
5. **Configure resource limits appropriately**

## 🛠️ Troubleshooting

### Common Issues

**Server won't start:**
```bash
# Check port availability
netstat -tulpn | grep :8000

# Check dependencies
pip install gopnik[web]
```

**Processing fails:**
```bash
# Check file format support
curl http://localhost:8000/api/v1/health

# Verify profile exists
curl http://localhost:8000/api/v1/profiles
```

**Memory issues:**
```bash
# Monitor resource usage
docker stats gopnik-api

# Adjust processing limits
export GOPNIK_MAX_FILE_SIZE=50MB
```

## 📞 Support

- **API Issues**: [GitHub Issues](https://github.com/happy2234/gopnik/issues)
- **Integration Help**: [GitHub Discussions](https://github.com/happy2234/gopnik/discussions)
- **Documentation**: [Official Docs](https://happy2234.github.io/gopnik/)

## 🔗 Related Pages

- **[CLI Usage Guide](CLI-Usage-Guide)**: Command-line interface
- **[Web Demo Tutorial](Web-Demo-Tutorial)**: Web interface
- **[API Integration Examples](API-Integration-Examples)**: More examples
- **[Security Configuration](Security-Configuration)**: Security setup