"""
Configuration de la base de données SQLAlchemy
"""

import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool

# Créer l'instance SQLAlchemy
db = SQLAlchemy()

# Créer le moteur SQLAlchemy
if os.environ.get('TESTING'):
    # Base de données en mémoire pour les tests
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool
    )
else:
    # Base de données SQLite pour le développement
    engine = create_engine('sqlite:///citrus.db')

# Créer la session
db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

# Classe de base pour les modèles
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    """Initialise la base de données"""
    from .models import user
    from .models import playlist
    from .models import track
    Base.metadata.create_all(bind=engine)

def shutdown_session(exception=None):
    """Ferme la session à la fin de chaque requête"""
    db_session.remove()
