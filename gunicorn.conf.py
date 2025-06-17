# Gunicorn configuration for medical imaging application
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 1  # Keep single worker for development
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout settings for large medical file uploads
timeout = 300  # 5 minutes for large DICOM files
keepalive = 2
graceful_timeout = 30

# Memory and request limits
limit_request_line = 8192
limit_request_fields = 100
limit_request_field_size = 16384

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
capture_output = True

# Process naming
proc_name = "medical_imaging_app"

# Server mechanics
preload_app = True
reload = True
reuse_port = True

# SSL (for production)
# keyfile = None
# certfile = None

# Application specific
raw_env = [
    'FLASK_ENV=development',
]