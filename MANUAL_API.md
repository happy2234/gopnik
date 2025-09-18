# Gopnik REST API Manual

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Authentication](#authentication)
4. [API Reference](#api-reference)
5. [Client Libraries](#client-libraries)
6. [Integration Examples](#integration-examples)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Troubleshooting](#troubleshooting)

## Overview

The Gopnik REST API provides programmatic access to AI-powered document deidentification capabilities. Built with FastAPI, it offers high-performance, scalable document processing with comprehensive audit trails and security features.

### Key Features
- **RESTful Design**: Standard HTTP methods and status codes
- **OpenAPI Documentation**: Interactive API documentation
- **Async Processing**: Non-blocking operations for large files
- **Job Management**: Track processing status and results
- **Batch Operations**: Process multiple documents efficiently
- **Comprehensive Audit**: Detailed processing logs and integrity validation
- **Security**: Authentication, rate limiting, and secure file handling

### Base URL
- **Production**: `https://api.gopnik.ai/v1`
- **Local Development**: `http://localhost:8000/api/v1`

### API Versioning
Current version: **v1**  
All endpoints are prefixed with `/api/v1/`

## Getting Started

### Installation and Setup

#### Start API Server
```bash
# Install Gopnik with API support
pip install gopnik[api]

# Start API server
gopnik api --host 0.0.0.0 --port 8000

# Development mode with auto-reload
gopnik api --reload --log-level debug
```

#### Docker Deployment
```bash
# Run with Docker
docker run -p 8000:8000 gopnik/api:latest

# With custom configuration
docker run -p 8000:8000 -v /path/to/config:/app/config gopnik/api:latest
```

### Interactive Documentation

Access interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

### Quick Test

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-09-18T10:30:00Z"
}
```

## Authentication

### API Key Authentication

#### Obtaining API Key
```bash
# Generate API key (local installation)
gopnik generate-api-key --name "my-app"

# Output
{
  "api_key": "gk_1234567890abcdef",
  "name": "my-app",
  "created_at": "2025-09-18T10:30:00Z"
}
```

#### Using API Key
Include the API key in the `Authorization` header:

```bash
curl -H "Authorization: Bearer gk_1234567890abcdef" \
     http://localhost:8000/api/v1/health
```

### JWT Token Authentication

#### Login Endpoint
```bash
# Login with credentials
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Using JWT Token
```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
     http://localhost:8000/api/v1/health
```

## API Reference

### Health and Status

#### GET /health
Check API server health and status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-09-18T10:30:00Z",
  "uptime": 3600,
  "ai_engines": {
    "cv_engine": "ready",
    "nlp_engine": "ready"
  }
}
```

#### GET /status
Get detailed system status and metrics.

**Response:**
```json
{
  "system": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1
  },
  "processing": {
    "active_jobs": 3,
    "queued_jobs": 7,
    "completed_today": 156
  },
  "ai_models": {
    "cv_model_loaded": true,
    "nlp_model_loaded": true,
    "model_versions": {
      "cv": "2.1.0",
      "nlp": "1.8.3"
    }
  }
}
```

### Document Processing

#### POST /process
Process a single document for PII detection and redaction.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -H "Authorization: Bearer your-token" \
  -F "file=@document.pdf" \
  -F "profile_name=healthcare" \
  -F "confidence_threshold=0.8" \
  -F "dry_run=false"
```

**Parameters:**
- `file` (required): Document file to process
- `profile_name` (optional): Redaction profile name (default: "default")
- `confidence_threshold` (optional): Detection confidence threshold (0.0-1.0)
- `dry_run` (optional): Preview detections without redaction (default: false)
- `audit_enabled` (optional): Enable audit logging (default: true)

**Response:**
```json
{
  "job_id": "job_1234567890",
  "status": "completed",
  "success": true,
  "processing_time": 12.34,
  "detections": [
    {
      "type": "person_name",
      "text": "John Doe",
      "confidence": 0.95,
      "coordinates": {
        "x": 100,
        "y": 200,
        "width": 80,
        "height": 20
      },
      "page": 1
    }
  ],
  "output_url": "/api/v1/download/job_1234567890",
  "audit_log_url": "/api/v1/audit/job_1234567890"
}
```

#### POST /batch
Process multiple documents in batch mode.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/batch \
  -H "Authorization: Bearer your-token" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.pdf" \
  -F "profile_name=default" \
  -F "parallel_processing=true"
```

**Parameters:**
- `files` (required): Multiple document files
- `profile_name` (optional): Redaction profile for all files
- `parallel_processing` (optional): Enable parallel processing (default: true)
- `max_concurrent` (optional): Maximum concurrent jobs (default: 4)

**Response:**
```json
{
  "batch_id": "batch_1234567890",
  "status": "processing",
  "total_files": 2,
  "completed_files": 0,
  "failed_files": 0,
  "jobs": [
    {
      "job_id": "job_1234567891",
      "filename": "doc1.pdf",
      "status": "queued"
    },
    {
      "job_id": "job_1234567892",
      "filename": "doc2.pdf",
      "status": "queued"
    }
  ],
  "status_url": "/api/v1/batch/batch_1234567890/status"
}
```

### Job Management

#### GET /jobs/{job_id}
Get status and results of a processing job.

**Response:**
```json
{
  "job_id": "job_1234567890",
  "status": "completed",
  "created_at": "2025-09-18T10:30:00Z",
  "started_at": "2025-09-18T10:30:05Z",
  "completed_at": "2025-09-18T10:30:17Z",
  "processing_time": 12.34,
  "success": true,
  "error_message": null,
  "input_filename": "document.pdf",
  "output_url": "/api/v1/download/job_1234567890",
  "detections_count": 5,
  "audit_log_url": "/api/v1/audit/job_1234567890"
}
```

#### GET /jobs
List all jobs with filtering and pagination.

**Query Parameters:**
- `status`: Filter by job status (queued, processing, completed, failed)
- `limit`: Number of results per page (default: 50, max: 200)
- `offset`: Pagination offset (default: 0)
- `created_after`: Filter jobs created after timestamp
- `created_before`: Filter jobs created before timestamp

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "job_1234567890",
      "status": "completed",
      "created_at": "2025-09-18T10:30:00Z",
      "input_filename": "document.pdf",
      "processing_time": 12.34
    }
  ],
  "total": 156,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

#### DELETE /jobs/{job_id}
Cancel a queued or processing job.

**Response:**
```json
{
  "job_id": "job_1234567890",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

### File Download

#### GET /download/{job_id}
Download processed document.

**Response:** Binary file content with appropriate headers.

```bash
curl -H "Authorization: Bearer your-token" \
     http://localhost:8000/api/v1/download/job_1234567890 \
     -o redacted_document.pdf
```

#### GET /download/{job_id}/original
Download original document (if retention enabled).

#### GET /download/batch/{batch_id}
Download all processed files from a batch as ZIP archive.

### Profile Management

#### GET /profiles
List available redaction profiles.

**Response:**
```json
{
  "profiles": [
    {
      "name": "default",
      "description": "General-purpose PII detection",
      "version": "1.0",
      "pii_types": ["person_name", "email_address", "phone_number"],
      "created_at": "2025-09-18T10:30:00Z"
    },
    {
      "name": "healthcare",
      "description": "HIPAA-compliant medical document redaction",
      "version": "1.2",
      "pii_types": ["person_name", "ssn", "medical_record_number"],
      "created_at": "2025-09-18T10:30:00Z"
    }
  ]
}
```

#### GET /profiles/{profile_name}
Get detailed information about a specific profile.

**Response:**
```json
{
  "name": "healthcare",
  "description": "HIPAA-compliant medical document redaction",
  "version": "1.2",
  "pii_types": [
    {
      "name": "person_name",
      "enabled": true,
      "confidence_threshold": 0.8,
      "redaction_style": "solid"
    },
    {
      "name": "ssn",
      "enabled": true,
      "confidence_threshold": 0.9,
      "redaction_style": "solid"
    }
  ],
  "redaction_styles": {
    "solid": {
      "color": "black",
      "opacity": 1.0
    }
  }
}
```

#### POST /profiles
Create a new redaction profile.

**Request:**
```json
{
  "name": "custom_profile",
  "description": "Custom redaction profile",
  "based_on": "default",
  "pii_types": [
    {
      "name": "person_name",
      "enabled": true,
      "confidence_threshold": 0.8,
      "redaction_style": "blur"
    }
  ]
}
```

#### PUT /profiles/{profile_name}
Update an existing profile.

#### DELETE /profiles/{profile_name}
Delete a profile.

### Validation and Audit

#### GET /audit/{job_id}
Get audit log for a processing job.

**Response:**
```json
{
  "job_id": "job_1234567890",
  "audit_log": {
    "document_hash": "sha256:abc123...",
    "processing_started": "2025-09-18T10:30:05Z",
    "processing_completed": "2025-09-18T10:30:17Z",
    "profile_used": "healthcare",
    "detections": [
      {
        "type": "person_name",
        "confidence": 0.95,
        "coordinates": {"x": 100, "y": 200, "width": 80, "height": 20},
        "redacted": true
      }
    ],
    "signature": "rsa:def456...",
    "integrity_verified": true
  }
}
```

#### POST /validate
Validate document integrity and audit trail.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/validate \
  -H "Authorization: Bearer your-token" \
  -F "document=@redacted_document.pdf" \
  -F "audit_log=@audit.json" \
  -F "verify_signatures=true"
```

**Response:**
```json
{
  "validation_result": {
    "document_integrity": "valid",
    "audit_log_integrity": "valid",
    "signature_verification": "valid",
    "chain_of_custody": "complete",
    "validation_timestamp": "2025-09-18T10:30:00Z"
  },
  "details": {
    "document_hash_match": true,
    "audit_signature_valid": true,
    "processing_chain_complete": true
  }
}
```

## Client Libraries

### Python Client

#### Installation
```bash
pip install gopnik-client
```

#### Usage
```python
from gopnik_client import GopnikClient

# Initialize client
client = GopnikClient(
    base_url="http://localhost:8000/api/v1",
    api_key="gk_1234567890abcdef"
)

# Process document
with open("document.pdf", "rb") as f:
    result = client.process_document(
        file=f,
        profile_name="healthcare",
        confidence_threshold=0.8
    )

print(f"Job ID: {result.job_id}")
print(f"Status: {result.status}")

# Wait for completion
job = client.wait_for_completion(result.job_id, timeout=300)

# Download result
if job.success:
    client.download_file(job.job_id, "redacted_document.pdf")
```

### JavaScript/Node.js Client

#### Installation
```bash
npm install gopnik-client
```

#### Usage
```javascript
const GopnikClient = require('gopnik-client');

const client = new GopnikClient({
  baseURL: 'http://localhost:8000/api/v1',
  apiKey: 'gk_1234567890abcdef'
});

// Process document
const fs = require('fs');
const fileBuffer = fs.readFileSync('document.pdf');

client.processDocument({
  file: fileBuffer,
  filename: 'document.pdf',
  profileName: 'healthcare',
  confidenceThreshold: 0.8
}).then(result => {
  console.log('Job ID:', result.jobId);
  
  // Poll for completion
  return client.waitForCompletion(result.jobId);
}).then(job => {
  if (job.success) {
    return client.downloadFile(job.jobId);
  }
}).then(fileBuffer => {
  fs.writeFileSync('redacted_document.pdf', fileBuffer);
}).catch(error => {
  console.error('Error:', error);
});
```

### cURL Examples

#### Process Document
```bash
# Process single document
curl -X POST http://localhost:8000/api/v1/process \
  -H "Authorization: Bearer gk_1234567890abcdef" \
  -F "file=@document.pdf" \
  -F "profile_name=healthcare"

# Check job status
curl -H "Authorization: Bearer gk_1234567890abcdef" \
     http://localhost:8000/api/v1/jobs/job_1234567890

# Download result
curl -H "Authorization: Bearer gk_1234567890abcdef" \
     http://localhost:8000/api/v1/download/job_1234567890 \
     -o redacted_document.pdf
```

## Integration Examples

### Webhook Integration

#### Configure Webhook
```bash
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhook",
    "events": ["job.completed", "job.failed"],
    "secret": "webhook-secret"
  }'
```

#### Webhook Payload
```json
{
  "event": "job.completed",
  "timestamp": "2025-09-18T10:30:17Z",
  "data": {
    "job_id": "job_1234567890",
    "status": "completed",
    "success": true,
    "processing_time": 12.34,
    "detections_count": 5
  }
}
```

### Workflow Automation

#### GitHub Actions Example
```yaml
name: Process Documents
on:
  push:
    paths: ['documents/**/*.pdf']

jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Process Documents
        run: |
          for file in documents/*.pdf; do
            curl -X POST ${{ secrets.GOPNIK_API_URL }}/process \
              -H "Authorization: Bearer ${{ secrets.GOPNIK_API_KEY }}" \
              -F "file=@$file" \
              -F "profile_name=default"
          done
```

#### Jenkins Pipeline
```groovy
pipeline {
    agent any
    
    stages {
        stage('Process Documents') {
            steps {
                script {
                    def files = findFiles(glob: 'documents/*.pdf')
                    files.each { file ->
                        sh """
                            curl -X POST ${GOPNIK_API_URL}/process \
                              -H "Authorization: Bearer ${GOPNIK_API_KEY}" \
                              -F "file=@${file.path}" \
                              -F "profile_name=healthcare"
                        """
                    }
                }
            }
        }
    }
}
```

### Database Integration

#### Store Results in Database
```python
import requests
import sqlite3

def process_and_store(file_path, profile_name):
    # Process document
    with open(file_path, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/api/v1/process',
            headers={'Authorization': 'Bearer your-token'},
            files={'file': f},
            data={'profile_name': profile_name}
        )
    
    result = response.json()
    
    # Store in database
    conn = sqlite3.connect('processing_results.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO processing_jobs 
        (job_id, filename, status, detections_count, processing_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        result['job_id'],
        file_path,
        result['status'],
        len(result['detections']),
        result['processing_time']
    ))
    
    conn.commit()
    conn.close()
    
    return result['job_id']
```

## Error Handling

### HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **413 Payload Too Large**: File size exceeds limit
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid file format",
    "details": {
      "field": "file",
      "allowed_formats": ["pdf", "png", "jpg", "jpeg", "tiff", "bmp"]
    },
    "timestamp": "2025-09-18T10:30:00Z",
    "request_id": "req_1234567890"
  }
}
```

### Common Error Codes

#### Authentication Errors
- `INVALID_API_KEY`: API key is invalid or expired
- `MISSING_AUTHORIZATION`: Authorization header missing
- `TOKEN_EXPIRED`: JWT token has expired

#### Validation Errors
- `INVALID_FILE_FORMAT`: Unsupported file format
- `FILE_TOO_LARGE`: File exceeds maximum size limit
- `MISSING_REQUIRED_FIELD`: Required parameter missing
- `INVALID_PROFILE_NAME`: Redaction profile not found

#### Processing Errors
- `PROCESSING_FAILED`: Document processing failed
- `AI_ENGINE_ERROR`: AI model processing error
- `INSUFFICIENT_MEMORY`: Not enough memory to process file
- `TIMEOUT_ERROR`: Processing timeout exceeded

#### Rate Limiting Errors
- `RATE_LIMIT_EXCEEDED`: Too many requests per time window
- `QUOTA_EXCEEDED`: Monthly processing quota exceeded
- `CONCURRENT_LIMIT_EXCEEDED`: Too many concurrent jobs

### Error Handling Best Practices

#### Retry Logic
```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
        backoff_factor=1
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Usage
session = create_session_with_retries()
response = session.post(url, data=data, timeout=30)
```

#### Exponential Backoff
```python
def process_with_backoff(file_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, files={'file': open(file_path, 'rb')})
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
                continue
            else:
                raise
        
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
    
    raise Exception("Max retries exceeded")
```

## Rate Limiting

### Rate Limits

#### Default Limits
- **Requests per minute**: 100
- **Requests per hour**: 1000
- **Requests per day**: 10000
- **Concurrent jobs**: 10
- **File size limit**: 100MB
- **Monthly processing quota**: 1000 documents

#### Premium Limits
- **Requests per minute**: 500
- **Requests per hour**: 5000
- **Requests per day**: 50000
- **Concurrent jobs**: 50
- **File size limit**: 1GB
- **Monthly processing quota**: 10000 documents

### Rate Limit Headers

Response headers include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1632150000
X-RateLimit-Window: 60
```

### Handling Rate Limits

#### Check Rate Limit Status
```python
def check_rate_limit(response):
    if 'X-RateLimit-Remaining' in response.headers:
        remaining = int(response.headers['X-RateLimit-Remaining'])
        if remaining < 10:
            print(f"Warning: Only {remaining} requests remaining")
    
    if response.status_code == 429:
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        wait_time = reset_time - int(time.time())
        print(f"Rate limited. Waiting {wait_time} seconds...")
        time.sleep(wait_time)
```

## Troubleshooting

### Common Issues

#### Connection Problems

**Issue:** Cannot connect to API server
**Solutions:**
- Verify server is running: `curl http://localhost:8000/api/v1/health`
- Check firewall settings
- Verify correct host and port
- Check network connectivity

#### Authentication Issues

**Issue:** 401 Unauthorized errors
**Solutions:**
- Verify API key is correct
- Check Authorization header format
- Ensure API key has required permissions
- Check if API key has expired

#### File Upload Problems

**Issue:** File upload fails or times out
**Solutions:**
- Check file size (must be under limit)
- Verify file format is supported
- Increase request timeout
- Try uploading smaller files first

#### Processing Failures

**Issue:** Jobs fail with processing errors
**Solutions:**
- Check file is not corrupted
- Verify sufficient server resources
- Try with different redaction profile
- Check server logs for detailed errors

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Start API server with debug logging
gopnik api --log-level debug

# Check server logs
tail -f /var/log/gopnik/api.log
```

### Performance Optimization

#### Client-Side Optimization
```python
# Use connection pooling
session = requests.Session()

# Set appropriate timeouts
response = session.post(url, data=data, timeout=(5, 30))

# Process files in parallel
from concurrent.futures import ThreadPoolExecutor

def process_file(file_path):
    with open(file_path, 'rb') as f:
        return session.post(url, files={'file': f})

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_file, f) for f in file_list]
    results = [future.result() for future in futures]
```

#### Server-Side Optimization
```bash
# Increase worker processes
gopnik api --workers 4

# Adjust memory limits
export GOPNIK_MAX_MEMORY=8GB
gopnik api

# Use GPU acceleration
export GOPNIK_AI_DEVICE=cuda
gopnik api
```

### Getting Help

#### Support Resources
- **API Documentation**: Interactive docs at `/docs` endpoint
- **GitHub Issues**: Report bugs and request features
- **Community Forum**: Get help from other developers
- **Email Support**: support@gopnik.ai

#### When Contacting Support
Include the following information:
- API endpoint and HTTP method
- Request headers and body
- Response status code and body
- Server logs (if available)
- Steps to reproduce the issue

---

**Version:** 1.0.0  
**Last Updated:** September 2025  
**License:** MIT  
**Support:** support@gopnik.ai