"""
Package Citrus Music Server
"""

import time
import logging
from flask import Flask, g, request
from pathlib import Path
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .database import db_session, init_db, db
from .routes.playlists import playlists_bp
from .routes.main import main_bp
from .routes.auth import auth_bp
from .routes.api import api_bp
from .routes.spotify_auth import spotify_bp
from .routes.download import download_bp

migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name='default'):
    """Crée l'application Flask"""
    app = Flask(__name__)

    # Charger la configuration
    if config_name == 'testing':
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            WTF_CSRF_ENABLED=False,
            UPLOAD_FOLDER=str(Path(__file__).parent / 'static' / 'uploads'),
            MUSIC_FOLDER=str(Path(__file__).parent / 'static' / 'music'),
            PLAYLIST_FOLDER=str(Path(__file__).parent / 'static' / 'playlists'),
            SECRET_KEY='dev-key-for-testing',
            MAX_CONTENT_LENGTH=100 * 1024 * 1024  # 100MB
        )
    else:
        from .config import Config, DevelopmentConfig, ProductionConfig, TestingConfig
        config = {
            'development': DevelopmentConfig,
            'production': ProductionConfig,
            'testing': TestingConfig,
            'default': DevelopmentConfig
        }
        app.config.from_object(config[config_name])

    # Initialiser la base de données
    # Initialiser les extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configuration de Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models.user import User
        return db.session.get(User, int(user_id))  # Utilisation de session.get au lieu de query.get
    
    # Enregistrer les blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(playlists_bp)
    app.register_blueprint(spotify_bp)
    app.register_blueprint(download_bp)
    
    # Importer et enregistrer les blueprints supplémentaires
    from .routes.stream import stream_bp
    from .routes.iptv import iptv_bp
    from .routes.admin import admin_bp
    app.register_blueprint(stream_bp)
    app.register_blueprint(iptv_bp)
    app.register_blueprint(admin_bp)

    # Initialiser le gestionnaire de téléchargements
    from .routes.download import init_download_manager
    init_download_manager(app)

    init_db()


    # Configurer le logging pour les requêtes lentes
    if not app.config.get('TESTING'):
        @app.before_request
        def before_request():
            g.start_time = time.time()

        @app.after_request
        def after_request(response):
            # Mesurer le temps d'exécution de la requête
            if hasattr(g, 'start_time'):
                elapsed = time.time() - g.start_time
                # Journaliser les requêtes qui prennent plus de 500ms
                if elapsed > 0.5:
                    app.logger.warning(
                        f"Requête lente: {request.method} {request.path} "
                        f"({elapsed:.2f}s)"
                    )
            return response

    # Nettoyer la session à la fin des requêtes
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    return app
