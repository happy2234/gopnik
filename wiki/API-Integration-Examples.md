# API Integration Examples

This page provides comprehensive examples for integrating Gopnik's REST API into various applications and workflows.

## 📖 Complete Integration Guide

For comprehensive API integration documentation, see our **[API Manual](../MANUAL_API.md)** which includes:
- Complete client library examples (Python, JavaScript, cURL)
- Real-world integration patterns
- Webhook integration examples
- Workflow automation with GitHub Actions, Jenkins
- Database integration patterns
- Error handling and retry strategies

## 🎯 Real-World Scenarios

Also check our **[Usage Scenarios](../SCENARIOS.md)** for detailed examples including:
- Healthcare HIPAA compliance workflows
- Legal document processing
- Financial PCI DSS compliance
- Government document declassification
- Corporate HR document processing
- Research data anonymization

## 🐍 Python Integration

### Basic Document Processing

```python
import requests
import json
from pathlib import Path

class GopnikClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """Check API health status."""
        response = self.session.get(f"{self.base_url}/api/v1/health")
        return response.json()
    
    def process_document(self, file_path, profile_name="default", 
                        confidence_threshold=None):
        """Process a single document."""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'profile_name': profile_name}
            
            if confidence_threshold:
                data['confidence_threshold'] = confidence_threshold
            
            response = self.session.post(
                f"{self.base_url}/api/v1/process",
                files=files,
                data=data
            )
            
            return response.json()
    
    def get_profiles(self):
        """Get all available profiles."""
        response = self.session.get(f"{self.base_url}/api/v1/profiles")
        return response.json()
    
    def create_profile(self, profile_config):
        """Create a new redaction profile."""
        response = self.session.post(
            f"{self.base_url}/api/v1/profiles",
            json=profile_config
        )
        return response.json()

# Usage example
client = GopnikClient()

# Check if API is healthy
health = client.health_check()
print(f"API Status: {health['status']}")

# Process a document
result = client.process_document(
    "sensitive_document.pdf",
    profile_name="healthcare_hipaa",
    confidence_threshold=0.9
)

print(f"Processing successful: {result['success']}")
print(f"Detections found: {len(result['detections'])}")

# Create custom profile
custom_profile = {
    "name": "financial_docs",
    "description": "Profile for financial documents",
    "text_rules": {
        "name": True,
        "ssn": True,
        "credit_card": True,
        "bank_account": True
    },
    "visual_rules": {
        "signature": True,
        "face": False
    },
    "redaction_style": "solid_black",
    "confidence_threshold": 0.85
}

profile_result = client.create_profile(custom_profile)
print(f"Profile created: {profile_result}")
```

### Async Processing with Job Tracking

```python
import asyncio
import aiohttp
import time

class AsyncGopnikClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    async def process_large_document(self, file_path, profile_name="default"):
        """Process large document with job tracking."""
        async with aiohttp.ClientSession() as session:
            # Submit processing job
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f)
                data.add_field('profile_name', profile_name)
                
                async with session.post(
                    f"{self.base_url}/api/v1/process",
                    data=data
                ) as response:
                    result = await response.json()
                    
                    if 'job_id' in result:
                        # Track job progress
                        return await self.track_job(session, result['job_id'])
                    else:
                        # Immediate result
                        return result
    
    async def track_job(self, session, job_id):
        """Track job progress until completion."""
        while True:
            async with session.get(
                f"{self.base_url}/api/v1/jobs/{job_id}"
            ) as response:
                job_status = await response.json()
                
                print(f"Job {job_id}: {job_status['status']} "
                      f"({job_status['progress']:.1f}%)")
                
                if job_status['status'] in ['completed', 'failed']:
                    return job_status
                
                await asyncio.sleep(2)  # Poll every 2 seconds

# Usage
async def main():
    client = AsyncGopnikClient()
    result = await client.process_large_document(
        "large_document.pdf",
        "healthcare_hipaa"
    )
    print(f"Final result: {result}")

# Run async processing
asyncio.run(main())
```

### Batch Processing Workflow

```python
import os
import zipfile
from pathlib import Path

def batch_process_directory(directory_path, profile_name="default"):
    """Process all documents in a directory."""
    client = GopnikClient()
    
    # Create zip archive of documents
    zip_path = f"{directory_path}.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, directory_path))
    
    # Submit batch processing
    with open(zip_path, 'rb') as f:
        files = {'archive': f}
        data = {
            'profile_name': profile_name,
            'recursive': True
        }
        
        response = requests.post(
            f"{client.base_url}/api/v1/batch",
            files=files,
            data=data
        )
        
        result = response.json()
    
    # Clean up zip file
    os.remove(zip_path)
    
    return result

# Process entire directory
batch_result = batch_process_directory(
    "/path/to/documents",
    "healthcare_hipaa"
)

print(f"Batch processing completed:")
print(f"Total documents: {batch_result['total_documents']}")
print(f"Successful: {batch_result['processed_documents']}")
print(f"Failed: {batch_result['failed_documents']}")
print(f"Success rate: {batch_result['success_rate']:.1f}%")
```

## 🌐 JavaScript/Node.js Integration

