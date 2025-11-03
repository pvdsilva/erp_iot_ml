# config.py - Configurações do sistema

import os
from datetime import timedelta

class Config:
    """Configurações base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'erp_iot_ml_secret_key_2025_university_project'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # Configurações do banco de dados
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'erp_iot_ml',
        'user': 'root',
        'password': 'senha gerada no phpmyadim para acesso ao banco de dados',
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }
    
    # Configurações da API de Clima
    WEATHER_API_KEY = 'b03cc9d9c6ee7fd9f8cc3b744378064d'
    WEATHER_CACHE_DURATION = 600  # 10 minutos
    
    # Configurações de segurança
    SESSION_COOKIE_SECURE = False  # True em produção com HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configurações de upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Configurações de logging
    LOG_LEVEL = 'INFO'

class DevelopmentConfig(Config):
    """Configurações de desenvolvimento"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configurações de produção"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

# Configuração atual
config = DevelopmentConfig()
