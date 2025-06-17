/**
 * Medical Image Viewer JavaScript
 * Handles medical image display, interaction, and analysis features
 */

window.MedicalViewer = {
    currentStudyId: null,
    currentImageId: null,
    segmentationVisible: false,
    segmentationOverlay: null,
    
    // Initialize the medical viewer
    init: async function(studyId) {
        this.currentStudyId = studyId;
        
        // Wait for Cornerstone to be ready
        if (typeof cornerstone === 'undefined') {
            console.error('Cornerstone.js not loaded');
            this.showError('Medical viewer not available - Cornerstone.js not loaded');
            return;
        }
        
        // Initialize Cornerstone configuration
        try {
            if (!window.CornerstoneConfig.initialized) {
                await window.CornerstoneConfig.init();
            }
            
            this.setupViewer();
            await this.loadStudyImage(studyId);
            
        } catch (error) {
            console.error('Failed to initialize medical viewer:', error);
            this.showError('Failed to initialize medical viewer: ' + error.message);
        }
    },
    
    // Set up the viewer element
    setupViewer: function() {
        try {
            // Enable the viewer element
            const element = window.CornerstoneConfig.enableElement('viewerElement', {
                viewport: {
                    scale: 1.0,
                    translation: { x: 0, y: 0 },
                    voi: {
                        windowWidth: 400,
                        windowCenter: 40
                    },
                    invert: false
                }
            });
            
            // Set up keyboard shortcuts
            this.setupKeyboardShortcuts();
            
            // Set up mouse wheel handling
            this.setupMouseWheel(element);
            
            console.log('Medical viewer setup complete');
            return Promise.resolve();
            
        } catch (error) {
            console.error('Failed to setup viewer:', error);
            return Promise.reject(error);
        }
    },
    
    // Load study image for viewing
    loadStudyImage: function(studyId) {
        const imageUrl = `/api/image/${studyId}`;
        this.currentImageId = imageUrl;
        
        return window.CornerstoneConfig.loadImage('viewerElement', imageUrl, {
            autoFit: true
        }).catch(error => {
            console.error('Failed to load study image:', error);
            this.showError('Failed to load medical image: ' + error.message);
        });
    },
    
    // Set up keyboard shortcuts for viewer
    setupKeyboardShortcuts: function() {
        document.addEventListener('keydown', (event) => {
            // Only handle shortcuts when viewer is focused
            if (!document.getElementById('viewerElement').matches(':focus-within')) {
                return;
            }
            
            switch (event.key.toLowerCase()) {
                case 'r':
                    event.preventDefault();
                    this.resetView();
                    break;
                case 'i':
                    event.preventDefault();
                    this.toggleInvert();
                    break;
                case 's':
                    event.preventDefault();
                    this.toggleSegmentation();
                    break;
                case 'p':
                    event.preventDefault();
                    this.setTool('pan');
                    break;
                case 'z':
                    event.preventDefault();
                    this.setTool('zoom');
                    break;
                case 'w':
                    event.preventDefault();
                    this.setTool('windowing');
                    break;
            }
        });
    },
    
    // Set up mouse wheel handling
    setupMouseWheel: function(element) {
        element.addEventListener('wheel', (event) => {
            event.preventDefault();
            
            if (event.ctrlKey) {
                // Zoom with Ctrl+Wheel
                const viewport = cornerstone.getViewport(element);
                const scaleFactor = event.deltaY > 0 ? 0.9 : 1.1;
                viewport.scale *= scaleFactor;
                cornerstone.setViewport(element, viewport);
            } else {
                // Window/Level adjustment with Shift+Wheel
                if (event.shiftKey) {
                    const viewport = cornerstone.getViewport(element);
                    const delta = event.deltaY > 0 ? -10 : 10;
                    viewport.voi.windowWidth += delta;
                    cornerstone.setViewport(element, viewport);
                }
            }
        });
    },
    
    // Set active tool
    setTool: function(toolName) {
        // Update UI to show active tool
        document.querySelectorAll('.tool-button').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const toolButton = document.getElementById(`${toolName}-tool`);
        if (toolButton) {
            toolButton.classList.add('active');
        }
        
        // Set the tool in Cornerstone
        window.CornerstoneConfig.setActiveTool(toolName);
        
        // Update cursor
        const element = document.getElementById('viewerElement');
        if (element) {
            element.style.cursor = this.getCursorForTool(toolName);
        }
    },
    
    // Get cursor style for tool
    getCursorForTool: function(toolName) {
        const cursors = {
            'pan': 'move',
            'zoom': 'zoom-in',
            'windowing': 'crosshair'
        };
        return cursors[toolName] || 'default';
    },
    
    // Reset view to fit window
    resetView: function() {
        window.CornerstoneConfig.resetViewport('viewerElement');
        MedicalApp.showToast('View reset to fit window', 'info');
    },
    
    // Toggle image inversion
    toggleInvert: function() {
        window.CornerstoneConfig.toggleInvert('viewerElement');
        MedicalApp.showToast('Image inversion toggled', 'info');
    },
    
    // Toggle segmentation overlay
    toggleSegmentation: function() {
        const checkbox = document.getElementById('segmentationToggle');
        if (!checkbox) return;
        
        this.segmentationVisible = checkbox.checked;
        
        if (this.segmentationVisible) {
            this.loadSegmentationOverlay();
        } else {
            this.hideSegmentationOverlay();
        }
    },
    
    // Load segmentation overlay
    loadSegmentationOverlay: function() {
        if (!this.currentStudyId) return;
        
        // Find latest analysis with segmentation
        fetch('/api/studies')
            .then(response => response.json())
            .then(data => {
                const study = data.studies.find(s => s.id === this.currentStudyId);
                if (study && study.analysis_count > 0) {
                    // For now, show a mock overlay indication
                    this.showSegmentationOverlay();
                    MedicalApp.showToast('Segmentation overlay enabled', 'success');
                } else {
                    MedicalApp.showToast('No segmentation data available', 'warning');
                    document.getElementById('segmentationToggle').checked = false;
                    this.segmentationVisible = false;
                }
            })
            .catch(error => {
                console.error('Error loading segmentation:', error);
                MedicalApp.showToast('Failed to load segmentation overlay', 'error');
                document.getElementById('segmentationToggle').checked = false;
                this.segmentationVisible = false;
            });
    },
    
    // Show segmentation overlay (mock implementation)
    showSegmentationOverlay: function() {
        const viewerElement = document.getElementById('viewerElement');
        if (!viewerElement) return;
        
        // Remove existing overlay
        this.hideSegmentationOverlay();
        
        // Create overlay element
        const overlay = document.createElement('div');
        overlay.id = 'segmentationOverlay';
        overlay.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            opacity: 0.3;
            background: linear-gradient(45deg, 
                transparent 40%, 
                rgba(255, 0, 0, 0.2) 41%, 
                rgba(255, 0, 0, 0.2) 43%, 
                transparent 44%,
                transparent 56%,
                rgba(0, 255, 0, 0.2) 57%,
                rgba(0, 255, 0, 0.2) 59%,
                transparent 60%
            );
            background-size: 20px 20px;
            mix-blend-mode: screen;
            z-index: 5;
        `;
        
        viewerElement.appendChild(overlay);
        this.segmentationOverlay = overlay;
    },
    
    // Hide segmentation overlay
    hideSegmentationOverlay: function() {
        if (this.segmentationOverlay) {
            this.segmentationOverlay.remove();
            this.segmentationOverlay = null;
        }
    },
    
    // Load specific segmentation by analysis ID
    loadSegmentation: function(analysisId) {
        MedicalApp.showToast('Loading segmentation overlay...', 'info');
        
        fetch(`/api/segmentation/${analysisId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Segmentation not found');
                }
                return response.blob();
            })
            .then(blob => {
                // In a full implementation, this would load the actual segmentation data
                // For now, we'll enable the mock overlay
                document.getElementById('segmentationToggle').checked = true;
                this.segmentationVisible = true;
                this.showSegmentationOverlay();
                MedicalApp.showToast('Segmentation overlay loaded', 'success');
            })
            .catch(error => {
                console.error('Error loading segmentation:', error);
                MedicalApp.showToast('Failed to load segmentation: ' + error.message, 'error');
            });
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
    
    // Retry image loading
    retryImageLoad: function() {
        if (this.currentStudyId) {
            window.CornerstoneConfig.showLoadingState('viewerElement', true);
            this.loadStudyImage(this.currentStudyId);
        }
    },
    
    // Get viewer statistics
    getViewerStats: function() {
        const viewport = window.CornerstoneConfig.getViewportState('viewerElement');
        if (!viewport) return null;
        
        return {
            scale: viewport.scale,
            windowWidth: viewport.voi.windowWidth,
            windowCenter: viewport.voi.windowCenter,
            inverted: viewport.invert,
            translation: viewport.translation,
            rotation: viewport.rotation
        };
    },
    
    // Export current view as image
    exportView: function() {
        const element = document.getElementById('viewerElement');
        if (!element) return;
        
        try {
            const canvas = cornerstone.getEnabledElement(element).canvas;
            const dataURL = canvas.toDataURL('image/png');
            
            // Create download link
            const link = document.createElement('a');
            link.download = `medical-image-${this.currentStudyId || 'export'}.png`;
            link.href = dataURL;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            MedicalApp.showToast('Image exported successfully', 'success');
            
        } catch (error) {
            console.error('Export failed:', error);
            MedicalApp.showToast('Failed to export image', 'error');
        }
    }
};

// Global functions for template usage
function initializeViewer(studyId) {
    return window.MedicalViewer.init(studyId);
}

function setTool(toolName) {
    window.MedicalViewer.setTool(toolName);
}

function resetView() {
    window.MedicalViewer.resetView();
}

function toggleInvert() {
    window.MedicalViewer.toggleInvert();
}

function toggleSegmentation() {
    window.MedicalViewer.toggleSegmentation();
}

function loadSegmentation(analysisId) {
    window.MedicalViewer.loadSegmentation(analysisId);
}

function retryImageLoad() {
    window.MedicalViewer.retryImageLoad();
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.CornerstoneConfig) {
        window.CornerstoneConfig.disableElement('viewerElement');
    }
});
