"""
Script pour exécuter les migrations Alembic
"""

import os
import sys
import logging
from flask import Flask
from flask_migrate import Migrate, upgrade

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Crée une application Flask pour les migrations"""
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///instance/citrus.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    
    # Initialiser la base de données
    from src.database import db
    db.init_app(app)
    
    # Initialiser Flask-Migrate
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    migrate = Migrate(app, db, directory=migrations_dir)
    
    return app, migrate

def run_migrations():
    """Exécute les migrations Alembic"""
    logger.info("Exécution des migrations...")
    
    app, _ = create_app()
    
    with app.app_context():
        # Exécuter les migrations
        upgrade()
        
        logger.info("Migrations terminées")

def main():
    """Fonction principale"""
    logger.info("Démarrage du script de migration...")
    
    try:
        run_migrations()
        logger.info("Script de migration terminé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution des migrations : {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
