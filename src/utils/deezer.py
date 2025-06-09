"""
Client pour l'API Deezer.
Gère les requêtes vers l'API Deezer.
"""

from typing import Dict, Any, List, Optional
from aiohttp import ClientSession, ClientTimeout
from .exceptions import ServiceError

class DeezerClient:
    """Client pour l'API Deezer avec gestion des requêtes."""
    
    def __init__(self):
        # Configuration
        self.base_url = 'https://api.deezer.com'
        self.timeout = ClientTimeout(total=10)
        
        # Session HTTP
        self.session: Optional[ClientSession] = None
    
    async def __aenter__(self):
        """Initialise la session HTTP."""
        if not self.session:
            self.session = ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ferme la session HTTP."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def is_configured(self) -> bool:
        """Vérifie si le client est configuré."""
        return True  # Pas besoin d'authentification pour l'API publique
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Recherche de pistes sur Deezer."""
        try:
            # Préparer la requête
            params = {
                'q': query,
                'limit': min(limit, 50)  # Maximum 50 résultats
            }
            
            # Faire la requête
            async with ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search/track",
                    params=params,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise ServiceError(f"\u00c9chec de la recherche: {error}")
                    
                    data = await response.json()
                    tracks = data['data']
                    
                    # Formater les résultats
                    return [{
                        'id': str(track['id']),
                        'title': track['title'],
                        'artist': track['artist']['name'],
                        'duration': track['duration'],
                        'url': track['link'],
                        'preview_url': track['preview'],
                        'thumbnail': track['album']['cover_big'],
                        'source': 'deezer',
                        'score': track.get('rank', 0) / 1000000.0  # Score basé sur le rang
                    } for track in tracks]
                
        except Exception as e:
            raise ServiceError(f"Erreur de recherche: {str(e)}")
    
    async def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Récupère les informations d'une playlist."""
        try:
            # Récupérer les infos de la playlist
            async with ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/playlist/{playlist_id}",
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise ServiceError(
                            f"\u00c9chec de la récupération de la playlist: {error}"
                        )
                    
                    playlist = await response.json()
                    
                    # Formater les résultats
                    return {
                        'id': str(playlist['id']),
                        'title': playlist['title'],
                        'description': playlist.get('description', ''),
                        'thumbnail': playlist['picture_big'],
                        'source': 'deezer',
                        'url': playlist['link'],
                        'track_count': playlist['nb_tracks'],
                        'tracks': [{
                            'id': str(track['id']),
                            'title': track['title'],
                            'artist': track['artist']['name'],
                            'duration': track['duration'],
                            'url': track['link'],
                            'preview_url': track['preview'],
                            'thumbnail': track['album']['cover_big'],
                            'source': 'deezer',
                            'position': i
                        } for i, track in enumerate(playlist['tracks']['data'])]
                }
                
        except Exception as e:
            raise ServiceError(f"Erreur de récupération de playlist: {str(e)}")

# Fonctions de compatibilité
async def search_deezer(query: str) -> List[Dict[str, Any]]:
    """Recherche de pistes sur Deezer."""
    async with DeezerClient() as client:
        return await client.search(query)

async def get_deezer_playlist(playlist_id: str) -> Dict[str, Any]:
    """Récupère les informations d'une playlist Deezer."""
    async with DeezerClient() as client:
        return await client.get_playlist(playlist_id)
