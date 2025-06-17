import os
import logging
import subprocess
import json
import time
from datetime import datetime
import tempfile
import shutil

logger = logging.getLogger(__name__)

class SegmentationService:
    """Service for medical image segmentation using TotalSegmentator"""
    
    def __init__(self):
        self.supported_formats = ['.dcm', '.nii', '.nii.gz']
        self.totalsegmentator_available = self._check_totalsegmentator()
    
    def _check_totalsegmentator(self):
        """Check if TotalSegmentator is available"""
        try:
            result = subprocess.run(['TotalSegmentator', '--help'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            logger.warning(f"TotalSegmentator not available: {str(e)}")
            return False
    
    def segment_image(self, input_path, output_dir=None, task='total'):
        """
        Segment medical image using TotalSegmentator
        
        Args:
            input_path: Path to input medical image
            output_dir: Directory to save segmentation results
            task: Segmentation task (total, lung_vessels, covid, etc.)
        
        Returns:
            dict with success status and result data
        """
        try:
            start_time = time.time()
            
            if not self.totalsegmentator_available:
                return self._mock_segmentation(input_path, output_dir)
            
            # Create output directory if not provided
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix='segmentation_')
            else:
                os.makedirs(output_dir, exist_ok=True)
            
            # Create unique output subdirectory
            timestamp = str(int(datetime.now().timestamp()))
            seg_output_dir = os.path.join(output_dir, f'segmentation_{timestamp}')
            os.makedirs(seg_output_dir, exist_ok=True)
            
            # Run TotalSegmentator
            cmd = [
                'TotalSegmentator',
                '-i', input_path,
                '-o', seg_output_dir,
                '--task', task,
                '--ml',  # Use machine learning mode
                '--quiet'  # Suppress verbose output
            ]
            
            logger.info(f"Running TotalSegmentator: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                cwd=os.getcwd()
            )
            
            processing_time = time.time() - start_time
            
            if result.returncode != 0:
                logger.error(f"TotalSegmentator failed: {result.stderr}")
                return {
                    'success': False,
                    'error': f'Segmentation failed: {result.stderr}',
                    'processing_time': processing_time
                }
            
            # Parse segmentation results
            segmentation_data = self._parse_segmentation_results(seg_output_dir)
            
            return {
                'success': True,
                'data': segmentation_data,
                'output_path': seg_output_dir,
                'processing_time': processing_time,
                'task': task,
                'confidence': 0.85  # TotalSegmentator typical confidence
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"TotalSegmentator timeout for {input_path}")
            return {
                'success': False,
                'error': 'Segmentation timeout (>10 minutes)',
                'processing_time': time.time() - start_time
            }
        except Exception as e:
            logger.error(f"Segmentation error for {input_path}: {str(e)}")
            return {
                'success': False,
                'error': f'Segmentation failed: {str(e)}',
                'processing_time': time.time() - start_time if 'start_time' in locals() else 0
            }
    
    def _parse_segmentation_results(self, output_dir):
        """Parse TotalSegmentator output and extract relevant information"""
        try:
            segmentation_data = {
                'timestamp': datetime.now().isoformat(),
                'output_directory': output_dir,
                'segmented_organs': [],
                'files': []
            }
            
            # Look for segmented organ files
            if os.path.exists(output_dir):
                for filename in os.listdir(output_dir):
                    if filename.endswith('.nii.gz') or filename.endswith('.nii'):
                        organ_name = os.path.splitext(filename)[0]
                        if organ_name.endswith('.nii'):
                            organ_name = os.path.splitext(organ_name)[0]
                        
                        file_path = os.path.join(output_dir, filename)
                        file_size = os.path.getsize(file_path)
                        
                        segmentation_data['segmented_organs'].append(organ_name)
                        segmentation_data['files'].append({
                            'organ': organ_name,
                            'filename': filename,
                            'path': file_path,
                            'size': file_size
                        })
            
            # Generate summary statistics
            segmentation_data['summary'] = {
                'total_organs': len(segmentation_data['segmented_organs']),
                'organs_found': segmentation_data['segmented_organs'][:10],  # Top 10 for display
                'total_files': len(segmentation_data['files'])
            }
            
            return segmentation_data
            
        except Exception as e:
            logger.error(f"Error parsing segmentation results: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': f'Failed to parse results: {str(e)}',
                'segmented_organs': [],
                'files': []
            }
    
    def _mock_segmentation(self, input_path, output_dir):
        """
        Mock segmentation for development/testing when TotalSegmentator is not available
        """
        logger.info("Using mock segmentation (TotalSegmentator not available)")
        
        try:
            # Create mock output directory
            if output_dir is None:
                output_dir = tempfile.mkdtemp(prefix='mock_segmentation_')
            else:
                os.makedirs(output_dir, exist_ok=True)
            
            timestamp = str(int(datetime.now().timestamp()))
            seg_output_dir = os.path.join(output_dir, f'mock_segmentation_{timestamp}')
            os.makedirs(seg_output_dir, exist_ok=True)
            
            # Create mock segmentation data
            mock_organs = [
                'liver', 'spleen', 'left_kidney', 'right_kidney', 
                'stomach', 'gallbladder', 'pancreas', 'left_lung', 'right_lung'
            ]
            
            # Create mock result files (empty files for demonstration)
            mock_files = []
            for organ in mock_organs:
                mock_file = os.path.join(seg_output_dir, f"{organ}.nii.gz")
                with open(mock_file, 'wb') as f:
                    f.write(b'mock_segmentation_data')  # Minimal mock data
                
                mock_files.append({
                    'organ': organ,
                    'filename': f"{organ}.nii.gz",
                    'path': mock_file,
                    'size': os.path.getsize(mock_file)
                })
            
            segmentation_data = {
                'timestamp': datetime.now().isoformat(),
                'output_directory': seg_output_dir,
                'segmented_organs': mock_organs,
                'files': mock_files,
                'summary': {
                    'total_organs': len(mock_organs),
                    'organs_found': mock_organs,
                    'total_files': len(mock_files)
                },
                'is_mock': True
            }
            
            return {
                'success': True,
                'data': segmentation_data,
                'output_path': seg_output_dir,
                'processing_time': 2.5,  # Mock processing time
                'task': 'total',
                'confidence': 0.75,  # Lower confidence for mock
                'is_mock': True
            }
            
        except Exception as e:
            logger.error(f"Mock segmentation error: {str(e)}")
            return {
                'success': False,
                'error': f'Mock segmentation failed: {str(e)}',
                'processing_time': 0
            }
    
    def get_available_tasks(self):
        """Get list of available segmentation tasks"""
        if not self.totalsegmentator_available:
            return ['total']  # Mock task
        
        try:
            # TotalSegmentator available tasks
            return [
                'total',           # Full body segmentation
                'lung_vessels',    # Lung vessel segmentation
                'covid',          # COVID-19 related segmentation
                'cerebral_bleed', # Cerebral bleeding
                'hip_implant',    # Hip implant
                'coronary_arteries', # Coronary arteries
                'body',           # Body composition
                'pleural_pericard_effusion'  # Pleural and pericardial effusion
            ]
        except Exception as e:
            logger.error(f"Error getting available tasks: {str(e)}")
            return ['total']
    
    def validate_input(self, input_path):
        """Validate input file for segmentation"""
        try:
            if not os.path.exists(input_path):
                return {'valid': False, 'error': 'Input file does not exist'}
            
            file_extension = self._get_file_extension(input_path)
            if file_extension not in self.supported_formats:
                return {
                    'valid': False, 
                    'error': f'Unsupported format: {file_extension}. Supported: {self.supported_formats}'
                }
            
            file_size = os.path.getsize(input_path)
            if file_size > 500 * 1024 * 1024:  # 500MB limit
                return {'valid': False, 'error': 'File too large (>500MB)'}
            
            if file_size < 1024:  # 1KB minimum
                return {'valid': False, 'error': 'File too small (<1KB)'}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {str(e)}'}
    
    def _get_file_extension(self, file_path):
        """Get file extension, handling .nii.gz specially"""
        if file_path.lower().endswith('.nii.gz'):
            return '.nii.gz'
        else:
            return os.path.splitext(file_path.lower())[1]
    
    def cleanup_old_results(self, output_dir, days=7):
        """Clean up old segmentation results"""
        try:
            if not os.path.exists(output_dir):
                return
            
            cutoff_time = time.time() - (days * 24 * 60 * 60)
            
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isdir(item_path) and item.startswith('segmentation_'):
                    if os.path.getctime(item_path) < cutoff_time:
                        shutil.rmtree(item_path)
                        logger.info(f"Cleaned up old segmentation result: {item_path}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old results: {str(e)}")
