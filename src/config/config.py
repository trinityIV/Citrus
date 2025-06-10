"""
Configuration pour l'application Citrus Music Server
"""

import os
from pathlib import Path

class Config:
    """Configuration de base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-development'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///citrus.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(Path(__file__).parent.parent / 'static' / 'uploads')
    MUSIC_FOLDER = str(Path(__file__).parent.parent / 'static' / 'music')
    PLAYLIST_FOLDER = str(Path(__file__).parent.parent / 'static' / 'playlists')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    
    # Configuration du cache
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_THRESHOLD = 500  # Nombre maximum d'éléments dans le cache

class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log des requêtes SQL

class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # En production, utiliser une clé secrète forte
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-key-should-be-set-in-env'
    
    # En production, utiliser une base de données plus robuste
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///citrus_prod.db'

class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
