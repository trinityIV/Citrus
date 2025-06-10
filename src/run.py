"""
Point d'entrée principal pour Citrus Music Server
Intègre toutes les fonctionnalités, y compris les téléchargements multi-appareils
"""

import os
import sys
from pathlib import Path
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

# Configuration du logger
from src.config.logging_config import setup_logging
logger = setup_logging()

# Chargement des variables d'environnement
load_dotenv()

def create_app():
    """Crée et configure l'application Flask"""
    # Configuration de l'application
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-me')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    
    # Chemins importants
    BASE_DIR = Path(__file__).parent.absolute()
    UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
    MUSIC_FOLDER = BASE_DIR / 'static' / 'music'
    
    # Créer les dossiers s'ils n'existent pas
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    MUSIC_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Configuration des dossiers
    app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
    app.config['MUSIC_FOLDER'] = str(MUSIC_FOLDER)
    
    # Configuration de la base de données
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(BASE_DIR / 'instance' / 'citrus.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialisation de la base de données
    from src.database import db
    db.init_app(app)
    
    # Création des tables si elles n'existent pas
    with app.app_context():
        db.create_all()
    
    # Configuration de Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from src.models.user import User
        return User.query.get(int(user_id))
    
    # Enregistrement des blueprints
    from src.routes.main import main_bp
    from src.routes.auth import auth_bp
    from src.routes.api import api_bp
    from src.routes.download import download_bp
    from src.routes.download_token import download_token_bp
    from src.routes.playlists import playlists_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(download_bp)
    app.register_blueprint(download_token_bp)
    app.register_blueprint(playlists_bp)
    
    # Initialisation du gestionnaire de téléchargements
    from src.routes.download import init_download_manager
    init_download_manager(app)
    
    # Gestion des erreurs
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"Erreur serveur: {error}")
        return {'error': 'Server error'}, 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    # Démarrer le serveur sur toutes les interfaces
    app.run(host='0.0.0.0', port=5000, debug=False)
