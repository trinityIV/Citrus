"""
Tests unitaires pour les modèles
"""

import unittest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.user import User
from src.models.playlist import Playlist, playlist_tracks
from src.models.track import Track
from src.database import Base

class TestModels(unittest.TestCase):
    """Tests pour les modèles de données"""

    def setUp(self):
        """Initialisation avant chaque test"""
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

    def tearDown(self):
        """Nettoyage après chaque test"""
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_user_creation(self):
        """Test la création d'un utilisateur"""
        user = self.session.query(User).filter_by(username='test_user').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.check_password('wrongpassword'))

    def test_user_to_dict(self):
        """Test la conversion d'un utilisateur en dictionnaire"""
        user = self.session.query(User).first()
        user_dict = user.to_dict()
        self.assertEqual(user_dict['username'], 'test_user')
        self.assertEqual(user_dict['email'], 'test@example.com')
        self.assertIn('created_at', user_dict)

    def test_playlist_creation(self):
        """Test la création d'une playlist"""
        playlist = Playlist(
            name='Test Playlist',
            description='Une playlist de test',
            user_id=self.user.id
        )
        playlist.session = self.session
        self.session.add(playlist)
        self.session.commit()

        # Vérifier la playlist
        saved_playlist = self.session.query(Playlist).first()
        self.assertEqual(saved_playlist.name, 'Test Playlist')
        self.assertEqual(saved_playlist.description, 'Une playlist de test')
        self.assertEqual(saved_playlist.user_id, self.user.id)
        self.assertEqual(saved_playlist.track_count, 0)

    def test_playlist_tracks(self):
        """Test l'ajout et la suppression de pistes dans une playlist"""
        # Créer une playlist
        playlist = Playlist(
            name='Test Playlist',
            description='Une playlist de test',
            user_id=self.user.id
        )
        playlist.session = self.session
        self.session.add(playlist)

        # Créer quelques pistes
        track1 = Track(
            title='Track 1',
            artist='Artist 1',
            duration=180
        )
        track2 = Track(
            title='Track 2',
            artist='Artist 2',
            duration=240
        )
        self.session.add_all([track1, track2])
        self.session.commit()

        # Ajouter les pistes à la playlist
        playlist.add_track(track1)
        playlist.add_track(track2)
        self.session.commit()

        # Vérifier les pistes
        self.assertEqual(playlist.track_count, 2)
        self.assertEqual(playlist.total_duration, 420)
        self.assertEqual(playlist.get_track_position(track1), 1)
        self.assertEqual(playlist.get_track_position(track2), 2)

        # Supprimer une piste
        playlist.remove_track(track1)
        self.session.commit()

        # Vérifier après suppression
        self.assertEqual(playlist.track_count, 1)
        self.assertEqual(playlist.total_duration, 240)
        self.assertEqual(playlist.get_track_position(track2), 1)

    def test_playlist_to_dict(self):
        """Test la conversion d'une playlist en dictionnaire"""
        playlist = Playlist(
            name='Test Playlist',
            description='Une playlist de test',
            user_id=self.user.id
        )
        playlist.session = self.session
        self.session.add(playlist)
        self.session.commit()

        playlist_dict = playlist.to_dict()
        self.assertEqual(playlist_dict['name'], 'Test Playlist')
        self.assertEqual(playlist_dict['description'], 'Une playlist de test')
        self.assertEqual(playlist_dict['track_count'], 0)
        self.assertEqual(playlist_dict['total_duration'], 0)
        self.assertIn('created_at', playlist_dict)
        self.assertIn('updated_at', playlist_dict)

    def test_playlist_reordering(self):
        """Test la réorganisation des pistes dans une playlist"""
        # Créer une playlist avec trois pistes
        playlist = Playlist(
            name='Test Playlist',
            user_id=self.user.id
        )
        playlist.session = self.session
        self.session.add(playlist)

        tracks = [
            Track(title=f'Track {i}', duration=180)
            for i in range(1, 4)
        ]
        self.session.add_all(tracks)
        self.session.commit()

        # Ajouter les pistes dans l'ordre
        for track in tracks:
            playlist.add_track(track)
        self.session.commit()

        # Vérifier l'ordre initial
        positions = [playlist.get_track_position(track) for track in tracks]
        self.assertEqual(positions, [1, 2, 3])

        # Déplacer une piste
        playlist.set_track_position(tracks[2], 1)
        self.session.commit()

        # Vérifier le nouvel ordre
        positions = [playlist.get_track_position(track) for track in tracks]
        self.assertEqual(playlist.get_track_position(tracks[2]), 1)
        self.assertTrue(all(pos > 1 for pos in positions[:2]))

if __name__ == '__main__':
    unittest.main()
