"""
Configuration de l'application
"""

import os
from pathlib import Path

class Config:
    """Configuration de base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///citrus.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Dossiers
    BASE_DIR = Path(__file__).parent.absolute()
    UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
    MUSIC_FOLDER = BASE_DIR / 'static' / 'music'
    PLAYLIST_FOLDER = BASE_DIR / 'static' / 'playlists'
    
    # Limites
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac', 'm4a', 'wma'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # yt-dlp configuration
    YTDLP_OPTIONS = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'outtmpl': str(MUSIC_FOLDER / '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True
    }
    
    # APIs gratuites pour métadonnées et images
    MUSICBRAINZ_API = 'https://musicbrainz.org/ws/2'
    LASTFM_API = 'https://ws.audioscrobbler.com/2.0'
    COVERARTARCHIVE_API = 'https://coverartarchive.org'
    
    # APIs IPTV gratuites
    IPTV_SOURCES = [
        'https://iptv-org.github.io/iptv/index.m3u',
        'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8'
    ]

class DevelopmentConfig(Config):
    """Configuration de développement"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Configuration de production"""
    DEBUG = False
    FLASK_ENV = 'production'
    # En production, utilisez une vraie clé secrète
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)

class TestingConfig(Config):
    """Configuration de test"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration par défaut
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
