import os
import logging
import pydicom
import nibabel as nib

logger = logging.getLogger(__name__)

def validate_medical_file(file_path):
    """
    Validate medical image file (DICOM or NIFTI)
    
    Args:
        file_path: Path to the medical image file
    
    Returns:
        dict with validation results
    """
    try:
        if not os.path.exists(file_path):
            return {
                'valid': False,
                'error': 'File does not exist'
            }
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return {
                'valid': False,
                'error': 'File is empty'
            }
        
        if file_size > 500 * 1024 * 1024:  # 500MB limit
            return {
                'valid': False,
                'error': 'File too large (>500MB)'
            }
        
        # Determine file type and validate
        if file_path.lower().endswith('.dcm'):
            return validate_dicom_file(file_path)
        elif file_path.lower().endswith('.nii') or file_path.lower().endswith('.nii.gz'):
            return validate_nifti_file(file_path)
        else:
            return {
                'valid': False,
                'error': 'Unsupported file format. Only DICOM (.dcm) and NIFTI (.nii, .nii.gz) are supported'
            }
            
    except Exception as e:
        logger.error(f"Error validating file {file_path}: {str(e)}")
        return {
            'valid': False,
            'error': f'Validation error: {str(e)}'
        }

def validate_dicom_file(file_path):
    """
    Validate DICOM file
    
    Args:
        file_path: Path to DICOM file
    
    Returns:
        dict with validation results
    """
    try:
        # Try to read DICOM file
        ds = pydicom.dcmread(file_path, force=True)
        
        # Check for required DICOM elements
        required_elements = ['PatientID', 'StudyInstanceUID', 'SeriesInstanceUID']
        missing_elements = []
        
        for element in required_elements:
            if not hasattr(ds, element) or getattr(ds, element) is None:
                missing_elements.append(element)
        
        # Check for pixel data
        if not hasattr(ds, 'pixel_array'):
            return {
                'valid': False,
                'error': 'DICOM file does not contain image data'
            }
        
        # Try to access pixel data
        try:
            pixel_array = ds.pixel_array
            if pixel_array is None or pixel_array.size == 0:
                return {
                    'valid': False,
                    'error': 'DICOM file contains empty image data'
                }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Cannot read DICOM pixel data: {str(e)}'
            }
        
        # Get modality
        modality = str(ds.get('Modality', 'UNKNOWN'))
        
        # Validate image dimensions
        rows = int(ds.get('Rows', 0))
        cols = int(ds.get('Columns', 0))
        
        if rows == 0 or cols == 0:
            return {
                'valid': False,
                'error': 'Invalid image dimensions'
            }
        
        validation_result = {
            'valid': True,
            'format': 'DICOM',
            'modality': modality,
            'dimensions': pixel_array.shape,
            'patient_id': str(ds.get('PatientID', 'UNKNOWN')),
            'study_id': str(ds.get('StudyInstanceUID', 'UNKNOWN'))
        }
        
        if missing_elements:
            validation_result['warnings'] = [f'Missing DICOM elements: {", ".join(missing_elements)}']
        
        return validation_result
        
    except pydicom.errors.InvalidDicomError:
        return {
            'valid': False,
            'error': 'File is not a valid DICOM file'
        }
    except Exception as e:
        logger.error(f"Error validating DICOM file {file_path}: {str(e)}")
        return {
            'valid': False,
            'error': f'DICOM validation error: {str(e)}'
        }

def validate_nifti_file(file_path):
    """
    Validate NIFTI file
    
    Args:
        file_path: Path to NIFTI file
    
    Returns:
        dict with validation results
    """
    try:
        # Try to load NIFTI file
        img = nib.load(file_path)
        
        # Get image data and header
        try:
            data = img.get_fdata()
        except Exception as e:
            return {
                'valid': False,
                'error': f'Cannot read NIFTI image data: {str(e)}'
            }
        
        if data is None or data.size == 0:
            return {
                'valid': False,
                'error': 'NIFTI file contains empty image data'
            }
        
        header = img.header
        
        # Validate dimensions
        if len(data.shape) < 2:
            return {
                'valid': False,
                'error': 'Invalid image dimensions (must be at least 2D)'
            }
        
        if len(data.shape) > 4:
            return {
                'valid': False,
                'error': 'Unsupported image dimensions (max 4D supported)'
            }
        
        # Check for reasonable data range
        if data.min() == data.max():
            return {
                'valid': False,
                'error': 'Image contains no variation (all pixels have same value)'
            }
        
        # Get voxel sizes
        voxel_sizes = header.get_zooms()
        
        return {
            'valid': True,
            'format': 'NIFTI',
            'modality': 'MRI',  # Default assumption for NIFTI
            'dimensions': data.shape,
            'voxel_sizes': list(voxel_sizes),
            'data_type': str(data.dtype),
            'file_size': os.path.getsize(file_path)
        }
        
    except nib.filebasedimages.ImageFileError:
        return {
            'valid': False,
            'error': 'File is not a valid NIFTI file'
        }
    except Exception as e:
        logger.error(f"Error validating NIFTI file {file_path}: {str(e)}")
        return {
            'valid': False,
            'error': f'NIFTI validation error: {str(e)}'
        }

def validate_patient_id(patient_id):
    """
    Validate patient ID format
    
    Args:
        patient_id: Patient ID string
    
    Returns:
        dict with validation results
    """
    try:
        if not patient_id or not isinstance(patient_id, str):
            return {
                'valid': False,
                'error': 'Patient ID must be a non-empty string'
            }
        
        patient_id = patient_id.strip()
        
        if len(patient_id) < 1:
            return {
                'valid': False,
                'error': 'Patient ID cannot be empty'
            }
        
        if len(patient_id) > 64:
            return {
                'valid': False,
                'error': 'Patient ID too long (max 64 characters)'
            }
        
        # Check for invalid characters
        invalid_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        for char in invalid_chars:
            if char in patient_id:
                return {
                    'valid': False,
                    'error': f'Patient ID contains invalid character: {char}'
                }
        
        return {
            'valid': True,
            'normalized_id': patient_id.upper()  # Normalize to uppercase
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Patient ID validation error: {str(e)}'
        }

def validate_study_description(description):
    """
    Validate study description
    
    Args:
        description: Study description string
    
    Returns:
        dict with validation results
    """
    try:
        if description is None:
            description = ""
        
        if not isinstance(description, str):
            return {
                'valid': False,
                'error': 'Description must be a string'
            }
        
        description = description.strip()
        
        if len(description) > 1000:
            return {
                'valid': False,
                'error': 'Description too long (max 1000 characters)'
            }
        
        return {
            'valid': True,
            'normalized_description': description
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Description validation error: {str(e)}'
        }
