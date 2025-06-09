"""
Service d'intégration avec Spotify
"""

import base64
import json
import requests
from flask import current_app
from urllib.parse import urlencode

class SpotifyService:
    """Service pour interagir avec l'API Spotify"""
    
    def __init__(self):
        self.client_id = current_app.config['SPOTIFY_CLIENT_ID']
        self.client_secret = current_app.config['SPOTIFY_CLIENT_SECRET']
        self.redirect_uri = current_app.config['SPOTIFY_REDIRECT_URI']
        self.auth_url = 'https://accounts.spotify.com/authorize'
        self.token_url = 'https://accounts.spotify.com/api/token'
        self.api_base_url = 'https://api.spotify.com/v1'
        
    def get_auth_url(self, state=None):
        """Génère l'URL d'authentification Spotify"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': 'user-library-read playlist-read-private streaming',
        }
        
        if state:
            params['state'] = state
            
        return f"{self.auth_url}?{urlencode(params)}"
    
    def get_access_token(self, code):
        """Échange le code d'autorisation contre un token d'accès"""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(self.token_url, headers=headers, data=data)
        return response.json()
    
    def refresh_token(self, refresh_token):
        """Rafraîchit le token d'accès"""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        response = requests.post(self.token_url, headers=headers, data=data)
        return response.json()
    
    def search(self, query, type='track', limit=20, offset=0):
        """Recherche sur Spotify"""
        headers = {
            'Authorization': f'Bearer {self._get_access_token()}'
        }
        
        params = {
            'q': query,
            'type': type,
            'limit': limit,
            'offset': offset
        }
        
        response = requests.get(
            f"{self.api_base_url}/search",
            headers=headers,
            params=params
        )
        return response.json()
    
    def get_track(self, track_id):
        """Récupère les détails d'une piste"""
        headers = {
            'Authorization': f'Bearer {self._get_access_token()}'
        }
        
        response = requests.get(
            f"{self.api_base_url}/tracks/{track_id}",
            headers=headers
        )
        return response.json()
    
    def get_audio_features(self, track_id):
        """Récupère les caractéristiques audio d'une piste"""
        headers = {
            'Authorization': f'Bearer {self._get_access_token()}'
        }
        
        response = requests.get(
            f"{self.api_base_url}/audio-features/{track_id}",
            headers=headers
        )
        return response.json()
    
    def _get_access_token(self):
        """Récupère un token d'accès client (sans utilisateur)"""
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {'grant_type': 'client_credentials'}
        
        response = requests.post(self.token_url, headers=headers, data=data)
        return response.json()['access_token']
