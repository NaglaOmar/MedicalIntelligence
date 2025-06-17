/**
 * Simple Medical Image Viewer
 * A lightweight viewer for medical images that works without complex dependencies
 */

window.SimpleMedicalViewer = {
    currentStudyId: null,
    currentImageUrl: null,
    currentSlice: 0,
    totalSlices: 1,
    isNifti: false,
    sliceImages: [],
    
    // Initialize the simple viewer
    init: function(studyId) {
        this.currentStudyId = studyId;
        this.currentSlice = 0;
        this.showLoadingState(true);
        
        // Check if this is a multi-frame NIFTI study
        this.checkStudyType(studyId);
        
        // Load the study image directly
        this.loadStudyImage(studyId);
    },
    
    // Check study type and setup slice navigation if needed
    checkStudyType: function(studyId) {
        fetch(`/api/studies/${studyId}/info`)
            .then(response => response.json())
            .then(data => {
                if (data.format === 'nifti' && data.slices > 1) {
                    this.isNifti = true;
                    this.totalSlices = data.slices;
                    this.setupSliceNavigation();
                }
            })
            .catch(error => {
                console.log('Could not get study info, assuming single slice');
            });
    },
    
    // Setup slice navigation controls for multi-frame images
    setupSliceNavigation: function() {
        const overlay = document.getElementById('viewerOverlay');
        if (overlay) {
            // Add slice navigation controls
            const sliceControls = document.createElement('div');
            sliceControls.innerHTML = `
                <div style="margin-top: 10px; padding: 5px; background: rgba(0,0,0,0.8); border-radius: 4px;">
                    <div style="margin-bottom: 5px;">
                        <button id="prevSlice" style="background: #333; color: white; border: 1px solid #555; padding: 2px 8px; margin-right: 5px;">◀</button>
                        <span id="sliceInfo" style="color: #00ff00;">Slice: 1/${this.totalSlices}</span>
                        <button id="nextSlice" style="background: #333; color: white; border: 1px solid #555; padding: 2px 8px; margin-left: 5px;">▶</button>
                    </div>
                    <div style="font-size: 10px; color: #aaa;">Use ↑↓ keys</div>
                </div>
            `;
            overlay.appendChild(sliceControls);
            
            // Add event listeners
            document.getElementById('prevSlice').addEventListener('click', () => this.previousSlice());
            document.getElementById('nextSlice').addEventListener('click', () => this.nextSlice());
            
            // Add keyboard navigation
            document.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
                    e.preventDefault();
                    this.previousSlice();
                } else if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
                    e.preventDefault();
                    this.nextSlice();
                }
            });
        }
    },
    
    // Load study image using direct image URL
    loadStudyImage: function(studyId) {
        const imageUrl = `/api/studies/${studyId}/image`;
        this.currentImageUrl = imageUrl;
        
        // Create image element
        const img = new Image();
        img.onload = () => {
            this.displayImage(img);
            this.showLoadingState(false);
        };
        
        img.onerror = () => {
            console.error('Failed to load medical image');
            this.showError('Failed to load medical image. The file may not be compatible or may be corrupted.');
        };
        
        img.src = imageUrl;
    },
    
    // Display the loaded image
    displayImage: function(img) {
        const viewerElement = document.getElementById('viewerElement');
        if (!viewerElement) return;
        
        // Clear previous content
        viewerElement.innerHTML = '';
        
        // Create container for the image
        const imageContainer = document.createElement('div');
        imageContainer.style.cssText = `
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #000;
            overflow: hidden;
            position: relative;
        `;
        
        // Style the image with NIFTI rotation correction
        let rotation = '';
        if (this.isNifti) {
            // NIFTI images often need rotation correction
            rotation = 'rotate(90deg) scaleX(-1)'; // Common NIFTI orientation fix
        }
        
        img.style.cssText = `
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            cursor: grab;
            transition: transform 0.1s ease;
            transform: ${rotation};
        `;
        
        img.draggable = false;
        
        // Add image to container
        imageContainer.appendChild(img);
        viewerElement.appendChild(imageContainer);
        
        // Add interaction handlers
        this.addImageInteractions(img, imageContainer);
        
        // Update image info
        this.updateImageInfo(img);
        
        console.log('Medical image displayed successfully');
    },
    
    // Add enhanced image interactions (zoom, pan, windowing)
    addImageInteractions: function(img, container) {
        let scale = 1;
        let translateX = 0;
        let translateY = 0;
        let isDragging = false;
        let isWindowing = false;
        let lastX = 0;
        let lastY = 0;
        let windowLevel = 128;
        let windowWidth = 256;
        let brightness = 0;
        let contrast = 1;
        
        // Get current active tool
        const getCurrentTool = () => {
            const activeButton = document.querySelector('.tool-button.active');
            return activeButton ? activeButton.id.replace('-tool', '') : 'zoom';
        };
        
        // Zoom with mouse wheel
        container.addEventListener('wheel', (e) => {
            e.preventDefault();
            
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            scale *= delta;
            scale = Math.max(0.1, Math.min(10, scale)); // Extended zoom range
            
            this.updateImageTransform(img, scale, translateX, translateY);
        });
        
        // Mouse interactions based on active tool
        container.addEventListener('mousedown', (e) => {
            if (e.button === 0) { // Left mouse button
                const tool = getCurrentTool();
                
                if (tool === 'pan') {
                    isDragging = true;
                    img.style.cursor = 'grabbing';
                } else if (tool === 'windowing') {
                    isWindowing = true;
                    img.style.cursor = 'col-resize';
                } else if (tool === 'zoom') {
                    // Click to zoom in, Shift+click to zoom out
                    const zoomFactor = e.shiftKey ? 0.8 : 1.25;
                    scale *= zoomFactor;
                    scale = Math.max(0.1, Math.min(10, scale));
                    this.updateImageTransform(img, scale, translateX, translateY);
                }
                
                lastX = e.clientX;
                lastY = e.clientY;
                e.preventDefault();
            }
        });
        
        container.addEventListener('mousemove', (e) => {
            const deltaX = e.clientX - lastX;
            const deltaY = e.clientY - lastY;
            
            if (isDragging) {
                // Pan the image
                translateX += deltaX;
                translateY += deltaY;
                this.updateImageTransform(img, scale, translateX, translateY);
            } else if (isWindowing) {
                // Window/Level adjustment
                windowLevel += deltaX * 2;
                windowWidth += deltaY * 2;
                windowWidth = Math.max(1, windowWidth);
                
                // Apply windowing effect through CSS filters
                brightness = (windowLevel - 128) / 255;
                contrast = windowWidth / 256;
                
                img.style.filter = `brightness(${1 + brightness}) contrast(${contrast})`;
                
                // Update info display
                this.updateWindowingInfo(windowLevel, windowWidth);
            }
            
            lastX = e.clientX;
            lastY = e.clientY;
        });
        
        container.addEventListener('mouseup', () => {
            isDragging = false;
            isWindowing = false;
            img.style.cursor = 'grab';
        });
        
        container.addEventListener('mouseleave', () => {
            isDragging = false;
            isWindowing = false;
            img.style.cursor = 'grab';
        });
        
        // Store transform state
        img._viewerState = { scale, translateX, translateY, windowLevel, windowWidth };
    },
    
    // Update image transform
    updateImageTransform: function(img, scale, translateX, translateY) {
        let baseTransform = '';
        if (this.isNifti) {
            baseTransform = 'rotate(90deg) scaleX(-1) '; // NIFTI orientation correction
        }
        
        img.style.transform = `${baseTransform}scale(${scale}) translate(${translateX/scale}px, ${translateY/scale}px)`;
        img._viewerState = { scale, translateX, translateY };
        
        // Update zoom info
        const zoomPercent = Math.round(scale * 100);
        this.updateImageInfo(img, { zoom: zoomPercent });
    },
    
    // Update windowing information
    updateWindowingInfo: function(windowLevel, windowWidth) {
        const infoElement = document.getElementById('imageInfo');
        if (infoElement) {
            const existingInfo = infoElement.innerHTML;
            const lines = existingInfo.split('<br>');
            
            // Update or add windowing info
            let updated = false;
            for (let i = 0; i < lines.length; i++) {
                if (lines[i].includes('WL:') || lines[i].includes('WW:')) {
                    lines[i] = `WL: ${Math.round(windowLevel)} | WW: ${Math.round(windowWidth)}`;
                    updated = true;
                    break;
                }
            }
            
            if (!updated) {
                lines.splice(1, 0, `WL: ${Math.round(windowLevel)} | WW: ${Math.round(windowWidth)}`);
            }
            
            infoElement.innerHTML = lines.join('<br>');
        }
    },
    
    // Reset view
    resetView: function() {
        const img = document.querySelector('#viewerElement img');
        if (img) {
            this.updateImageTransform(img, 1, 0, 0);
        }
    },
    
    // Toggle image inversion
    toggleInvert: function() {
        const img = document.querySelector('#viewerElement img');
        if (img) {
            const currentFilter = img.style.filter || '';
            if (currentFilter.includes('invert')) {
                img.style.filter = currentFilter.replace(/invert\([^)]*\)/g, '').trim();
            } else {
                img.style.filter = (currentFilter + ' invert(1)').trim();
            }
        }
    },
    
    // Slice navigation functions
    nextSlice: function() {
        if (this.currentSlice < this.totalSlices - 1) {
            this.currentSlice++;
            this.loadSlice(this.currentSlice);
            this.updateSliceInfo();
        }
    },
    
    previousSlice: function() {
        if (this.currentSlice > 0) {
            this.currentSlice--;
            this.loadSlice(this.currentSlice);
            this.updateSliceInfo();
        }
    },
    
    loadSlice: function(sliceIndex) {
        const imageUrl = `/api/studies/${this.currentStudyId}/image?slice=${sliceIndex}`;
        this.currentImageUrl = imageUrl;
        
        const img = document.querySelector('#viewerElement img');
        if (img) {
            img.src = imageUrl;
        }
    },
    
    updateSliceInfo: function() {
        const sliceInfoElement = document.getElementById('sliceInfo');
        if (sliceInfoElement) {
            sliceInfoElement.textContent = `Slice: ${this.currentSlice + 1}/${this.totalSlices}`;
        }
    },

    // Update image information display
    updateImageInfo: function(img, extraInfo = {}) {
        const infoElement = document.getElementById('imageInfo');
        if (infoElement) {
            const zoom = extraInfo.zoom || 100;
            let info = `
                Size: ${img.naturalWidth} × ${img.naturalHeight}<br>
                Zoom: ${zoom}%<br>
            `;
            
            if (this.isNifti && this.totalSlices > 1) {
                info += `Slices: ${this.totalSlices}<br>`;
            }
            
            info += `
                Pan: Drag with mouse<br>
                Zoom: Mouse wheel<br>
                Window: Select tool & drag
            `;
            
            infoElement.innerHTML = info;
        }
    },
    
    // Show loading state
    showLoadingState: function(show) {
        const loadingElement = document.getElementById('loadingState');
        const viewerContainer = document.getElementById('viewerContainer');
        const errorElement = document.getElementById('errorState');
        
        if (show) {
            if (loadingElement) loadingElement.classList.remove('d-none');
            if (viewerContainer) viewerContainer.classList.add('d-none');
            if (errorElement) errorElement.classList.add('d-none');
        } else {
            if (loadingElement) loadingElement.classList.add('d-none');
            if (viewerContainer) viewerContainer.classList.remove('d-none');
        }
    },
    
    // Show error state
    showError: function(message) {
        const errorElement = document.getElementById('errorState');
        const loadingElement = document.getElementById('loadingState');
        const viewerContainer = document.getElementById('viewerContainer');
        
        if (errorElement && loadingElement && viewerContainer) {
            loadingElement.classList.add('d-none');
            viewerContainer.classList.add('d-none');
            errorElement.classList.remove('d-none');
            
            const errorMessage = document.getElementById('errorMessage');
            if (errorMessage) {
                errorMessage.textContent = message;
            }
        }
    },
    
    // Retry loading the image
    retryLoad: function() {
        if (this.currentStudyId) {
            this.init(this.currentStudyId);
        }
    }
};

