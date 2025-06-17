import os
import logging
import numpy as np
import pydicom
import nibabel as nib
from PIL import Image
import cv2
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Service for processing medical images (DICOM/NIFTI)"""
    
    def __init__(self):
        self.supported_formats = ['.dcm', '.nii', '.nii.gz']
    
    def process_image(self, file_path):
        """
        Process medical image and extract metadata
        Returns dict with success status and processed data
        """
        try:
            file_extension = self._get_file_extension(file_path)
            
            if file_extension == '.dcm':
                return self._process_dicom(file_path)
            elif file_extension in ['.nii', '.nii.gz']:
                return self._process_nifti(file_path)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file format: {file_extension}'
                }
                
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {str(e)}")
            return {
                'success': False,
                'error': f'Image processing failed: {str(e)}'
            }
    
    def _process_dicom(self, file_path):
        """Process DICOM file"""
        try:
            ds = pydicom.dcmread(file_path)
            
            # Extract image data
            image_data = ds.pixel_array
            
            # Extract metadata
            metadata = {
                'patient_id': str(ds.get('PatientID', 'UNKNOWN')),
                'study_id': str(ds.get('StudyInstanceUID', 'UNKNOWN')),
                'series_id': str(ds.get('SeriesInstanceUID', 'UNKNOWN')),
                'modality': str(ds.get('Modality', 'UNKNOWN')),
                'study_date': str(ds.get('StudyDate', '')),
                'study_time': str(ds.get('StudyTime', '')),
                'institution': str(ds.get('InstitutionName', '')),
                'manufacturer': str(ds.get('Manufacturer', '')),
                'model': str(ds.get('ManufacturerModelName', '')),
                'slice_thickness': float(ds.get('SliceThickness', 0)) if ds.get('SliceThickness') else None,
                'pixel_spacing': [float(x) for x in ds.get('PixelSpacing', [])] if ds.get('PixelSpacing') else None,
                'image_orientation': [float(x) for x in ds.get('ImageOrientationPatient', [])] if ds.get('ImageOrientationPatient') else None,
                'image_position': [float(x) for x in ds.get('ImagePositionPatient', [])] if ds.get('ImagePositionPatient') else None,
                'rows': int(ds.get('Rows', 0)),
                'columns': int(ds.get('Columns', 0)),
                'bits_allocated': int(ds.get('BitsAllocated', 0)),
                'bits_stored': int(ds.get('BitsStored', 0)),
                'window_center': float(ds.get('WindowCenter', 0)) if ds.get('WindowCenter') else None,
                'window_width': float(ds.get('WindowWidth', 0)) if ds.get('WindowWidth') else None,
            }
            
            # Calculate basic statistics
            stats = self._calculate_image_stats(image_data)
            
            return {
                'success': True,
                'format': 'DICOM',
                'metadata': metadata,
                'image_stats': stats,
                'dimensions': image_data.shape,
                'dtype': str(image_data.dtype)
            }
            
        except Exception as e:
            logger.error(f"Error processing DICOM {file_path}: {str(e)}")
            return {
                'success': False,
                'error': f'DICOM processing failed: {str(e)}'
            }
    
    def _process_nifti(self, file_path):
        """Process NIFTI file"""
        try:
            img = nib.load(file_path)
            image_data = img.get_fdata()
            header = img.header
            
            # Extract metadata
            metadata = {
                'dimensions': list(image_data.shape),
                'voxel_size': [float(x) for x in header.get_zooms()],
                'data_type': str(header.get_data_dtype()),
                'units': {
                    'space': header.get_xyzt_units()[0],
                    'time': header.get_xyzt_units()[1]
                },
                'qform_code': int(header['qform_code']),
                'sform_code': int(header['sform_code']),
                'affine': img.affine.tolist(),
                'description': header['descrip'].tobytes().decode('utf-8', errors='ignore').strip('\x00'),
            }
            
            # Calculate basic statistics
            stats = self._calculate_image_stats(image_data)
            
            return {
                'success': True,
                'format': 'NIFTI',
                'metadata': metadata,
                'image_stats': stats,
                'dimensions': image_data.shape,
                'dtype': str(image_data.dtype),
                'slices': image_data.shape[2] if len(image_data.shape) >= 3 else 1
            }
            
        except Exception as e:
            logger.error(f"Error processing NIFTI {file_path}: {str(e)}")
            return {
                'success': False,
                'error': f'NIFTI processing failed: {str(e)}'
            }
    
    def _calculate_image_stats(self, image_data):
        """Calculate basic statistics for image data"""
        try:
            # Handle NaN values
            clean_data = image_data[~np.isnan(image_data)] if np.any(np.isnan(image_data)) else image_data
            
            stats = {
                'min': float(np.min(clean_data)),
                'max': float(np.max(clean_data)),
                'mean': float(np.mean(clean_data)),
                'std': float(np.std(clean_data)),
                'median': float(np.median(clean_data)),
                'percentile_5': float(np.percentile(clean_data, 5)),
                'percentile_95': float(np.percentile(clean_data, 95)),
                'non_zero_count': int(np.count_nonzero(clean_data)),
                'total_voxels': int(clean_data.size)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating image stats: {str(e)}")
            return {}
    
    def prepare_for_web(self, file_path, slice_index=0):
        """
        Prepare medical image for web viewing
        Returns path to web-compatible image
        """
        try:
            file_extension = self._get_file_extension(file_path)
            output_dir = os.path.dirname(file_path)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            if file_extension == '.dcm':
                return self._dicom_to_web(file_path, output_dir, base_name)
            elif file_extension in ['.nii', '.nii.gz']:
                return self._nifti_to_web(file_path, output_dir, base_name, slice_index)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error preparing image for web {file_path}: {str(e)}")
            return None
    
    def _dicom_to_web(self, file_path, output_dir, base_name):
        """Convert DICOM to web-viewable format"""
        try:
            ds = pydicom.dcmread(file_path)
            image_data = ds.pixel_array
            
            # Normalize image data
            normalized = self._normalize_for_display(image_data)
            
            # Save as PNG for web viewing
            output_path = os.path.join(output_dir, f"{base_name}_web.png")
            Image.fromarray(normalized).save(output_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting DICOM to web format: {str(e)}")
            return None
    
    def _nifti_to_web(self, file_path, output_dir, base_name, slice_index=None):
        """Convert NIFTI to web-viewable format with slice support"""
        try:
            img = nib.load(file_path)
            image_data = img.get_fdata()
            
            # Handle slice selection for 3D volumes
            if len(image_data.shape) == 3:
                total_slices = image_data.shape[2]
                if slice_index is None:
                    slice_index = total_slices // 2  # Default to middle slice
                else:
                    slice_index = max(0, min(slice_index, total_slices - 1))  # Clamp to valid range
                
                slice_data = image_data[:, :, slice_index]
            else:
                # If 2D, use as is
                slice_data = image_data
                slice_index = 0
            
            # Normalize image data
            normalized = self._normalize_for_display(slice_data)
            
            # Create unique filename for each slice
            if slice_index > 0:
                output_path = os.path.join(output_dir, f"{base_name}_slice_{slice_index}_web.png")
            else:
                output_path = os.path.join(output_dir, f"{base_name}_web.png")
            
            # Save as PNG for web viewing
            Image.fromarray(normalized).save(output_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting NIFTI to web format: {str(e)}")
            return None
    
    def _normalize_for_display(self, image_data):
        """Normalize image data for display (0-255 range)"""
        try:
            # Handle different data types and ranges
            if image_data.dtype == np.uint8:
                return image_data
            
            # Remove outliers for better visualization
            p1, p99 = np.percentile(image_data, (1, 99))
            image_data = np.clip(image_data, p1, p99)
            
            # Normalize to 0-255
            if p99 > p1:
                normalized = ((image_data - p1) / (p99 - p1) * 255).astype(np.uint8)
            else:
                normalized = np.zeros_like(image_data, dtype=np.uint8)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing image: {str(e)}")
            # Return zeros as fallback
            return np.zeros_like(image_data, dtype=np.uint8)
    
    def _get_file_extension(self, file_path):
        """Get file extension, handling .nii.gz specially"""
        if file_path.lower().endswith('.nii.gz'):
            return '.nii.gz'
        else:
            return os.path.splitext(file_path.lower())[1]
    
    def extract_slices(self, file_path, output_dir, slice_count=5):
        """
        Extract multiple slices from 3D medical image
        Returns list of slice file paths
        """
        try:
            file_extension = self._get_file_extension(file_path)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            if file_extension == '.dcm':
                ds = pydicom.dcmread(file_path)
                image_data = ds.pixel_array
            elif file_extension in ['.nii', '.nii.gz']:
                img = nib.load(file_path)
                image_data = img.get_fdata()
            else:
                return []
            
            slice_paths = []
            
            if len(image_data.shape) == 3:
                # Extract evenly spaced slices
                depth = image_data.shape[2]
                slice_indices = np.linspace(0, depth-1, min(slice_count, depth), dtype=int)
                
                for i, slice_idx in enumerate(slice_indices):
                    slice_data = image_data[:, :, slice_idx]
                    normalized = self._normalize_for_display(slice_data)
                    
                    slice_path = os.path.join(output_dir, f"{base_name}_slice_{i+1}.png")
                    Image.fromarray(normalized).save(slice_path)
                    slice_paths.append(slice_path)
            
            return slice_paths
            
        except Exception as e:
            logger.error(f"Error extracting slices from {file_path}: {str(e)}")
            return []
