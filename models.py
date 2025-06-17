from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to medical studies
    studies = db.relationship('MedicalStudy', backref='user', lazy=True)

class MedicalStudy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(64), nullable=False)
    study_id = db.Column(db.String(64), nullable=False)
    modality = db.Column(db.String(16), nullable=False)  # CT, MRI, etc.
    study_date = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    processing_status = db.Column(db.String(32), default='uploaded')  # uploaded, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key to user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationship to analysis results
    analyses = db.relationship('AnalysisResult', backref='study', lazy=True)

class AnalysisResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    analysis_type = db.Column(db.String(64), nullable=False)  # segmentation, detection, etc.
    status = db.Column(db.String(32), default='pending')  # pending, completed, failed
    result_data = db.Column(db.JSON)  # Store JSON results
    segmentation_path = db.Column(db.String(500))  # Path to segmentation files
    report_text = db.Column(db.Text)  # LLM generated report
    confidence_score = db.Column(db.Float)
    processing_time = db.Column(db.Float)  # Time in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Foreign key to medical study
    study_id = db.Column(db.Integer, db.ForeignKey('medical_study.id'), nullable=False)

class ProcessingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('medical_study.id'), nullable=False)
    log_level = db.Column(db.String(16), nullable=False)  # DEBUG, INFO, WARNING, ERROR
    message = db.Column(db.Text, nullable=False)
    component = db.Column(db.String(64))  # Which component logged this
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    study = db.relationship('MedicalStudy', backref='logs')
