import os
import json
import logging
from datetime import datetime
from flask import render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from app import app, db
from models import MedicalStudy, AnalysisResult, ProcessingLog
from services.image_processor import ImageProcessor
from services.segmentation_service import SegmentationService
from services.llm_service import LLMService
from utils.validators import validate_medical_file
from utils.file_utils import get_file_info, cleanup_old_files

logger = logging.getLogger(__name__)

# Initialize services
image_processor = ImageProcessor()
segmentation_service = SegmentationService()
llm_service = LLMService()

ALLOWED_EXTENSIONS = {'dcm', 'nii', 'nii.gz', 'gz'}

def allowed_file(filename):
    return '.' in filename and (
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS or
        filename.lower().endswith('.nii.gz')
    )

@app.route('/')
def index():
    """Main dashboard page"""
    recent_studies = MedicalStudy.query.order_by(MedicalStudy.created_at.desc()).limit(10).all()
    return render_template('index.html', studies=recent_studies)

@app.route('/upload')
def upload_page():
    """Upload page for medical images"""
    return render_template('upload.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and basic validation with streaming support"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '' or file.filename is None:
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload DICOM (.dcm) or NIFTI (.nii, .nii.gz) files'}), 400
        
        # Secure the filename
        filename = secure_filename(file.filename) if file.filename else None
        if not filename:
            filename = 'medical_image_' + str(int(datetime.now().timestamp()))
        
        # Save file with streaming to handle large files
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Stream save for large files
        with open(filepath, 'wb') as f:
            while True:
                chunk = file.stream.read(4096)  # 4KB chunks
                if not chunk:
                    break
                f.write(chunk)
        
        # Validate medical file format with improved error handling
        try:
            validation_result = validate_medical_file(filepath)
            if not validation_result['valid']:
                try:
                    os.remove(filepath)  # Clean up invalid file
                except OSError:
                    pass  # File already removed or doesn't exist
                return jsonify({'error': f'Invalid medical image file: {validation_result["error"]}'}), 400
        except Exception as validation_error:
            try:
                os.remove(filepath)
            except OSError:
                pass
            return jsonify({'error': f'File validation failed: {str(validation_error)}'}), 400
        
        # Get file information
        try:
            file_info = get_file_info(filepath)
        except Exception as info_error:
            logger.warning(f"Could not get file info for {filepath}: {str(info_error)}")
            file_info = {'size': os.path.getsize(filepath) if os.path.exists(filepath) else 0}
        
        # Create database record
        study = MedicalStudy(
            patient_id=request.form.get('patient_id', 'UNKNOWN'),
            study_id=request.form.get('study_id', f'STUDY_{int(datetime.now().timestamp())}'),
            modality=validation_result.get('modality', 'UNKNOWN'),
            study_date=datetime.now(),
            description=request.form.get('description', ''),
            original_filename=file.filename,
            file_path=filepath,
            file_size=file_info['size'],
            processing_status='uploaded'
        )
        
        db.session.add(study)
        db.session.commit()
        
        logger.info(f"File uploaded successfully: {filename}, Study ID: {study.id}")
        
        return jsonify({
            'success': True,
            'study_id': study.id,
            'message': 'File uploaded successfully',
            'file_info': {
                'filename': filename,
                'size': file_info['size'],
                'modality': validation_result.get('modality'),
                'format': validation_result.get('format')
            }
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        # Clean up partially uploaded file if it exists
        if 'filepath' in locals() and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/process/<int:study_id>', methods=['POST'])
def process_study(study_id):
    """Process a medical study with segmentation and analysis"""
    try:
        study = MedicalStudy.query.get_or_404(study_id)
        
        if study.processing_status == 'processing':
            return jsonify({'error': 'Study is already being processed'}), 400
        
        # Update status
        study.processing_status = 'processing'
        db.session.commit()
        
        # Log processing start
        log_entry = ProcessingLog(
            study_id=study_id,
            log_level='INFO',
            message='Processing started',
            component='api'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        # Process the image
        processed_data = image_processor.process_image(study.file_path)
        if not processed_data['success']:
            study.processing_status = 'failed'
            db.session.commit()
            return jsonify({'error': processed_data['error']}), 500
        
        # Run segmentation
        segmentation_result = segmentation_service.segment_image(
            study.file_path, 
            output_dir=app.config['PROCESSED_FOLDER']
        )
        
        if not segmentation_result['success']:
            study.processing_status = 'failed'
            db.session.commit()
            return jsonify({'error': segmentation_result['error']}), 500
        
        # Generate LLM analysis if requested
        analysis_request = request.json.get('analysis_request', '')
        llm_report = None
        if analysis_request:
            llm_report = llm_service.analyze_segmentation(
                segmentation_result['data'], 
                analysis_request
            )
        
        # Create analysis result
        analysis = AnalysisResult(
            study_id=study_id,
            analysis_type='segmentation',
            status='completed',
            result_data=segmentation_result['data'],
            segmentation_path=segmentation_result.get('output_path'),
            report_text=llm_report.get('report', '') if llm_report else '',
            confidence_score=segmentation_result.get('confidence'),
            processing_time=segmentation_result.get('processing_time', 0),
            completed_at=datetime.now()
        )
        
        db.session.add(analysis)
        study.processing_status = 'completed'
        db.session.commit()
        
        logger.info(f"Study {study_id} processed successfully")
        
        return jsonify({
            'success': True,
            'study_id': study_id,
            'analysis_id': analysis.id,
            'message': 'Processing completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Processing error for study {study_id}: {str(e)}")
        if 'study' in locals():
            study.processing_status = 'failed'
            db.session.commit()
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/viewer/<int:study_id>')
def viewer(study_id):
    """Medical image viewer page"""
    study = MedicalStudy.query.get_or_404(study_id)
    analyses = AnalysisResult.query.filter_by(study_id=study_id).all()
    return render_template('viewer.html', study=study, analyses=analyses)

@app.route('/api/studies/<int:study_id>/image')
def serve_image(study_id):
    """Serve medical image for viewing with slice support"""
    try:
        study = MedicalStudy.query.get_or_404(study_id)
        slice_index = request.args.get('slice', 0, type=int)
        
        # Convert image to format suitable for web viewing
        web_image_path = image_processor.prepare_for_web(study.file_path, slice_index=slice_index)
        
        if not web_image_path or not os.path.exists(web_image_path):
            return jsonify({'error': 'Image preparation failed'}), 500
        
        return send_file(web_image_path, as_attachment=False)
        
    except Exception as e:
        logger.error(f"Error serving image for study {study_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/studies/<int:study_id>/info')
def get_study_info(study_id):
    """Get study information including slice count for NIFTI files"""
    try:
        study = MedicalStudy.query.get_or_404(study_id)
        
        # Process the file to get detailed information
        processed_info = image_processor.process_image(study.file_path)
        
        return jsonify({
            'id': study.id,
            'format': processed_info.get('format', 'unknown'),
            'slices': processed_info.get('slices', 1),
            'dimensions': processed_info.get('dimensions', {}),
            'modality': study.modality
        })
        
    except Exception as e:
        logger.error(f"Error getting study info for {study_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/segmentation/<int:analysis_id>')
def serve_segmentation(analysis_id):
    """Serve segmentation overlay data"""
    try:
        analysis = AnalysisResult.query.get_or_404(analysis_id)
        
        if not analysis.segmentation_path or not os.path.exists(analysis.segmentation_path):
            return jsonify({'error': 'Segmentation data not found'}), 404
        
        return send_file(analysis.segmentation_path, as_attachment=False)
        
    except Exception as e:
        logger.error(f"Error serving segmentation for analysis {analysis_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_with_llm():
    """Analyze study with LLM using natural language"""
    try:
        data = request.get_json()
        study_id = data.get('study_id')
        query = data.get('query', '')
        
        if not study_id or not query:
            return jsonify({'error': 'Study ID and query are required'}), 400
        
        study = MedicalStudy.query.get_or_404(study_id)
        
        # Get latest analysis for this study
        analysis = AnalysisResult.query.filter_by(study_id=study_id).order_by(AnalysisResult.created_at.desc()).first()
        
        # Use LLM service to process the query
        llm_response = llm_service.process_query(query, study, analysis)
        
        return jsonify({
            'success': True,
            'response': llm_response.get('response', ''),
            'confidence': llm_response.get('confidence', 0.0)
        })
        
    except Exception as e:
        logger.error(f"LLM analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/studies')
def list_studies():
    """Get list of all studies"""
    try:
        studies = MedicalStudy.query.order_by(MedicalStudy.created_at.desc()).all()
        
        studies_data = []
        for study in studies:
            studies_data.append({
                'id': study.id,
                'patient_id': study.patient_id,
                'study_id': study.study_id,
                'modality': study.modality,
                'study_date': study.study_date.isoformat() if study.study_date else None,
                'description': study.description,
                'processing_status': study.processing_status,
                'created_at': study.created_at.isoformat(),
                'file_size': study.file_size,
                'analysis_count': len(study.analyses)
            })
        
        return jsonify({'studies': studies_data})
        
    except Exception as e:
        logger.error(f"Error listing studies: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/study/<int:study_id>/status')
def get_study_status(study_id):
    """Get processing status of a study"""
    try:
        study = MedicalStudy.query.get_or_404(study_id)
        
        return jsonify({
            'study_id': study_id,
            'status': study.processing_status,
            'updated_at': study.updated_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting study status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 500MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# Cleanup old files periodically (can be called via cron or task scheduler)
@app.route('/api/cleanup', methods=['POST'])
def cleanup_files():
    """Clean up old processed files"""
    try:
        cleanup_old_files(app.config['PROCESSED_FOLDER'], days=7)
        return jsonify({'success': True, 'message': 'Cleanup completed'})
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        return jsonify({'error': str(e)}), 500
