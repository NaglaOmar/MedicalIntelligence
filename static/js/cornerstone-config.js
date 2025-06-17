/**
 * Cornerstone.js Configuration for Medical Image Viewer
 * Configures Cornerstone.js for DICOM and medical image display
 */

// Global configuration object
window.CornerstoneConfig = {
    initialized: false,
    tools: {},
    viewports: new Map(),
    
    // Initialize Cornerstone with required settings
    init: function() {
        if (this.initialized) {
            console.log('Cornerstone already initialized');
            return Promise.resolve();
        }
        
        try {
            // Cornerstone v2 doesn't have a configure method
            // Configuration is handled through individual settings
            
            // Configure web image loader for various formats
            if (typeof cornerstoneWebImageLoader !== 'undefined') {
                // Configure DICOM parser if available
                if (typeof dicomParser !== 'undefined') {
                    cornerstoneWebImageLoader.external.dicomParser = dicomParser;
                }
                
                cornerstoneWebImageLoader.configure({
                    beforeSend: function(xhr) {
                        // Add authentication headers if needed
                        // xhr.setRequestHeader('Authorization', 'Bearer ' + token);
                    }
                });
                
                // Register web image loader
                cornerstone.registerImageLoader('http', cornerstoneWebImageLoader.loadImage);
                cornerstone.registerImageLoader('https', cornerstoneWebImageLoader.loadImage);
                
                console.log('Cornerstone Web Image Loader configured');
            } else {
                console.warn('cornerstoneWebImageLoader not available - only basic image loading will work');
            }
            
            // Initialize tools if available
            if (typeof cornerstoneTools !== 'undefined') {
                this.initializeTools();
            }
            
            // Cornerstone v2 doesn't have configure method
            // Configuration is done through individual settings
            
            this.initialized = true;
            console.log('Cornerstone initialized successfully');
            return Promise.resolve();
            
        } catch (error) {
            console.error('Failed to initialize Cornerstone:', error);
            return Promise.reject(error);
        }
    },
    
    // Initialize Cornerstone Tools
    initializeTools: function() {
        try {
            // Initialize tools with basic configuration
            cornerstoneTools.init();
            
            // Add basic tools
            const PanTool = cornerstoneTools.PanTool;
            const ZoomTool = cornerstoneTools.ZoomTool;
            const WwwcTool = cornerstoneTools.WwwcTool;
            const ZoomMouseWheelTool = cornerstoneTools.ZoomMouseWheelTool;
            const PanMultiTouchTool = cornerstoneTools.PanMultiTouchTool;
            const ZoomTouchPinchTool = cornerstoneTools.ZoomTouchPinchTool;
            
            // Add tools if they exist
            if (PanTool) cornerstoneTools.addTool(PanTool);
            if (ZoomTool) cornerstoneTools.addTool(ZoomTool);
            if (WwwcTool) cornerstoneTools.addTool(WwwcTool);
            if (ZoomMouseWheelTool) cornerstoneTools.addTool(ZoomMouseWheelTool);
            if (PanMultiTouchTool) cornerstoneTools.addTool(PanMultiTouchTool);
            if (ZoomTouchPinchTool) cornerstoneTools.addTool(ZoomTouchPinchTool);
            
            // Set default tool states
            if (PanTool) cornerstoneTools.setToolActive('Pan', { mouseButtonMask: 4 });
            if (ZoomTool) cornerstoneTools.setToolActive('Zoom', { mouseButtonMask: 2 });
            if (WwwcTool) cornerstoneTools.setToolActive('Wwwc', { mouseButtonMask: 1 });
            if (ZoomMouseWheelTool) cornerstoneTools.setToolActive('ZoomMouseWheel', {});
            if (PanMultiTouchTool) cornerstoneTools.setToolActive('PanMultiTouch', {});
            if (ZoomTouchPinchTool) cornerstoneTools.setToolActive('ZoomTouchPinch', {});
            
            console.log('Cornerstone Tools initialized successfully');
            
        } catch (error) {
            console.warn('Some Cornerstone Tools features may not be available:', error.message);
        }
    },
    
    // Enable element for Cornerstone rendering
    enableElement: function(elementId, options = {}) {
        const element = document.getElementById(elementId);
        if (!element) {
            throw new Error(`Element with id '${elementId}' not found`);
        }
        
        try {
            // Default viewport settings for medical images
            const defaultViewport = {
                scale: 1.0,
                translation: { x: 0, y: 0 },
                voi: {
                    windowWidth: 400,
                    windowCenter: 40
                },
                invert: false,
                pixelReplication: false,
                rotation: 0,
                hflip: false,
                vflip: false,
                ...options.viewport
            };
            
            // Enable the element
            cornerstone.enable(element, {
                renderer: 'webgl', // Use WebGL for better performance
                ...options.cornerstone
            });
            
            // Store viewport reference
            this.viewports.set(elementId, {
                element: element,
                viewport: defaultViewport,
                imageId: null,
                enabled: true
            });
            
            // Set up event listeners
            this.setupEventListeners(element, elementId);
            
            console.log(`Cornerstone enabled for element: ${elementId}`);
            return element;
            
        } catch (error) {
            console.error(`Failed to enable Cornerstone for element ${elementId}:`, error);
            throw error;
        }
    },
    
    // Set up event listeners for the viewport
    setupEventListeners: function(element, elementId) {
        // Image rendered event
        element.addEventListener('cornerstoneimagerendered', (event) => {
            this.updateImageInfo(elementId, event.detail);
        });
        
        // Viewport changed event
        element.addEventListener('cornerstoneviewportchanged', (event) => {
            const viewport = this.viewports.get(elementId);
            if (viewport) {
                viewport.viewport = event.detail;
            }
        });
        
        // Image loaded event
        element.addEventListener('cornerstoneimageloaded', (event) => {
            console.log('Image loaded:', event.detail);
        });
        
        // Error handling
        element.addEventListener('cornerstoneimageerror', (event) => {
            console.error('Image loading error:', event.detail);
            this.handleImageError(elementId, event.detail);
        });
        
        // Touch/mouse interaction events
        if (typeof cornerstoneTools !== 'undefined') {
            cornerstoneTools.addStackStateManager(element, ['stack']);
            cornerstoneTools.addToolState(element, 'stack', {
                imageIds: [],
                currentImageIdIndex: 0
            });
        }
    },
    
    // Load and display image
    loadImage: function(elementId, imageId, options = {}) {
        const viewport = this.viewports.get(elementId);
        if (!viewport) {
            throw new Error(`Viewport not found for element: ${elementId}`);
        }
        
        // Show loading state
        this.showLoadingState(elementId, true);
        
        return cornerstone.loadImage(imageId)
            .then(image => {
                // Display the image
                cornerstone.displayImage(viewport.element, image, viewport.viewport);
                
                // Update viewport reference
                viewport.imageId = imageId;
                
                // Auto-fit image to viewport if requested
                if (options.autoFit !== false) {
                    cornerstone.fitToWindow(viewport.element);
                }
                
                // Hide loading state
                this.showLoadingState(elementId, false);
                
                console.log(`Image loaded successfully: ${imageId}`);
                return image;
            })
            .catch(error => {
                console.error(`Failed to load image ${imageId}:`, error);
                this.showLoadingState(elementId, false);
                this.handleImageError(elementId, error);
                throw error;
            });
    },
    
    // Update image information display
    updateImageInfo: function(elementId, renderData) {
        const infoElement = document.getElementById('imageInfo');
        if (!infoElement || !renderData) return;
        
        const { image, viewport } = renderData;
        
        const info = [
            `WW: ${Math.round(viewport.voi.windowWidth)}`,
            `WC: ${Math.round(viewport.voi.windowCenter)}`,
            `Zoom: ${(viewport.scale * 100).toFixed(0)}%`,
            `${image.width} × ${image.height}`
        ];
        
        infoElement.innerHTML = info.join('<br>');
    },
    
    // Handle image loading errors
    handleImageError: function(elementId, error) {
        const errorElement = document.getElementById('errorState');
        const loadingElement = document.getElementById('loadingState');
        const viewerContainer = document.getElementById('viewerContainer');
        
        if (errorElement && loadingElement && viewerContainer) {
            loadingElement.classList.add('d-none');
            viewerContainer.classList.add('d-none');
            errorElement.classList.remove('d-none');
            
            const errorMessage = document.getElementById('errorMessage');
            if (errorMessage) {
                errorMessage.textContent = error.message || 'Failed to load medical image';
            }
        }
    },
    
    // Show/hide loading state
    showLoadingState: function(elementId, show) {
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
    
    // Set active tool
    setActiveTool: function(toolName, options = {}) {
        if (!this.initialized || typeof cornerstoneTools === 'undefined') {
            console.warn('Cornerstone Tools not initialized');
            return;
        }
        
        try {
            // Deactivate all mouse tools first
            cornerstoneTools.setToolPassive('Pan');
            cornerstoneTools.setToolPassive('Zoom');
            cornerstoneTools.setToolPassive('Wwwc');
            
            // Activate the selected tool
            switch (toolName.toLowerCase()) {
                case 'pan':
                    cornerstoneTools.setToolActive('Pan', { mouseButtonMask: 1 });
                    break;
                case 'zoom':
                    cornerstoneTools.setToolActive('Zoom', { mouseButtonMask: 1 });
                    break;
                case 'windowing':
                    cornerstoneTools.setToolActive('Wwwc', { mouseButtonMask: 1 });
                    break;
                default:
                    console.warn(`Unknown tool: ${toolName}`);
                    return;
            }
            
            console.log(`Active tool set to: ${toolName}`);
            
        } catch (error) {
            console.error(`Failed to set active tool to ${toolName}:`, error);
        }
    },
    
    // Reset viewport to default state
    resetViewport: function(elementId) {
        const viewport = this.viewports.get(elementId);
        if (!viewport) return;
        
        try {
            cornerstone.reset(viewport.element);
            cornerstone.fitToWindow(viewport.element);
            console.log(`Viewport reset for element: ${elementId}`);
        } catch (error) {
            console.error(`Failed to reset viewport for ${elementId}:`, error);
        }
    },
    
    // Toggle image inversion
    toggleInvert: function(elementId) {
        const viewport = this.viewports.get(elementId);
        if (!viewport) return;
        
        try {
            const currentViewport = cornerstone.getViewport(viewport.element);
            currentViewport.invert = !currentViewport.invert;
            cornerstone.setViewport(viewport.element, currentViewport);
            console.log(`Image inversion toggled for element: ${elementId}`);
        } catch (error) {
            console.error(`Failed to toggle inversion for ${elementId}:`, error);
        }
    },
    
    // Cleanup and disable element
    disableElement: function(elementId) {
        const viewport = this.viewports.get(elementId);
        if (!viewport) return;
        
        try {
            cornerstone.disable(viewport.element);
            this.viewports.delete(elementId);
            console.log(`Cornerstone disabled for element: ${elementId}`);
        } catch (error) {
            console.error(`Failed to disable Cornerstone for ${elementId}:`, error);
        }
    },
    
    // Get current viewport state
    getViewportState: function(elementId) {
        const viewport = this.viewports.get(elementId);
        if (!viewport) return null;
        
        try {
            return cornerstone.getViewport(viewport.element);
        } catch (error) {
            console.error(`Failed to get viewport state for ${elementId}:`, error);
            return null;
        }
    }
};

// Auto-initialize when Cornerstone is available
document.addEventListener('DOMContentLoaded', function() {
    if (typeof cornerstone !== 'undefined') {
        window.CornerstoneConfig.init().catch(console.error);
    } else {
        console.warn('Cornerstone not loaded - viewer functionality will be limited');
    }
});
