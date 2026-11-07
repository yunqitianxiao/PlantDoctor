import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv


load_dotenv()
 
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    DATABASE_PATH = 'instance/plant_doctor.db'
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    CLASSIFY_MODEL_PATH = 'best_classification_model.pth'
    SEG_MODEL_PATH = 'best_segmentation_model.pth'
    MASK2FORMER_PATH = 'mask2former_local'
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    DEEPSEEK_API_BASE = os.environ.get('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
    DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
    SEVERITY_THRESHOLDS = {
        'healthy': 0.02,
        'mild': 0.10,
        'moderate': 0.30,
        'severe': 1.0
    }
    SEVERITY_DESCRIPTIONS = {
        'healthy': ('健康', '#2e7d64', '植株生长正常，无需处理'),
        'mild': ('轻度', '#f4a261', '建议加强观察，可进行预防性处理'),
        'moderate': ('中度', '#e76f51', '需要及时治疗，防止扩散'),
        'severe': ('重度', '#e63946', '立即采取紧急措施，考虑隔离或清除病株')
    }
