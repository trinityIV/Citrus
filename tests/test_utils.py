"""
Tests unitaires pour les utilitaires
"""

import unittest
import os
import tempfile
from io import BytesIO
from PIL import Image
from flask import Flask
from werkzeug.datastructures import FileStorage
from src.utils.image import save_image, delete_image, get_image_url
from src.utils.auth import login_required, get_current_user, login_user, logout_user
from src.models.user import User
from src.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestImageUtils(unittest.TestCase):
    """Tests pour les utilitaires de gestion d'images"""

    def setUp(self):
        """Initialisation avant chaque test"""
        # Créer l'application Flask de test
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

        # Créer une image de test
        self.test_image = Image.new('RGB', (100, 100), color='red')
        self.image_file = BytesIO()
        self.test_image.save(self.image_file, 'JPEG')
        self.image_file.seek(0)

    def tearDown(self):
        """Nettoyage après chaque test"""
        import shutil
        shutil.rmtree(self.app.config['UPLOAD_FOLDER'])

    def test_save_image(self):
        """Test la sauvegarde d'une image"""
        with self.app.app_context():
            file = FileStorage(
                stream=self.image_file,
                filename='test.jpg',
                content_type='image/jpeg'
            )

            # Test avec des paramètres valides
            filename = save_image(
                file=file,
                folder='test',
                allowed_extensions={'jpg', 'jpeg'},
                max_size=1024 * 1024,
                max_dimensions=(800, 800)
            )
            self.assertIsNotNone(filename)
            self.assertTrue(filename.endswith('.jpg'))
            self.assertTrue(os.path.exists(
                os.path.join(self.app.config['UPLOAD_FOLDER'], 'test', filename)
            ))

            # Test avec une extension non autorisée
            file.filename = 'test.txt'
            filename = save_image(
                file=file,
                folder='test',
                allowed_extensions={'jpg', 'jpeg'}
            )
            self.assertIsNone(filename)

    def test_delete_image(self):
        """Test la suppression d'une image"""
        with self.app.app_context():
            # Sauvegarder une image
            file = FileStorage(
                stream=self.image_file,
                filename='test.jpg',
                content_type='image/jpeg'
            )
            filename = save_image(file, 'test')

            # Supprimer l'image
            result = delete_image(filename, 'test')
            self.assertTrue(result)
            self.assertFalse(os.path.exists(
                os.path.join(self.app.config['UPLOAD_FOLDER'], 'test', filename)
            ))

            # Tester avec un fichier inexistant
            result = delete_image('nonexistent.jpg', 'test')
            self.assertFalse(result)

    def test_get_image_url(self):
        """Test la génération d'URL d'image"""
        # Test avec un nom de fichier valide
        url = get_image_url('test.jpg', 'playlists')
        self.assertEqual(url, '/uploads/playlists/test.jpg')

        # Test avec un nom de fichier vide
        url = get_image_url('', 'playlists')
        self.assertIsNone(url)

        # Test avec un nom de fichier None
        url = get_image_url(None, 'playlists')
        self.assertIsNone(url)

class TestAuthUtils(unittest.TestCase):
    """Tests pour les utilitaires d'authentification"""

    def setUp(self):
        """Initialisation avant chaque test"""
        # Créer l'application Flask de test
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_key'

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

    def tearDown(self):
        """Nettoyage après chaque test"""
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def test_login_required_decorator(self):
        """Test le décorateur login_required"""
        @self.app.route('/protected')
        @login_required
        def protected_route():
            return 'Protected Content'

        # Test sans authentification
        response = self.client.get('/protected')
        self.assertEqual(response.status_code, 401)

        # Test avec authentification
        with self.client.session_transaction() as session:
            session['user_id'] = self.user.id
        response = self.client.get('/protected')
        self.assertEqual(response.status_code, 200)

    def test_user_session(self):
        """Test les fonctions de gestion de session utilisateur"""
        with self.app.test_request_context():
            # Test login_user
            login_user(self.user)
            self.assertEqual(get_current_user(), self.user)

            # Test is_authenticated
            self.assertTrue('user_id' in self.app.session)

            # Test logout_user
            logout_user()
            self.assertIsNone(get_current_user())
            self.assertNotIn('user_id', self.app.session)

if __name__ == '__main__':
    unittest.main()
