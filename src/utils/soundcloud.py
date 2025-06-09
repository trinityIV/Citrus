"""
Utilitaires pour l'API SoundCloud
"""
import yt_dlp
from typing import Dict, Any

# Helper pour récupérer les infos d'une piste ou playlist SoundCloud via yt-dlp (scrapping)
def get_soundcloud_info(url: str) -> Dict[str, Any]:
    """Récupère les informations d'une piste ou playlist SoundCloud via yt-dlp."""
    ydl_opts = {'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


        # Configuration
        self.client_id = os.getenv('SOUNDCLOUD_CLIENT_ID')
        self.base_url = 'https://api.soundcloud.com'
        self.timeout = ClientTimeout(total=10)
        
        # Session HTTP
        self.session: Optional[ClientSession] = None
        
        # Vérifier la configuration
        if not self.client_id:
            raise ValidationError("Client ID SoundCloud non configuré")
    
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
        return bool(self.client_id)
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Recherche de pistes sur SoundCloud."""
        try:
            # Préparer la requête
            params = {
                'q': query,
                'client_id': self.client_id,
                'limit': min(limit, 50)  # Maximum 50 résultats
            }
            
            # Faire la requête
            async with ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/tracks",
                    params=params,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise ServiceError(f"\u00c9chec de la recherche: {error}")
                    
                    tracks = await response.json()
                    
                    # Formater les résultats
                    return [{
                        'id': str(track['id']),
                        'title': track['title'],
                        'artist': track['user']['username'],
                        'duration': int(track['duration'] / 1000),  # ms -> s
                        'url': track['permalink_url'],
                        'preview_url': f"{track['stream_url']}?client_id={self.client_id}",
                        'thumbnail': (
                            track['artwork_url'].replace('large', 't500x500')
                            if track['artwork_url']
                            else None
                        ),
                        'source': 'soundcloud',
                        'score': track.get('playback_count', 0) / 100000.0  # Score basé sur les écoutes
                    } for track in tracks]
                    
        except Exception as e:
            raise ServiceError(f"Erreur de recherche: {str(e)}")
    
    async def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Récupère les informations d'une playlist."""
        try:
            # Récupérer les infos de la playlist
            async with ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/playlists/{playlist_id}",
                    params={'client_id': self.client_id},
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
                        'thumbnail': (
                            playlist['artwork_url'].replace('large', 't500x500')
                            if playlist['artwork_url']
                            else None
                        ),
                        'source': 'soundcloud',
                        'url': playlist['permalink_url'],
                        'track_count': len(playlist['tracks']),
                        'tracks': [{
                            'id': str(track['id']),
                            'title': track['title'],
                            'artist': track['user']['username'],
                            'duration': int(track['duration'] / 1000),
                            'url': track['permalink_url'],
                            'preview_url': f"{track['stream_url']}?client_id={self.client_id}",
                            'thumbnail': (
                                track['artwork_url'].replace('large', 't500x500')
                                if track['artwork_url']
                                else None
                            ),
                            'source': 'soundcloud',
                            'position': i
                        } for i, track in enumerate(playlist['tracks'])]
                    }
                    
        except Exception as e:
            raise ServiceError(f"Erreur de récupération de playlist: {str(e)}")

# Fonctions de compatibilité
async def search_soundcloud(query: str) -> List[Dict[str, Any]]:
    """Recherche de pistes sur SoundCloud."""
    async with SoundCloudClient() as client:
        return await client.search(query)

async def get_soundcloud_playlist(playlist_id: str) -> Dict[str, Any]:
    """Récupère les informations d'une playlist SoundCloud."""
    async with SoundCloudClient() as client:
        return await client.get_playlist(playlist_id)
