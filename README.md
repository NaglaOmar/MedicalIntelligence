# Medical Imaging Analysis System

A comprehensive AI-powered medical imaging platform that processes DICOM and NIFTI files with intelligent analysis capabilities.

## Features

### Core Functionality
- **DICOM/NIFTI Upload**: Support for compressed and uncompressed medical image formats
- **Interactive Medical Viewer**: Pan, zoom, windowing tools for medical image examination
- **AI-Powered Analysis**: Google Gemini integration for intelligent medical image interpretation
- **Segmentation Ready**: Architecture prepared for TotalSegmentator integration
- **Clinical Workflow**: Patient study management and analysis tracking

### Technical Capabilities
- **Compressed DICOM Support**: Handles JPEG Lossless compression with pylibjpeg
- **Large File Handling**: Up to 1GB file uploads with optimized streaming
- **Secure Processing**: PostgreSQL database with proper medical data handling
- **RESTful API**: Complete API for integration with clinical systems
- **Responsive UI**: Bootstrap-themed interface optimized for medical workflows

## Quick Start

1. **Upload Medical Images**
   - Navigate to the upload page
   - Drag and drop DICOM (.dcm) or NIFTI (.nii, .nii.gz) files
   - System automatically processes and validates medical images

2. **View Medical Images**
   - Click "View" on any uploaded study
   - Use interactive tools: pan (drag), zoom (mouse wheel), windowing
   - Toggle image inversion for different viewing preferences

3. **AI Analysis** (requires Google API key)
   - Click "AI Analysis" in the viewer
   - Ask natural language questions about the medical image
   - Receive intelligent interpretations and clinical insights

## Architecture

### Backend Services
- **Image Processor**: Handles DICOM/NIFTI parsing and web conversion
- **LLM Service**: Google Gemini integration for medical analysis
- **Segmentation Service**: Ready for TotalSegmentator integration
- **Validation System**: Medical file format validation and error handling

### Database Schema
- **Users**: Authentication and access control
- **Medical Studies**: Patient studies with metadata
- **Analysis Results**: AI analysis results and segmentation data
- **Processing Logs**: Comprehensive audit trail

### API Endpoints
- `POST /api/upload` - Upload medical images
- `GET /api/studies/{id}/image` - Serve medical images
- `POST /api/analyze` - AI-powered analysis
- `POST /api/process/{id}` - Trigger image processing
- `GET /api/studies` - List all studies

## Configuration

### Required Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `GOOGLE_API_KEY`: Google Gemini API key for AI features
- `SESSION_SECRET`: Flask session security key

### Optional Settings
- `FLASK_ENV`: Development/production environment
- Upload limits: Currently set to 1GB maximum file size
- Processing timeout: 5 minutes for large medical files

## Medical File Support

### DICOM Files (.dcm)
- Uncompressed DICOM images
- JPEG Lossless compressed DICOM
- Various transfer syntaxes supported
- Automatic metadata extraction

### NIFTI Files (.nii, .nii.gz)
- Neuroimaging Informatics Technology Initiative format
- Compressed and uncompressed variants
- 3D medical image volumes
- Slice extraction for web viewing

## Deployment

The system is production-ready with:
- Gunicorn WSGI server with medical file optimizations
- PostgreSQL database for clinical data persistence
- Scalable architecture for healthcare environments
- Security configurations for medical data handling

## AI Features

When properly configured with a Google API key:
- **Automated Report Generation**: AI-generated medical image reports
- **Natural Language Queries**: Ask questions about medical findings
- **Clinical Decision Support**: Intelligent analysis of medical images
- **Multi-modal Understanding**: Text and image comprehension

## Future Enhancements

- **TotalSegmentator Integration**: Organ segmentation capabilities
- **PACS Integration**: Hospital information system connectivity
- **Advanced AI Models**: Specialized medical AI model integration
- **Compliance Features**: HIPAA and medical regulation compliance tools

---

This medical imaging system provides a solid foundation for clinical workflows while maintaining the flexibility to integrate with existing healthcare infrastructure.