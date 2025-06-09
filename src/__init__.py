"""
Package Citrus Music Server
"""

from flask import Flask
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
    from .config import config
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
        return User.query.get(int(user_id))
    
    # Enregistrer les blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(playlists_bp)
    app.register_blueprint(spotify_bp)
    app.register_blueprint(download_bp)

    # Initialiser le gestionnaire de téléchargements
    from .routes.download import init_download_manager
    init_download_manager(app)

    init_db()


    # Nettoyer la session à la fin des requêtes
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    return app