### Express.js Middleware

```javascript
const express = require('express');
const multer = require('multer');
const FormData = require('form-data');
const axios = require('axios');
const fs = require('fs');

const app = express();
const upload = multer({ dest: 'uploads/' });

// Gopnik API client
class GopnikClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async processDocument(filePath, profileName = 'default') {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    form.append('profile_name', profileName);

    try {
      const response = await axios.post(
        `${this.baseUrl}/api/v1/process`,
        form,
        { headers: form.getHeaders() }
      );
      return response.data;
    } catch (error) {
      throw new Error(`Processing failed: ${error.response?.data?.message || error.message}`);
    }
  }

  async getProfiles() {
    const response = await axios.get(`${this.baseUrl}/api/v1/profiles`);
    return response.data;
  }

  async healthCheck() {
    const response = await axios.get(`${this.baseUrl}/api/v1/health`);
    return response.data;
  }
}

const gopnikClient = new GopnikClient();

// Middleware for document processing
app.post('/api/redact', upload.single('document'), async (req, res) => {
  try {
    const { profile = 'default', confidence_threshold } = req.body;
    
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    // Process document with Gopnik
    const result = await gopnikClient.processDocument(
      req.file.path,
      profile
    );

    // Clean up uploaded file
    fs.unlinkSync(req.file.path);

    res.json({
      success: result.success,
      detections: result.detections.length,
      processing_time: result.metrics?.total_time,
      profile_used: result.profile_name
    });

  } catch (error) {
    console.error('Processing error:', error);
    res.status(500).json({ 
      error: 'Processing failed',
      message: error.message 
    });
  }
});

// Health check endpoint
app.get('/api/health', async (req, res) => {
  try {
    const health = await gopnikClient.healthCheck();
    res.json(health);
  } catch (error) {
    res.status(503).json({ 
      status: 'unhealthy',
      error: error.message 
    });
  }
});

// Get available profiles
app.get('/api/profiles', async (req, res) => {
  try {
    const profiles = await gopnikClient.getProfiles();
    res.json(profiles);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

### React Frontend Integration

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const DocumentProcessor = () => {
  const [file, setFile] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState('default');
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    // Load available profiles
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      const response = await axios.get('/api/profiles');
      setProfiles(response.data);
    } catch (error) {
      console.error('Failed to load profiles:', error);
    }
  };

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const processDocument = async () => {
    if (!file) return;

    setProcessing(true);
    setResult(null);

    const formData = new FormData();
    formData.append('document', file);
    formData.append('profile', selectedProfile);

    try {
      const response = await axios.post('/api/redact', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setResult(response.data);
    } catch (error) {
      console.error('Processing failed:', error);
      setResult({ 
        success: false, 
        error: error.response?.data?.message || 'Processing failed' 
      });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="document-processor">
      <h2>Document Redaction</h2>
      
      <div className="upload-section">
        <input
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={handleFileChange}
        />
        
        <select
          value={selectedProfile}
          onChange={(e) => setSelectedProfile(e.target.value)}
        >
          {profiles.map(profile => (
            <option key={profile.name} value={profile.name}>
              {profile.name} - {profile.description}
            </option>
          ))}
        </select>
        
        <button
          onClick={processDocument}
          disabled={!file || processing}
        >
          {processing ? 'Processing...' : 'Redact Document'}
        </button>
      </div>

      {result && (
        <div className="result-section">
          {result.success ? (
            <div className="success">
              <h3>Processing Completed</h3>
              <p>Detections found: {result.detections}</p>
              <p>Processing time: {result.processing_time}s</p>
              <p>Profile used: {result.profile_used}</p>
            </div>
          ) : (
            <div className="error">
              <h3>Processing Failed</h3>
              <p>{result.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DocumentProcessor;
```

## 🔧 Shell Script Integration

### Batch Processing Script

