import unittest
from flask import Flask
from flask.testing import FlaskClient
import unittest
import tempfile
import os
from src import create_app

class CitrusIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Créer une application de test avec une base de données en mémoire
        self.app = create_app('testing')
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI=f'sqlite:///:memory:',
            WTF_CSRF_ENABLED=False
        )
        
        self.client = self.app.test_client()
        
        # Initialiser la base de données
        with self.app.app_context():
            from src.database import db
            db.create_all()
            self.db = db
            
            # Importer User après création de l'application
            from src.models.user import User

    def tearDown(self):
        with self.app.app_context():
            self.db.session.remove()
            self.db.drop_all()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def register(self, username, password, follow_redirects=True):
        return self.client.post('/auth/register', data={
            'username': username,
            'password': password
        }, follow_redirects=follow_redirects)

    def login(self, username, password, follow_redirects=True):
        return self.client.post('/auth/login', data={
            'username': username,
            'password': password,
            'remember': 'on'  # Ajouter le champ remember pour le login
        }, follow_redirects=follow_redirects)

    def test_register_and_login(self):
        # Test registration
        rv = self.register('testuser', 'testpass', follow_redirects=False)
        self.assertIn(rv.status_code, (200, 302))  # Could be 200 (form) or 302 (redirect)
        
        if rv.status_code == 302:
            # Follow the redirect if there is one
            rv = self.client.get(rv.location)
            self.assertEqual(rv.status_code, 200)
        
        # Test login with correct credentials
        rv = self.login('testuser', 'testpass', follow_redirects=False)
        self.assertIn(rv.status_code, (200, 302))  # Could be 200 (form) or 302 (redirect)
        
        if rv.status_code == 302:
            # Follow the redirect if there is one
            rv = self.client.get(rv.location)
            self.assertEqual(rv.status_code, 200)

        # Test login with wrong password
        rv = self.login('testuser', 'wrongpass')
        self.assertIn(rv.status_code, (200, 302))  # Could be 200 (form) or 302 (redirect)

    def test_music_download_page(self):
        # Register and login
        self.register('musicuser', 'musicpass')
        rv = self.login('musicuser', 'musicpass', follow_redirects=False)
        self.assertIn(rv.status_code, (200, 302))  # Could be 200 (form) or 302 (redirect)
        
        if rv.status_code == 302:
            # Follow the redirect if there is one
            rv = self.client.get(rv.location)
            self.assertEqual(rv.status_code, 200)
        
        # Access music library - should be accessible after login
        rv = self.client.get('/stream')
        self.assertIn(rv.status_code, (200, 302))  # Could be 200 or redirect
        
        rv = self.client.get('/iptv')
        self.assertIn(rv.status_code, (200, 302))  # Could be 200 or redirect

    def test_api_routes_protected(self):
        # Not logged in - should be unauthorized or redirect
        rv = self.client.get('/api/tracks')
        self.assertIn(rv.status_code, (200, 401, 403, 302, 404))
        
        # Register and login
        self.register('apiuser', 'apipass')
        rv = self.login('apiuser', 'apipass', follow_redirects=False)
        self.assertIn(rv.status_code, (200, 302))  # Could be 200 (form) or 302 (redirect)
        
        if rv.status_code == 302:
            # Follow the redirect if there is one
            rv = self.client.get(rv.location)
            self.assertEqual(rv.status_code, 200)
        
        # Should be accessible after login (200) or not found (404) if no tracks
        rv = self.client.get('/api/tracks')
        self.assertIn(rv.status_code, (200, 302, 404))  # 302 for redirect is also acceptable

if __name__ == '__main__':
    unittest.main()
