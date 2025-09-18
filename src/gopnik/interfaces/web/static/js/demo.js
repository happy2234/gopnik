/**
 * Demo page JavaScript functionality
 * Implements drag-and-drop, file processing, and real-time status updates
 */

class GopnikDemo {
    constructor() {
        this.currentFile = null;
        this.selectedProfile = 'default';
        this.processingJob = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.setupDragAndDrop();
    }
    
    initializeElements() {
        // Main elements
        this.dropzone = document.getElementById('dropzone');
        this.fileInput = document.getElementById('fileInput');
        this.fileInfo = document.getElementById('fileInfo');
        this.processBtn = document.getElementById('processBtn');
        
        // Status elements
        this.processingStatus = document.getElementById('processingStatus');
        this.progressFill = document.getElementById('progressFill');
        this.progressPercent = document.getElementById('progressPercent');
        this.progressStatus = document.getElementById('progressStatus');
        
        // Results elements
        this.resultsSection = document.getElementById('resultsSection');
        this.piiCount = document.getElementById('piiCount');
        this.redactionCount = document.getElementById('redactionCount');
        this.confidenceScore = document.getElementById('confidenceScore');
        
        // Profile options
        this.profileOptions = document.querySelectorAll('.profile-option');
    }
    
    setupEventListeners() {
        // File input
        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });
        
        // Process button
        this.processBtn.addEventListener('click', () => {
            this.startProcessing();
        });
        
        // Profile selection
        this.profileOptions.forEach(option => {
            option.addEventListener('click', () => {
                this.selectProfile(option.dataset.profile);
            });
        });
        
        // Results buttons
        document.getElementById('downloadBtn')?.addEventListener('click', () => {
            this.downloadResult();
        });
        
        document.getElementById('previewBtn')?.addEventListener('click', () => {
            this.showPreview();
        });
        
        document.getElementById('auditBtn')?.addEventListener('click', () => {
            this.showAuditTrail();
        });
    }
    
    setupDragAndDrop() {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropzone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });
        
        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropzone.addEventListener(eventName, () => {
                this.dropzone.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            this.dropzone.addEventListener(eventName, () => {
                this.dropzone.classList.remove('dragover');
            }, false);
        });
        
        // Handle dropped files
        this.dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        }, false);
        
        // Handle click to select file
        this.dropzone.addEventListener('click', () => {
            this.fileInput.click();
        });
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    handleFile(file) {
        // Validate file type
        const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/tiff'];
        if (!allowedTypes.includes(file.type)) {
            this.showError('Please select a PDF, PNG, JPG, or TIFF file.');
            return;
        }
        
        // Validate file size (10MB limit)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            this.showError('File size must be less than 10MB.');
            return;
        }
        
        this.currentFile = file;
        this.displayFileInfo(file);
        this.processBtn.disabled = false;
        
        // Hide dropzone and show file info
        this.dropzone.style.display = 'none';
        this.fileInfo.style.display = 'block';
    }
    
    displayFileInfo(file) {
        const fileName = this.fileInfo.querySelector('.file-name');
        const fileSize = this.fileInfo.querySelector('.file-size');
        
        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    selectProfile(profileName) {
        this.selectedProfile = profileName;
        
        // Update UI
        this.profileOptions.forEach(option => {
            option.classList.remove('active');
        });
        
        document.querySelector(`[data-profile="${profileName}"]`).classList.add('active');
    }
    
    removeFile() {
        this.currentFile = null;
        this.processBtn.disabled = true;
        
        // Show dropzone and hide file info
        this.dropzone.style.display = 'block';
        this.fileInfo.style.display = 'none';
        
        // Reset file input
        this.fileInput.value = '';
    }
    
    async startProcessing() {
        if (!this.currentFile) return;
        
        // Show processing status
        this.processingStatus.style.display = 'block';
        this.resultsSection.style.display = 'none';
        
        // Disable process button
        this.processBtn.disabled = true;
        
        try {
            // Create form data
            const formData = new FormData();
            formData.append('file', this.currentFile);
            formData.append('profile', this.selectedProfile);
            formData.append('preview_mode', document.getElementById('previewMode').checked);
            formData.append('audit_trail', document.getElementById('auditTrail').checked);
            
            // Start processing
            const response = await fetch('/api/web/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.job_id) {
                // Start polling for job status
                this.processingJob = result.job_id;
                this.pollJobStatus();
            } else {
                // Direct processing result
                this.handleProcessingComplete(result);
            }
            
        } catch (error) {
            console.error('Processing error:', error);
            this.showError('An error occurred during processing. Please try again.');
            this.resetProcessing();
        }
    }
    
    async pollJobStatus() {
        if (!this.processingJob) return;
        
        try {
            const response = await fetch(`/api/web/jobs/${this.processingJob}/status`);
            const status = await response.json();
            
            this.updateProcessingStatus(status);
            
            if (status.status === 'completed') {
                this.handleProcessingComplete(status.result);
            } else if (status.status === 'failed') {
                this.showError(status.error || 'Processing failed');
                this.resetProcessing();
            } else {
                // Continue polling
                setTimeout(() => this.pollJobStatus(), 1000);
            }
            
        } catch (error) {
            console.error('Status polling error:', error);
            this.showError('Lost connection to processing job');
            this.resetProcessing();
        }
    }
    
    updateProcessingStatus(status) {
        const progress = status.progress || 0;
        const currentStep = status.current_step || 'upload';
        const stepMessage = status.step_message || 'Processing...';
        
        // Update progress bar
        this.progressFill.style.width = `${progress}%`;
        this.progressPercent.textContent = `${Math.round(progress)}%`;
        this.progressStatus.textContent = stepMessage;
        
        // Update step indicators
        const steps = ['upload', 'analyze', 'detect', 'redact', 'complete'];
        const currentStepIndex = steps.indexOf(currentStep);
        
        steps.forEach((step, index) => {
            const stepElement = document.getElementById(`step-${step}`);
            if (!stepElement) return;
            
            stepElement.classList.remove('active', 'completed');
            
            if (index < currentStepIndex) {
                stepElement.classList.add('completed');
            } else if (index === currentStepIndex) {
                stepElement.classList.add('active');
            }
        });
    }
    
    handleProcessingComplete(result) {
        // Hide processing status
        this.processingStatus.style.display = 'none';
        
        // Show results
        this.resultsSection.style.display = 'block';
        
        // Update summary
        this.piiCount.textContent = result.pii_detected || 0;
        this.redactionCount.textContent = result.redactions_applied || 0;
        this.confidenceScore.textContent = `${Math.round((result.average_confidence || 0) * 100)}%`;
        
        // Store result for download
        this.processingResult = result;
        
        // Re-enable process button for new files
        this.processBtn.disabled = false;
    }
    
    resetProcessing() {
        this.processingStatus.style.display = 'none';
        this.resultsSection.style.display = 'none';
        this.processBtn.disabled = false;
        this.processingJob = null;
    }
    
    async downloadResult() {
        if (!this.processingResult || !this.processingResult.download_url) {
            this.showError('No processed document available for download');
            return;
        }
        
        try {
            const downloadUrl = `/api/web/jobs/${this.processingJob}/download`;
            const response = await fetch(downloadUrl);
            const blob = await response.blob();
            
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = this.processingResult.filename || 'redacted_document.pdf';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
        } catch (error) {
            console.error('Download error:', error);
            this.showError('Failed to download the processed document');
        }
    }
    
    showPreview() {
        if (!this.processingResult) return;
        
        // Open preview in new window/modal
        // This would typically show a side-by-side comparison
        alert('Preview functionality would show before/after comparison');
    }
    
    showAuditTrail() {
        if (!this.processingResult) return;
        
        // Show audit trail information
        alert('Audit trail functionality would show processing details and cryptographic verification');
    }
    
    showError(message) {
        // Create error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.innerHTML = `
            <div class="error-content">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
                <button class="error-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add error styles if not already present
        if (!document.querySelector('.error-notification-styles')) {
            const style = document.createElement('style');
            style.className = 'error-notification-styles';
            style.textContent = `
                .error-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #fef2f2;
                    border: 1px solid #fecaca;
                    border-radius: 0.5rem;
                    padding: 1rem;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    z-index: 1000;
                    max-width: 400px;
                }
                .error-content {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    color: #dc2626;
                }
                .error-close {
                    background: none;
                    border: none;
                    color: #dc2626;
                    cursor: pointer;
                    margin-left: auto;
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }
}

// Global function for remove file button
function removeFile() {
    if (window.gopnikDemo) {
        window.gopnikDemo.removeFile();
    }
}

// Initialize demo when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.gopnikDemo = new GopnikDemo();
});