// Simple tool functions for the UI
function setTool(toolName) {
    // Remove active class from all tool buttons
    document.querySelectorAll('.tool-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active class to selected tool
    const toolButton = document.getElementById(toolName + '-tool');
    if (toolButton) {
        toolButton.classList.add('active');
    }
    
    console.log(`Tool set to: ${toolName}`);
}

function resetView() {
    window.SimpleMedicalViewer.resetView();
}

function toggleInvert() {
    window.SimpleMedicalViewer.toggleInvert();
}

function toggleSegmentation() {
    const toggle = document.getElementById('segmentationToggle');
    if (toggle && toggle.checked) {
        // Load segmentation overlay (placeholder for now)
        console.log('Segmentation overlay would be loaded here');
    } else {
        // Hide segmentation overlay
        console.log('Segmentation overlay hidden');
    }
}

function loadSegmentation(analysisId) {
    // Load segmentation overlay for the given analysis
    console.log('Loading segmentation for analysis:', analysisId);
    // This would load and display segmentation overlay data
}

function retryImageLoad() {
    window.SimpleMedicalViewer.retryLoad();
}

// Initialize viewer when page loads
function initializeViewer(studyId) {
    console.log('Initializing Simple Medical Viewer for study:', studyId);
    window.SimpleMedicalViewer.init(studyId);
}