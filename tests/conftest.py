"""
Configuration des tests
"""

import os
import tempfile
import pytest
from src import create_app
from src.database import db as _db, Base
from src.models.user import User
from src.models.playlist import Playlist
from src.models.track import Track

@pytest.fixture(scope='session')
def app(request):
    """Crée une instance de l'application Flask pour les tests."""
    app = create_app('testing')
    
    # Configurer la base de données de test
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app

@pytest.fixture(scope='function')
def db(app, request):
    """Fournit une session de base de données isolée pour chaque test."""
    with app.app_context():
        # Créer toutes les tables
        Base.metadata.create_all(bind=_db.engine)
        
        # Créer une connexion et une transaction
        connection = _db.engine.connect()
        transaction = connection.begin()
        
        # Créer une session liée à cette connexion
        options = dict(bind=connection, binds={})
        session = _db.create_scoped_session(options=options)
        
        # Remplacer la session globale par notre session de test
        _db.session = session
        
        def teardown():
            transaction.rollback()
            connection.close()
            session.remove()
        
        request.addfinalizer(teardown)
        
        return _db

@pytest.fixture(scope='function')
def session(db, request):
    """Fournit une session SQLAlchemy pour les tests."""
    return db.session
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope='function')
def test_user(session):
    """Crée un utilisateur de test"""
    user = User(username='test_user', email='test@example.com')
    user.set_password('password123')
    session.add(user)
    session.commit()
    return user

@pytest.fixture(scope='function')
def test_playlist(session, test_user):
    """Crée une playlist de test"""
    playlist = Playlist(
        name='Test Playlist',
        description='Une playlist de test',
        user_id=test_user.id
    )
    session.add(playlist)
    session.commit()
    return playlist

@pytest.fixture(scope='function')
def test_tracks(session):
    """Crée des pistes de test"""
    tracks = [
        Track(
            title=f'Track {i}',
            artist=f'Artist {i}',
            duration=180 + i * 30
        )
        for i in range(3)
    ]
    session.add_all(tracks)
    session.commit()
    return tracks

@pytest.fixture(scope='function')
def client(app):
    """Crée un client de test"""
    return app.test_client()

@pytest.fixture(scope='function')
def authenticated_client(app, client, test_user):
    """Crée un client de test authentifié"""
    with client.session_transaction() as session:
        session['user_id'] = test_user.id
    return client
