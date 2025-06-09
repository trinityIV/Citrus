"""
Tests unitaires pour les routes
"""

import unittest
import json
import os
from io import BytesIO
from flask import Flask
from werkzeug.datastructures import FileStorage
from src.models.user import User
from src.models.playlist import Playlist
from src.models.track import Track
from src.routes.playlists import playlists_bp
from src.database import Base, db_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestPlaylistRoutes(unittest.TestCase):
    """Tests pour les routes des playlists"""

    def setUp(self):
        """Initialisation avant chaque test"""
        # Créer l'application Flask de test
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_key'
        self.app.config['UPLOAD_FOLDER'] = 'tests/uploads'
        
        # Créer les dossiers d'upload temporaires
        os.makedirs(os.path.join(self.app.config['UPLOAD_FOLDER'], 'playlists'), exist_ok=True)

        # Enregistrer le blueprint
        self.app.register_blueprint(playlists_bp)

        # Créer une base de données en mémoire
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Créer un utilisateur de test
        self.user = User(username='test_user', email='test@example.com')
        self.user.set_password('password123')
        self.session.add(self.user)
        self.session.commit()

        # Client de test
        self.client = self.app.test_client()

        # Simuler une connexion utilisateur
        with self.client.session_transaction() as session:
            session['user_id'] = self.user.id

    def tearDown(self):
        """Nettoyage après chaque test"""
        self.session.close()
        Base.metadata.drop_all(self.engine)
        
        # Nettoyer les fichiers uploadés
        import shutil
        if os.path.exists(self.app.config['UPLOAD_FOLDER']):
            shutil.rmtree(self.app.config['UPLOAD_FOLDER'])

    def test_get_playlists(self):
        """Test la récupération des playlists"""
        # Créer quelques playlists de test
        playlists = [
            Playlist(name=f'Playlist {i}', user_id=self.user.id)
            for i in range(3)
        ]
        self.session.add_all(playlists)
        self.session.commit()

        # Faire la requête
        response = self.client.get('/api/playlists')
        self.assertEqual(response.status_code, 200)

        # Vérifier les données
        data = json.loads(response.data)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['name'], 'Playlist 0')

    def test_create_playlist(self):
        """Test la création d'une playlist"""
        # Créer une image de test
        image = (BytesIO(b'test image content'), 'cover.jpg')
        
        # Données de la playlist
        data = {
            'name': 'Nouvelle Playlist',
            'description': 'Description de test',
            'cover_image': (image[0], image[1])
        }

        # Faire la requête
        response = self.client.post(
            '/api/playlists',
            data=data,
            content_type='multipart/form-data'
        )
        self.assertEqual(response.status_code, 201)

        # Vérifier les données
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Nouvelle Playlist')
        self.assertEqual(data['description'], 'Description de test')
        self.assertIsNotNone(data['cover_image'])

    def test_update_playlist(self):
        """Test la mise à jour d'une playlist"""
        # Créer une playlist
        playlist = Playlist(
            name='Test Playlist',
            description='Old description',
            user_id=self.user.id
        )
        self.session.add(playlist)
        self.session.commit()

        # Données de mise à jour
        data = {
            'name': 'Updated Playlist',
            'description': 'New description'
        }

        # Faire la requête
        response = self.client.put(
            f'/api/playlists/{playlist.id}',
            data=data
        )
        self.assertEqual(response.status_code, 200)

        # Vérifier les données
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'Updated Playlist')
        self.assertEqual(data['description'], 'New description')

    def test_delete_playlist(self):
        """Test la suppression d'une playlist"""
        # Créer une playlist
        playlist = Playlist(
            name='Test Playlist',
            user_id=self.user.id
        )
        self.session.add(playlist)
        self.session.commit()

        # Faire la requête
        response = self.client.delete(f'/api/playlists/{playlist.id}')
        self.assertEqual(response.status_code, 204)

        # Vérifier que la playlist n'existe plus
        playlist = self.session.query(Playlist).get(playlist.id)
        self.assertIsNone(playlist)

    def test_playlist_tracks(self):
        """Test la gestion des pistes dans une playlist"""
        # Créer une playlist et des pistes
        playlist = Playlist(name='Test Playlist', user_id=self.user.id)
        tracks = [
            Track(title=f'Track {i}', duration=180)
            for i in range(3)
        ]
        self.session.add(playlist)
        self.session.add_all(tracks)
        self.session.commit()

        # Ajouter une piste
        response = self.client.post(
            f'/api/playlists/{playlist.id}/tracks',
            json={'track_id': tracks[0].id}
        )
        self.assertEqual(response.status_code, 200)

        # Vérifier les pistes
        response = self.client.get(f'/api/playlists/{playlist.id}/tracks')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Track 0')

        # Réorganiser les pistes
        response = self.client.post(
            f'/api/playlists/{playlist.id}/tracks/reorder',
            json={
                'track_id': tracks[0].id,
                'position': 1
            }
        )
        self.assertEqual(response.status_code, 200)

        # Supprimer une piste
        response = self.client.delete(
            f'/api/playlists/{playlist.id}/tracks/{tracks[0].id}'
        )
        self.assertEqual(response.status_code, 204)

    def test_unauthorized_access(self):
        """Test l'accès non autorisé"""
        # Déconnecter l'utilisateur
        with self.client.session_transaction() as session:
            session.clear()

        # Essayer d'accéder aux playlists
        response = self.client.get('/api/playlists')
        self.assertEqual(response.status_code, 401)

    def test_playlist_not_found(self):
        """Test l'accès à une playlist inexistante"""
        response = self.client.get('/api/playlists/999')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
