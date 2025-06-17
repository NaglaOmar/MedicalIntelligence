import os
import logging
import shutil
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_file_info(file_path):
    """
    Get detailed information about a file
    
    Args:
        file_path: Path to the file
    
    Returns:
        dict with file information
    """
    try:
        if not os.path.exists(file_path):
            return {
                'exists': False,
                'error': 'File does not exist'
            }
        
        stat = os.stat(file_path)
        
        return {
            'exists': True,
            'path': file_path,
            'filename': os.path.basename(file_path),
            'directory': os.path.dirname(file_path),
            'size': stat.st_size,
            'size_human': format_file_size(stat.st_size),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'accessed': datetime.fromtimestamp(stat.st_atime),
            'extension': get_file_extension(file_path),
            'is_readable': os.access(file_path, os.R_OK),
            'is_writable': os.access(file_path, os.W_OK)
        }
        
    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {str(e)}")
        return {
            'exists': False,
            'error': f'Cannot get file info: {str(e)}'
        }

def format_file_size(size_bytes):
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Formatted size string
    """
    try:
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}"
        
    except Exception:
        return f"{size_bytes} B"

def get_file_extension(file_path):
    """
    Get file extension, handling special cases like .nii.gz
    
    Args:
        file_path: Path to the file
    
    Returns:
        File extension string
    """
    try:
        file_path = file_path.lower()
        
        if file_path.endswith('.nii.gz'):
            return '.nii.gz'
        elif file_path.endswith('.tar.gz'):
            return '.tar.gz'
        else:
            return os.path.splitext(file_path)[1]
            
    except Exception:
        return ''

def create_directory(directory_path):
    """
    Create directory if it doesn't exist
    
    Args:
        directory_path: Path to directory
    
    Returns:
        dict with creation result
    """
    try:
        if os.path.exists(directory_path):
            if os.path.isdir(directory_path):
                return {
                    'success': True,
                    'message': 'Directory already exists',
                    'path': directory_path
                }
            else:
                return {
                    'success': False,
                    'error': 'Path exists but is not a directory'
                }
        
        os.makedirs(directory_path, exist_ok=True)
        
        return {
            'success': True,
            'message': 'Directory created successfully',
            'path': directory_path
        }
        
    except Exception as e:
        logger.error(f"Error creating directory {directory_path}: {str(e)}")
        return {
            'success': False,
            'error': f'Cannot create directory: {str(e)}'
        }

def safe_file_move(source_path, destination_path):
    """
    Safely move a file to a new location
    
    Args:
        source_path: Source file path
        destination_path: Destination file path
    
    Returns:
        dict with move result
    """
    try:
        if not os.path.exists(source_path):
            return {
                'success': False,
                'error': 'Source file does not exist'
            }
        
        # Create destination directory if needed
        dest_dir = os.path.dirname(destination_path)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        
        # Check if destination already exists
        if os.path.exists(destination_path):
            return {
                'success': False,
                'error': 'Destination file already exists'
            }
        
        # Move the file
        shutil.move(source_path, destination_path)
        
        return {
            'success': True,
            'message': 'File moved successfully',
            'source': source_path,
            'destination': destination_path
        }
        
    except Exception as e:
        logger.error(f"Error moving file from {source_path} to {destination_path}: {str(e)}")
        return {
            'success': False,
            'error': f'Cannot move file: {str(e)}'
        }

def safe_file_delete(file_path):
    """
    Safely delete a file
    
    Args:
        file_path: Path to file to delete
    
    Returns:
        dict with deletion result
    """
    try:
        if not os.path.exists(file_path):
            return {
                'success': True,
                'message': 'File does not exist (already deleted)'
            }
        
        if os.path.isdir(file_path):
            return {
                'success': False,
                'error': 'Path is a directory, not a file'
            }
        
        os.remove(file_path)
        
        return {
            'success': True,
            'message': 'File deleted successfully',
            'path': file_path
        }
        
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        return {
            'success': False,
            'error': f'Cannot delete file: {str(e)}'
        }

def cleanup_old_files(directory, days=7, file_pattern=None):
    """
    Clean up old files in a directory
    
    Args:
        directory: Directory to clean
        days: Files older than this many days will be deleted
        file_pattern: Optional pattern to match files (e.g., "*.tmp")
    
    Returns:
        dict with cleanup result
    """
    try:
        if not os.path.exists(directory):
            return {
                'success': True,
                'message': 'Directory does not exist',
                'files_deleted': 0
            }
        
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        files_deleted = 0
        total_size_freed = 0
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                
                try:
                    # Check file pattern if specified
                    if file_pattern:
                        import fnmatch
                        if not fnmatch.fnmatch(file, file_pattern):
                            continue
                    
                    # Check file age
                    file_stat = os.stat(file_path)
                    if file_stat.st_mtime < cutoff_time:
                        file_size = file_stat.st_size
                        os.remove(file_path)
                        files_deleted += 1
                        total_size_freed += file_size
                        logger.info(f"Deleted old file: {file_path}")
                        
                except Exception as e:
                    logger.warning(f"Could not delete file {file_path}: {str(e)}")
                    continue
        
        return {
            'success': True,
            'message': f'Cleanup completed',
            'files_deleted': files_deleted,
            'size_freed': total_size_freed,
            'size_freed_human': format_file_size(total_size_freed)
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup of {directory}: {str(e)}")
        return {
            'success': False,
            'error': f'Cleanup failed: {str(e)}',
            'files_deleted': 0
        }

def get_directory_size(directory):
    """
    Get total size of all files in a directory
    
    Args:
        directory: Directory path
    
    Returns:
        dict with size information
    """
    try:
        if not os.path.exists(directory):
            return {
                'success': False,
                'error': 'Directory does not exist'
            }
        
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    file_count += 1
                except Exception as e:
                    logger.warning(f"Could not get size of file {file_path}: {str(e)}")
                    continue
        
        return {
            'success': True,
            'total_size': total_size,
            'total_size_human': format_file_size(total_size),
            'file_count': file_count,
            'directory': directory
        }
        
    except Exception as e:
        logger.error(f"Error getting directory size for {directory}: {str(e)}")
        return {
            'success': False,
            'error': f'Cannot get directory size: {str(e)}'
        }

def ensure_upload_directory(upload_dir):
    """
    Ensure upload directory exists and is writable
    
    Args:
        upload_dir: Upload directory path
    
    Returns:
        dict with validation result
    """
    try:
        # Create directory if it doesn't exist
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
        
        # Check if it's a directory
        if not os.path.isdir(upload_dir):
            return {
                'valid': False,
                'error': 'Upload path exists but is not a directory'
            }
        
        # Check if writable
        if not os.access(upload_dir, os.W_OK):
            return {
                'valid': False,
                'error': 'Upload directory is not writable'
            }
        
        # Get directory info
        dir_info = get_directory_size(upload_dir)
        
        return {
            'valid': True,
            'path': upload_dir,
            'writable': True,
            'current_size': dir_info.get('total_size', 0),
            'current_files': dir_info.get('file_count', 0)
        }
        
    except Exception as e:
        logger.error(f"Error validating upload directory {upload_dir}: {str(e)}")
        return {
            'valid': False,
            'error': f'Upload directory validation failed: {str(e)}'
        }