```bash
#!/bin/bash

# Gopnik API batch processing script
# Usage: ./batch_process.sh /path/to/documents healthcare_hipaa

GOPNIK_API_URL="http://localhost:8000"
DOCUMENTS_DIR="$1"
PROFILE_NAME="${2:-default}"

if [ -z "$DOCUMENTS_DIR" ]; then
    echo "Usage: $0 <documents_directory> [profile_name]"
    exit 1
fi

# Check API health
echo "Checking Gopnik API health..."
health_response=$(curl -s "$GOPNIK_API_URL/api/v1/health")
status=$(echo "$health_response" | jq -r '.status')

if [ "$status" != "healthy" ]; then
    echo "API is not healthy: $status"
    exit 1
fi

echo "API is healthy. Starting batch processing..."

# Create temporary zip file
temp_zip="/tmp/gopnik_batch_$(date +%s).zip"
cd "$DOCUMENTS_DIR"
zip -r "$temp_zip" . -i "*.pdf" "*.png" "*.jpg" "*.jpeg"

# Submit batch processing
echo "Submitting batch processing job..."
response=$(curl -s -X POST "$GOPNIK_API_URL/api/v1/batch" \
    -F "archive=@$temp_zip" \
    -F "profile_name=$PROFILE_NAME" \
    -F "recursive=true")

# Parse response
job_id=$(echo "$response" | jq -r '.job_id // empty')

if [ -n "$job_id" ]; then
    echo "Job submitted with ID: $job_id"
    
    # Track job progress
    while true; do
        job_status=$(curl -s "$GOPNIK_API_URL/api/v1/jobs/$job_id")
        status=$(echo "$job_status" | jq -r '.status')
        progress=$(echo "$job_status" | jq -r '.progress')
        
        echo "Job $job_id: $status ($progress%)"
        
        if [ "$status" = "completed" ] || [ "$status" = "failed" ]; then
            break
        fi
        
        sleep 5
    done
    
    # Get final result
    if [ "$status" = "completed" ]; then
        result=$(echo "$job_status" | jq -r '.result')
        total=$(echo "$result" | jq -r '.total_documents')
        processed=$(echo "$result" | jq -r '.processed_documents')
        failed=$(echo "$result" | jq -r '.failed_documents')
        
        echo "Batch processing completed:"
        echo "  Total documents: $total"
        echo "  Processed: $processed"
        echo "  Failed: $failed"
    else
        echo "Batch processing failed"
        exit 1
    fi
else
    # Immediate result
    total=$(echo "$response" | jq -r '.total_documents')
    processed=$(echo "$response" | jq -r '.processed_documents')
    
    echo "Batch processing completed immediately:"
    echo "  Total documents: $total"
    echo "  Processed: $processed"
fi

# Clean up
rm -f "$temp_zip"
echo "Batch processing complete!"
```

### Health Monitoring Script

```bash
#!/bin/bash

# Gopnik API health monitoring script
# Usage: ./monitor_health.sh [interval_seconds]

GOPNIK_API_URL="http://localhost:8000"
INTERVAL="${1:-30}"

echo "Monitoring Gopnik API health (checking every ${INTERVAL}s)..."
echo "Press Ctrl+C to stop"

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Check health
    health_response=$(curl -s --max-time 10 "$GOPNIK_API_URL/api/v1/health" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        status=$(echo "$health_response" | jq -r '.status // "unknown"')
        total_processed=$(echo "$health_response" | jq -r '.statistics.total_processed // 0')
        success_rate=$(echo "$health_response" | jq -r '.statistics.success_rate // 0')
        
        echo "[$timestamp] Status: $status | Processed: $total_processed | Success Rate: $success_rate%"
        
        # Check for warnings
        warnings=$(echo "$health_response" | jq -r '.warnings[]? // empty')
        if [ -n "$warnings" ]; then
            echo "  Warnings: $warnings"
        fi
    else
        echo "[$timestamp] Status: UNREACHABLE"
    fi
    
    sleep "$INTERVAL"
done
```

## 🐳 Docker Integration

### Docker Compose with API

```yaml
version: '3.8'

services:
  gopnik-api:
    image: gopnik:latest
    ports:
      - "8000:8000"
    environment:
      - GOPNIK_API_HOST=0.0.0.0
      - GOPNIK_API_PORT=8000
      - GOPNIK_MAX_FILE_SIZE=100MB
    volumes:
      - ./profiles:/app/profiles
      - ./output:/app/output
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - gopnik-api
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gopnik-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gopnik-api
  template:
    metadata:
      labels:
        app: gopnik-api
    spec:
      containers:
      - name: gopnik-api
        image: gopnik:latest
        ports:
        - containerPort: 8000
        env:
        - name: GOPNIK_API_HOST
          value: "0.0.0.0"
        - name: GOPNIK_API_PORT
          value: "8000"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/status
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: gopnik-api-service
spec:
  selector:
    app: gopnik-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 📊 Monitoring and Analytics

### Prometheus Metrics Integration

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import requests
import time

# Metrics
processing_requests = Counter('gopnik_processing_requests_total', 
                            'Total processing requests', ['profile', 'status'])
processing_duration = Histogram('gopnik_processing_duration_seconds',
                               'Processing duration')
active_jobs = Gauge('gopnik_active_jobs', 'Number of active jobs')

def monitor_gopnik_api():
    """Monitor Gopnik API and export metrics."""
    gopnik_url = "http://localhost:8000"
    
    while True:
        try:
            # Get health status
            health = requests.get(f"{gopnik_url}/api/v1/health").json()
            
            # Update metrics
            stats = health.get('statistics', {})
            processing_requests._value._value = stats.get('total_processed', 0)
            
            # Get active jobs
            jobs = requests.get(f"{gopnik_url}/api/v1/jobs").json()
            active_count = len([j for j in jobs.get('jobs', []) 
                              if j['status'] in ['pending', 'running']])
            active_jobs.set(active_count)
            
        except Exception as e:
            print(f"Monitoring error: {e}")
        
        time.sleep(30)

# Start Prometheus metrics server
start_http_server(8001)
monitor_gopnik_api()
```

## 🔗 Related Resources

- **[REST API Guide](REST-API-Guide)**: Complete API documentation
- **[CLI Usage Guide](CLI-Usage-Guide)**: Command-line interface
- **[Security Configuration](Security-Configuration)**: Security setup
- **[Performance Tuning](Performance-Tuning)**: Optimization tips