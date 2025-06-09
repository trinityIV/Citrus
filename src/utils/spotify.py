"""
Utilitaires pour l'API Spotify
"""
import os
import time
import base64
from typing import Dict, Any, List, Optional, Tuple
import aiohttp
from aiohttp import ClientTimeout
from .exceptions import ServiceError, AuthenticationError

class SpotifyClient:
    """Client pour l'API Spotify avec gestion du token et des requêtes."""
    
    def __init__(self):
        # Configuration
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.base_url = 'https://api.spotify.com/v1'
        self.auth_url = 'https://accounts.spotify.com/api/token'
        
        # Token d'accès
        self.access_token: Optional[str] = None
        self.token_type: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        
        # Session HTTP
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = ClientTimeout(total=10)
        
        # Vérifier la configuration
        if not self.client_id or not self.client_secret:
            raise AuthenticationError("Les identifiants Spotify ne sont pas configurés")
    
    async def __aenter__(self):
        """Initialise la session HTTP."""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ferme la session HTTP."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def is_configured(self) -> bool:
        """Vérifie si le client est configuré."""
        return bool(self.client_id and self.client_secret)
    
    async def get_access_token(self) -> Tuple[str, str]:
        """Obtient un token d'accès via l'authentification client credentials."""
        try:
            # Vérifier si le token est encore valide
            if (
                self.access_token
                and self.token_type
                and self.token_expires_at
                and time.time() < self.token_expires_at - 60
            ):
                return self.access_token, self.token_type
            
            # Préparer l'authentification
            auth = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            
            headers = {
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {'grant_type': 'client_credentials'}
            
            # Faire la requête
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.auth_url,
                    headers=headers,
                    data=data,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise AuthenticationError(
                            f"\u00c9chec de l'authentification Spotify: {error}"
                        )
                    
                    token_info = await response.json()
                    
                    # Sauvegarder le token
                    self.access_token = token_info['access_token']
                    self.token_type = token_info['token_type']
                    self.token_expires_at = time.time() + token_info['expires_in']
                    
                    return self.access_token, self.token_type
                    
        except Exception as e:
            raise AuthenticationError(f"Erreur d'authentification: {str(e)}")
    
    async def get_headers(self) -> Dict[str, str]:
        """Retourne les en-têtes pour les requêtes API."""
        token, token_type = await self.get_access_token()
        return {
            'Authorization': f'{token_type} {token}',
            'Content-Type': 'application/json'
        }
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Recherche de pistes sur Spotify."""
        try:
            # Préparer la requête
            params = {
                'q': query,
                'type': 'track',
                'limit': min(limit, 50)  # Maximum 50 résultats
            }
            
            headers = await self.get_headers()
            
            # Faire la requête
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search",
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise ServiceError(f"\u00c9chec de la recherche: {error}")
                    
                    data = await response.json()
                    tracks = data['tracks']['items']
                    
                    # Formater les résultats
                    return [{
                        'id': track['id'],
                        'title': track['name'],
                        'artist': track['artists'][0]['name'],
                        'duration': int(track['duration_ms'] / 1000),
                        'url': track['external_urls']['spotify'],
                        'preview_url': track['preview_url'],
                        'thumbnail': (
                            track['album']['images'][0]['url']
                            if track['album']['images']
                            else None
                        ),
                        'source': 'spotify',
                        'score': track['popularity'] / 100.0
                    } for track in tracks]
                    
        except Exception as e:
            raise ServiceError(f"Erreur de recherche: {str(e)}")
    
    async def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Récupère les informations d'une playlist."""
        try:
            headers = await self.get_headers()
            
            # Récupérer les infos de la playlist
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/playlists/{playlist_id}",
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise ServiceError(
                            f"\u00c9chec de la récupération de la playlist: {error}"
                        )
                    
                    playlist = await response.json()
            
            # Récupérer toutes les pistes
            tracks = []
            next_url = playlist['tracks']['href']
            
            while next_url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        next_url,
                        headers=headers,
                        timeout=self.timeout
                    ) as response:
                        if response.status != 200:
                            break
                        
                        track_data = await response.json()
                        tracks.extend(track_data['items'])
                        next_url = track_data.get('next')
            
            # Formater les résultats
            return {
                'id': playlist['id'],
                'title': playlist['name'],
                'description': playlist['description'],
                'thumbnail': (
                    playlist['images'][0]['url']
                    if playlist['images']
                    else None
                ),
                'source': 'spotify',
                'url': playlist['external_urls']['spotify'],
                'track_count': playlist['tracks']['total'],
                'tracks': [{
                    'id': item['track']['id'],
                    'title': item['track']['name'],
                    'artist': item['track']['artists'][0]['name'],
                    'duration': int(item['track']['duration_ms'] / 1000),
                    'url': item['track']['external_urls']['spotify'],
                    'preview_url': item['track']['preview_url'],
                    'thumbnail': (
                        item['track']['album']['images'][0]['url']
                        if item['track']['album']['images']
                        else None
                    ),
                    'source': 'spotify'
                } for item in tracks if item['track']]
            }
            
        except Exception as e:
            raise ServiceError(f"Erreur de récupération de playlist: {str(e)}")

_client: Optional[SpotifyClient] = None

def get_spotify_client() -> SpotifyClient:
    """
    Retourne une instance unique du client Spotify
    """
    global _client
    if not _client:
        _client = SpotifyClient()
    return _client
