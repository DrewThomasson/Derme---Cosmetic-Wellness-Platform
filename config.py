"""
Configuration file for Derme application
"""
import os

class Config:
    """Application configuration"""
    
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///derme.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Google Gemini API Settings
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
    
    # Enable/Disable Gemini features
    USE_GEMINI_FOR_OCR = os.environ.get('USE_GEMINI_FOR_OCR', 'true').lower() == 'true'
    USE_GEMINI_FOR_ALLERGEN_INFO = os.environ.get('USE_GEMINI_FOR_ALLERGEN_INFO', 'true').lower() == 'true'
    
    # Fallback to Tesseract OCR if Gemini is not available
    FALLBACK_TO_TESSERACT = os.environ.get('FALLBACK_TO_TESSERACT', 'true').lower() == 'true'
    
    # Application Features
    RUNNING_ON_HUGGINGFACE = os.environ.get('SPACE_ID') is not None
    
    # Allergen Analysis Settings
    CONFIDENCE_THRESHOLD = float(os.environ.get('CONFIDENCE_THRESHOLD', '0.6'))
    MAX_ALLERGEN_SYNONYMS = int(os.environ.get('MAX_ALLERGEN_SYNONYMS', '10'))
