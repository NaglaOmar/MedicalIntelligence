/**
 * Medical Image Upload Handler
 * Handles file upload, validation, and progress tracking for medical images
 */

window.UploadHandler = {
    selectedFiles: [],
    uploadQueue: [],
    isUploading: false,
    maxFileSize: 500 * 1024 * 1024, // 500MB
    allowedExtensions: ['.dcm', '.nii', '.nii.gz'],
    
    // Initialize upload functionality
    init: function() {
        this.setupDragAndDrop();
        this.setupFileInput();
        this.setupFormValidation();
        console.log('Upload handler initialized');
    },
    
    // Set up drag and drop functionality
    setupDragAndDrop: function() {
        const uploadZone = document.getElementById('uploadZone');
        if (!uploadZone) return;
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });
        
        // Highlight drop zone when item is dragged over
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.remove('dragover');
            }, false);
        });
        
        // Handle dropped files
        uploadZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            this.handleFiles(files);
        }, false);
        
        // Handle click to browse
        uploadZone.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    },
    
    // Set up file input handler
    setupFileInput: function() {
        const fileInput = document.getElementById('fileInput');
        if (!fileInput) return;
        
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });
    },
    
    // Set up form validation
    setupFormValidation: function() {
        const patientIdInput = document.getElementById('patientId');
        if (patientIdInput) {
            patientIdInput.addEventListener('input', () => {
                this.validatePatientId(patientIdInput.value);
            });
        }
    },
    
    // Prevent default drag behaviors
    preventDefaults: function(e) {
        e.preventDefault();
        e.stopPropagation();
    },
    
    // Handle selected files
    handleFiles: function(files) {
        const fileArray = Array.from(files);
        
        // Validate each file
        const validFiles = [];
        const errors = [];
        
        fileArray.forEach(file => {
            const validation = this.validateFile(file);
            if (validation.valid) {
                validFiles.push(file);
            } else {
                errors.push(`${file.name}: ${validation.error}`);
            }
        });
        
        // Show validation errors
        if (errors.length > 0) {
            errors.forEach(error => {
                MedicalApp.showToast(error, 'error');
            });
        }
        
        // Add valid files to selection
        if (validFiles.length > 0) {
            this.addFilesToSelection(validFiles);
        }
    },
    
    // Validate individual file
    validateFile: function(file) {
        // Check file size
        if (file.size > this.maxFileSize) {
            return {
                valid: false,
                error: `File too large (${this.formatFileSize(file.size)}). Maximum size is ${this.formatFileSize(this.maxFileSize)}`
            };
        }
        
        // Check file extension
        const fileName = file.name.toLowerCase();
        const isValidExtension = this.allowedExtensions.some(ext => {
            if (ext === '.nii.gz') {
                return fileName.endsWith('.nii.gz');
            }
            return fileName.endsWith(ext);
        });
        
        if (!isValidExtension) {
            return {
                valid: false,
                error: `Invalid file type. Supported formats: ${this.allowedExtensions.join(', ')}`
            };
        }
        
        // Check for empty file
        if (file.size === 0) {
            return { valid: false, error: 'File is empty' };
        }
        
        return { valid: true };
    },
    
    // Add files to selection
    addFilesToSelection: function(files) {
        files.forEach(file => {
            // Check for duplicates
            const isDuplicate = this.selectedFiles.some(f => 
                f.name === file.name && f.size === file.size
            );
            
            if (!isDuplicate) {
                this.selectedFiles.push(file);
            }
        });
        
        this.updateFilePreview();
        this.updateUI();
    },
    
    // Update file preview display
    updateFilePreview: function() {
        const previewSection = document.getElementById('filePreviewSection');
        const preview = document.getElementById('filePreview');
        const fileCount = document.getElementById('fileCount');
        
        if (!previewSection || !preview || !fileCount) return;
        
        if (this.selectedFiles.length === 0) {
            previewSection.classList.add('d-none');
            return;
        }
        
        previewSection.classList.remove('d-none');
        fileCount.textContent = this.selectedFiles.length;
        
        // Clear existing preview
        preview.innerHTML = '';
        
        // Add each file to preview
        this.selectedFiles.forEach((file, index) => {
            const fileItem = this.createFilePreviewItem(file, index);
            preview.appendChild(fileItem);
        });
    },
    
    // Create file preview item
    createFilePreviewItem: function(file, index) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item d-flex align-items-center p-3 border-bottom';
        
        const fileType = this.getFileType(file.name);
        const iconClass = fileType === 'dicom' ? 'file' : 'layers';
        const badgeClass = fileType === 'dicom' ? 'bg-primary' : 'bg-info';
        
        fileItem.innerHTML = `
            <div class="file-icon ${fileType} me-3">
                <i data-feather="${iconClass}" style="width: 20px; height: 20px;"></i>
            </div>
            <div class="file-info flex-grow-1">
                <div class="file-name fw-medium">${file.name}</div>
                <div class="file-details">
                    <span class="badge ${badgeClass} format-badge me-2">${fileType.toUpperCase()}</span>
                    <span class="text-muted">${this.formatFileSize(file.size)}</span>
                    <span class="text-muted ms-2">${new Date(file.lastModified).toLocaleDateString()}</span>
                </div>
            </div>
            <div class="file-actions">
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFile(${index})">
                    <i data-feather="x" style="width: 14px; height: 14px;"></i>
                </button>
            </div>
        `;
        
        // Initialize feather icons
        setTimeout(() => feather.replace(), 0);
        
        return fileItem;
    },
    
    // Get file type from filename
    getFileType: function(filename) {
        const lower = filename.toLowerCase();
        if (lower.endsWith('.dcm')) return 'dicom';
        if (lower.endsWith('.nii') || lower.endsWith('.nii.gz')) return 'nifti';
        return 'unknown';
    },
    
    // Format file size for display
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Remove file from selection
    removeFile: function(index) {
        this.selectedFiles.splice(index, 1);
        this.updateFilePreview();
        this.updateUI();
    },
    
    // Clear all files
    clearFiles: function() {
        this.selectedFiles = [];
        this.updateFilePreview();
        this.updateUI();
        
        // Reset file input
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.value = '';
        }
        
        MedicalApp.showToast('All files cleared', 'info');
    },
    
    // Update UI visibility
    updateUI: function() {
        const patientInfoSection = document.getElementById('patientInfoSection');
        const uploadActionsSection = document.getElementById('uploadActionsSection');
        
        const hasFiles = this.selectedFiles.length > 0;
        
        if (patientInfoSection) {
            patientInfoSection.classList.toggle('d-none', !hasFiles);
        }
        
        if (uploadActionsSection) {
            uploadActionsSection.classList.toggle('d-none', !hasFiles);
        }
    },
    
    // Validate patient ID
    validatePatientId: function(patientId) {
        const input = document.getElementById('patientId');
        if (!input) return false;
        
        const trimmed = patientId.trim();
        
        if (trimmed.length === 0) {
            input.classList.add('is-invalid');
            return false;
        }
        
        if (trimmed.length > 64) {
            input.classList.add('is-invalid');
            return false;
        }
        
        // Check for invalid characters
        const invalidChars = /[<>"'&\n\r\t]/;
        if (invalidChars.test(trimmed)) {
            input.classList.add('is-invalid');
            return false;
        }
        
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
        return true;
    },
    
    // Start upload process
    startUpload: function() {
        if (this.selectedFiles.length === 0) {
            MedicalApp.showToast('No files selected', 'warning');
            return;
        }
        
        // Validate form
        const patientId = document.getElementById('patientId').value.trim();
        if (!this.validatePatientId(patientId)) {
            MedicalApp.showToast('Please enter a valid Patient ID', 'error');
            return;
        }
        
        if (this.isUploading) {
            MedicalApp.showToast('Upload already in progress', 'warning');
            return;
        }
        
        this.isUploading = true;
        this.showUploadProgress();
        
        // Process each file
        this.uploadQueue = [...this.selectedFiles];
        this.processUploadQueue();
    },
    
    // Show upload progress section
    showUploadProgress: function() {
        const progressSection = document.getElementById('uploadProgressSection');
        const actionsSection = document.getElementById('uploadActionsSection');
        
        if (progressSection) {
            progressSection.classList.remove('d-none');
        }
        
        if (actionsSection) {
            actionsSection.classList.add('d-none');
        }
    },
    
    // Process upload queue
    processUploadQueue: function() {
        const uploadProgress = document.getElementById('uploadProgress');
        if (!uploadProgress) return;
        
        uploadProgress.innerHTML = '';
        
        const promises = this.uploadQueue.map((file, index) => {
            return this.uploadSingleFile(file, index);
        });
        
        Promise.allSettled(promises)
            .then(results => {
                this.handleUploadComplete(results);
            });
    },
    
    // Upload single file
    uploadSingleFile: function(file, index) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('patient_id', document.getElementById('patientId').value.trim());
            formData.append('study_id', document.getElementById('studyId').value.trim());
            formData.append('description', document.getElementById('description').value.trim());
            
            // Create progress item
            const progressItem = this.createProgressItem(file, index);
            document.getElementById('uploadProgress').appendChild(progressItem);
            
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    this.updateProgressItem(index, percent, 'uploading');
                }
            });
            
            // Handle completion
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (response.success) {
                            this.updateProgressItem(index, 100, 'completed', response);
                            resolve(response);
                        } else {
                            this.updateProgressItem(index, 0, 'failed', null, response.error);
                            reject(new Error(response.error));
                        }
                    } catch (e) {
                        this.updateProgressItem(index, 0, 'failed', null, 'Invalid response');
                        reject(new Error('Invalid response'));
                    }
                } else {
                    this.updateProgressItem(index, 0, 'failed', null, `HTTP ${xhr.status}`);
                    reject(new Error(`HTTP ${xhr.status}`));
                }
            });
            
            // Handle errors
            xhr.addEventListener('error', () => {
                this.updateProgressItem(index, 0, 'failed', null, 'Network error');
                reject(new Error('Network error'));
            });
            
            // Start upload
            xhr.open('POST', '/api/upload');
            xhr.send(formData);
        });
    },
    
    // Create progress item
    createProgressItem: function(file, index) {
        const item = document.createElement('div');
        item.className = 'upload-item mb-3 p-3 border rounded';
        item.id = `upload-item-${index}`;
        
        item.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i data-feather="file" class="me-2"></i>
                <span class="fw-medium flex-grow-1">${file.name}</span>
                <span class="badge bg-secondary" id="status-${index}">Preparing...</span>
            </div>
            <div class="progress mb-2">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     id="progress-${index}" style="width: 0%"></div>
            </div>
            <div class="small text-muted" id="details-${index}">
                ${this.formatFileSize(file.size)} • Waiting to upload
            </div>
        `;
        
        setTimeout(() => feather.replace(), 0);
        return item;
    },
    
    // Update progress item
    updateProgressItem: function(index, percent, status, response = null, error = null) {
        const statusElement = document.getElementById(`status-${index}`);
        const progressElement = document.getElementById(`progress-${index}`);
        const detailsElement = document.getElementById(`details-${index}`);
        
        if (!statusElement || !progressElement || !detailsElement) return;
        
        // Update progress bar
        progressElement.style.width = `${percent}%`;
        
        // Update status and styling based on state
        switch (status) {
            case 'uploading':
                statusElement.textContent = 'Uploading...';
                statusElement.className = 'badge bg-primary';
                progressElement.className = 'progress-bar progress-bar-striped progress-bar-animated bg-primary';
                detailsElement.textContent = `${percent}% uploaded`;
                break;
                
            case 'completed':
                statusElement.textContent = 'Completed';
                statusElement.className = 'badge bg-success';
                progressElement.className = 'progress-bar bg-success';
                if (response && response.study_id) {
                    detailsElement.innerHTML = `
                        <i data-feather="check-circle" class="me-1" style="width: 14px; height: 14px;"></i>
                        Upload successful • Study ID: ${response.study_id}
                    `;
                    setTimeout(() => feather.replace(), 0);
                }
                break;
                
            case 'failed':
                statusElement.textContent = 'Failed';
                statusElement.className = 'badge bg-danger';
                progressElement.className = 'progress-bar bg-danger';
                detailsElement.innerHTML = `
                    <i data-feather="alert-circle" class="me-1" style="width: 14px; height: 14px;"></i>
                    Upload failed: ${error || 'Unknown error'}
                `;
                setTimeout(() => feather.replace(), 0);
                break;
        }
    },
    
    // Handle upload completion
    handleUploadComplete: function(results) {
        this.isUploading = false;
        
        const successful = results.filter(r => r.status === 'fulfilled');
        const failed = results.filter(r => r.status === 'rejected');
        
        if (successful.length > 0) {
            const studies = successful.map(r => r.value);
            this.showUploadSuccess(studies);
        }
        
        if (failed.length > 0) {
            MedicalApp.showToast(`${failed.length} files failed to upload`, 'error');
        }
        
        // Update UI
        if (successful.length === this.selectedFiles.length) {
            // All files uploaded successfully
            setTimeout(() => {
                this.resetUploadForm();
            }, 3000);
        }
    },
    
    // Show upload success modal
    showUploadSuccess: function(studies) {
        const modal = document.getElementById('uploadSuccessModal');
        const studiesContainer = document.getElementById('uploadedStudies');
        
        if (!modal || !studiesContainer) return;
        
        // Populate studies list
        studiesContainer.innerHTML = studies.map(study => `
            <div class="border rounded p-2 mb-2">
                <div class="fw-medium">${study.file_info.filename}</div>
                <small class="text-muted">Study ID: ${study.study_id}</small>
            </div>
        `).join('');
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        MedicalApp.showToast(`${studies.length} files uploaded successfully`, 'success');
    },
    
    // Reset upload form
    resetUploadForm: function() {
        this.selectedFiles = [];
        this.uploadQueue = [];
        
        // Reset form fields
        document.getElementById('patientId').value = '';
        document.getElementById('studyId').value = '';
        document.getElementById('description').value = '';
        document.getElementById('fileInput').value = '';
        
        // Hide sections
        document.getElementById('filePreviewSection').classList.add('d-none');
        document.getElementById('patientInfoSection').classList.add('d-none');
        document.getElementById('uploadActionsSection').classList.add('d-none');
        document.getElementById('uploadProgressSection').classList.add('d-none');
        
        // Remove validation classes
        document.querySelectorAll('.is-valid, .is-invalid').forEach(el => {
            el.classList.remove('is-valid', 'is-invalid');
        });
    }
};

// Global functions for template usage
function initializeUploadZone() {
    window.UploadHandler.init();
}

function setupFileHandlers() {
    // Already handled in init
}

function removeFile(index) {
    window.UploadHandler.removeFile(index);
}

function clearFiles() {
    window.UploadHandler.clearFiles();
}

function startUpload() {
    window.UploadHandler.startUpload();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('uploadZone')) {
        window.UploadHandler.init();
    }
});
