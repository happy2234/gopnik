# Gopnik Web Interface Manual

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [User Interface Guide](#user-interface-guide)
4. [Features and Capabilities](#features-and-capabilities)
5. [Security and Privacy](#security-and-privacy)
6. [Troubleshooting](#troubleshooting)
7. [Limitations](#limitations)

## Overview

The Gopnik Web Interface provides an intuitive, browser-based solution for document deidentification. Built with modern web technologies and the Cardio UI library, it offers a user-friendly way to process documents without requiring technical expertise.

### Key Features
- **Drag-and-Drop Interface**: Easy file upload with visual feedback
- **Real-Time Processing**: Live progress updates and status tracking
- **Profile Selection**: Choose from predefined redaction profiles
- **Instant Preview**: Preview detections before final processing
- **Secure Processing**: Temporary file handling with automatic cleanup
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices

### Supported Formats
- **Documents**: PDF files
- **Images**: PNG, JPEG, TIFF, BMP
- **Maximum File Size**: 50MB per file
- **Batch Processing**: Up to 10 files simultaneously

## Getting Started

### Accessing the Web Interface

#### Option 1: Public Demo
Visit the live demo at: **https://gopnik-demo.example.com**

#### Option 2: Local Installation
```bash
# Install Gopnik with web interface
pip install gopnik[web]

# Start local web server
gopnik web --host localhost --port 8000

# Access in browser
open http://localhost:8000
```

#### Option 3: Docker Container
```bash
# Run with Docker
docker run -p 8000:8000 gopnik/web:latest

# Access in browser
open http://localhost:8000
```

### System Requirements

**Browser Compatibility:**
- Chrome 90+ (recommended)
- Firefox 88+
- Safari 14+
- Edge 90+

**Network Requirements:**
- JavaScript enabled
- Cookies enabled for session management
- Minimum 1 Mbps upload speed for large files

## User Interface Guide

### Welcome Page

The welcome page provides an overview of Gopnik's capabilities and navigation options:

**Navigation Options:**
- **Web Demo**: Access the interactive processing interface
- **CLI Download**: Download command-line tools
- **Desktop Version**: Download native desktop application
- **Documentation**: Access comprehensive guides

**Feature Comparison Table:**
Compare capabilities across different Gopnik versions (Web, CLI, Desktop, API).

### Main Processing Interface

#### 1. File Upload Area

**Drag-and-Drop Zone:**
- Drag files directly onto the upload area
- Visual feedback with hover effects
- Support for multiple file selection
- File type and size validation

**File Browser:**
- Click "Choose Files" to open file browser
- Multi-select support with Ctrl/Cmd+click
- Preview selected files before upload

**Upload Progress:**
- Real-time upload progress bars
- File size and upload speed indicators
- Cancel upload option

#### 2. Profile Selection Panel

**Available Profiles:**
- **Default**: General-purpose PII detection
- **Healthcare**: HIPAA-compliant medical documents
- **Financial**: PCI DSS-compliant financial documents
- **Legal**: Legal document redaction
- **Custom**: User-defined profiles (if configured)

**Profile Information:**
- Hover over profiles to see detailed descriptions
- PII types detected by each profile
- Redaction styles and confidence thresholds

#### 3. Processing Options

**Detection Settings:**
- **Confidence Threshold**: Adjust sensitivity (0.1 - 1.0)
- **PII Types**: Enable/disable specific detection types
- **Redaction Style**: Choose from solid, blur, or pixelate

**Preview Options:**
- **Show Detections**: Highlight detected PII before redaction
- **Bounding Boxes**: Display detection boundaries
- **Confidence Scores**: Show detection confidence levels

#### 4. Processing Status

**Status Indicators:**
- **Queued**: File waiting for processing
- **Processing**: Active AI analysis and redaction
- **Complete**: Processing finished successfully
- **Error**: Processing failed with error details

**Progress Information:**
- Processing stage (Upload → Analysis → Redaction → Finalization)
- Estimated time remaining
- Number of detections found

#### 5. Results and Download

**Processing Results:**
- Summary of detections found
- Processing time and statistics
- Download links for redacted documents

**Download Options:**
- **Individual Files**: Download each processed file
- **Batch Download**: ZIP archive of all processed files
- **Audit Logs**: Download processing audit trails

### Help Sidebar

**Quick Help:**
- Step-by-step processing guide
- Keyboard shortcuts
- Common troubleshooting tips

**Documentation Links:**
- User guide and tutorials
- API documentation
- FAQ and support

**Contact Information:**
- Support email and chat
- GitHub repository links
- Community forums

## Features and Capabilities

### Document Processing

#### AI-Powered Detection
- **Computer Vision**: Detects faces, signatures, barcodes, QR codes
- **Natural Language Processing**: Identifies names, emails, phones, addresses
- **Hybrid Analysis**: Combines CV and NLP for comprehensive detection
- **Confidence Scoring**: Adjustable thresholds for precision control

#### Redaction Styles
- **Solid Redaction**: Complete black/white blocks
- **Blur Redaction**: Gaussian blur effect
- **Pixelate Redaction**: Pixelation effect
- **Custom Patterns**: Configurable redaction appearance

#### Document Formats
- **PDF Processing**: Multi-page PDF support with layout preservation
- **Image Processing**: High-resolution image handling
- **Batch Processing**: Multiple files in single session
- **Format Conversion**: Automatic format optimization

### User Experience Features

#### Interactive Elements
- **Real-Time Feedback**: Instant visual feedback for all actions
- **Progress Tracking**: Detailed progress indicators
- **Error Handling**: User-friendly error messages and recovery options
- **Responsive Design**: Optimized for all screen sizes

#### Accessibility
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: ARIA labels and semantic HTML
- **High Contrast Mode**: Enhanced visibility options
- **Font Size Controls**: Adjustable text sizing

#### Performance Optimization
- **Lazy Loading**: Efficient resource loading
- **Caching**: Smart caching for faster repeat operations
- **Compression**: Optimized file transfer
- **Background Processing**: Non-blocking UI operations

### Security Features

#### Data Protection
- **Encrypted Transfer**: HTTPS/TLS encryption for all communications
- **Temporary Storage**: Secure temporary file handling
- **Automatic Cleanup**: Files deleted after processing completion
- **No Data Retention**: No permanent storage of user documents

#### Privacy Controls
- **Session Management**: Secure session handling
- **Access Controls**: File access restrictions
- **Audit Logging**: Optional processing audit trails
- **GDPR Compliance**: European privacy regulation compliance

## Security and Privacy

### Data Handling

#### File Upload Security
- **Virus Scanning**: Automatic malware detection
- **File Type Validation**: Strict file format checking
- **Size Limits**: Maximum file size enforcement
- **Content Filtering**: Suspicious content detection

#### Processing Security
- **Isolated Processing**: Sandboxed document processing
- **Memory Protection**: Secure memory handling
- **Cryptographic Integrity**: Document integrity verification
- **Audit Trails**: Comprehensive processing logs

#### Data Cleanup
- **Automatic Deletion**: Files deleted after 1 hour
- **Secure Wiping**: Cryptographic file deletion
- **Memory Clearing**: Sensitive data cleared from memory
- **Session Cleanup**: Complete session data removal

### Privacy Guarantees

#### No Data Retention
- Documents are not stored permanently
- Processing data is not logged or analyzed
- User information is not collected or stored
- No tracking or analytics on document content

#### Compliance
- **HIPAA**: Healthcare document processing compliance
- **GDPR**: European privacy regulation compliance
- **PCI DSS**: Financial document security standards
- **SOC 2**: Security and availability controls

### Best Practices

#### For Sensitive Documents
1. Use local installation instead of public demo
2. Verify HTTPS connection before uploading
3. Clear browser cache after processing
4. Use private/incognito browsing mode
5. Download and verify audit logs

#### For High-Security Environments
1. Deploy on private network or VPN
2. Use custom SSL certificates
3. Enable additional authentication
4. Configure custom security headers
5. Implement network-level restrictions

## Troubleshooting

### Common Issues

#### Upload Problems

**Issue:** Files won't upload or upload fails
**Solutions:**
- Check file size (must be under 50MB)
- Verify file format is supported
- Ensure stable internet connection
- Try uploading one file at a time
- Clear browser cache and cookies

**Issue:** Upload is very slow
**Solutions:**
- Check internet connection speed
- Try uploading smaller files first
- Use wired connection instead of WiFi
- Close other browser tabs and applications
- Try different browser

#### Processing Issues

**Issue:** Processing gets stuck or fails
**Solutions:**
- Refresh the page and try again
- Try with a different file
- Check if file is corrupted
- Reduce confidence threshold
- Contact support with error details

**Issue:** No detections found in document
**Solutions:**
- Try different redaction profile
- Lower confidence threshold
- Verify document contains detectable PII
- Check document quality and resolution
- Try manual review of document content

#### Download Problems

**Issue:** Cannot download processed files
**Solutions:**
- Check browser download settings
- Disable popup blockers
- Try right-click "Save As"
- Clear browser cache
- Try different browser

**Issue:** Downloaded file is corrupted
**Solutions:**
- Try downloading again
- Check available disk space
- Disable browser extensions
- Try different download location
- Contact support for file recovery

### Browser-Specific Issues

#### Chrome
- Clear cache: Settings → Privacy → Clear browsing data
- Disable extensions: Settings → Extensions
- Reset settings: Settings → Advanced → Reset

#### Firefox
- Clear cache: Preferences → Privacy → Clear Data
- Disable add-ons: Add-ons → Extensions
- Refresh Firefox: Help → Troubleshooting Information

#### Safari
- Clear cache: Develop → Empty Caches
- Disable extensions: Safari → Preferences → Extensions
- Reset Safari: Safari → Reset Safari

### Error Messages

#### "File too large"
- Maximum file size is 50MB
- Compress or split large files
- Use CLI version for larger files

#### "Unsupported file format"
- Only PDF and image files supported
- Convert document to supported format
- Check file extension matches content

#### "Processing timeout"
- Large files may take longer to process
- Try with smaller files first
- Check internet connection stability
- Contact support if issue persists

#### "Server error"
- Temporary server issue
- Try again in a few minutes
- Check service status page
- Contact support if problem continues

### Getting Help

#### Self-Service Resources
- **FAQ**: Common questions and answers
- **User Guide**: Comprehensive documentation
- **Video Tutorials**: Step-by-step video guides
- **Community Forum**: User discussions and tips

#### Support Channels
- **Email Support**: support@gopnik.ai
- **Live Chat**: Available during business hours
- **GitHub Issues**: Technical bug reports
- **Community Discord**: Real-time community help

#### When Contacting Support
Include the following information:
- Browser type and version
- Operating system
- File type and size
- Error messages or screenshots
- Steps to reproduce the issue

## Limitations

### Technical Limitations

#### File Restrictions
- **Maximum File Size**: 50MB per file
- **Batch Limit**: 10 files per session
- **Processing Time**: 5-minute timeout per file
- **Concurrent Users**: May be limited during peak usage

#### Feature Limitations
- **No Custom Profiles**: Cannot create custom redaction profiles
- **Limited AI Models**: Subset of full AI capabilities
- **No API Access**: Web interface only, no programmatic access
- **Basic Audit Logs**: Simplified audit trail information

#### Browser Limitations
- **JavaScript Required**: Must have JavaScript enabled
- **Modern Browser**: Requires recent browser version
- **Local Storage**: Uses browser storage for temporary data
- **Network Dependent**: Requires stable internet connection

### Comparison with Other Versions

| Feature | Web Interface | CLI Tool | Desktop App | API |
|---------|---------------|----------|-------------|-----|
| File Size Limit | 50MB | 1GB+ | 1GB+ | 1GB+ |
| Batch Processing | 10 files | Unlimited | Unlimited | Unlimited |
| Custom Profiles | No | Yes | Yes | Yes |
| Offline Processing | No | Yes | Yes | No |
| Advanced AI Models | Limited | Full | Full | Full |
| Audit Trails | Basic | Full | Full | Full |
| Automation | No | Yes | Limited | Yes |

### When to Use Other Versions

#### Use CLI Tool When:
- Processing large files (>50MB)
- Batch processing many files
- Need custom redaction profiles
- Require offline processing
- Need advanced audit trails
- Automating workflows

#### Use Desktop App When:
- Regular document processing
- Need offline capabilities
- Prefer native application
- Require advanced features
- Need better performance

#### Use API When:
- Integrating with existing systems
- Building custom applications
- Need programmatic access
- Require automation
- Processing at scale

---

**Version:** 1.0.0  
**Last Updated:** September 2025  
**License:** MIT  
**Support:** support@gopnik.ai