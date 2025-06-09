"""
Utilitaires pour l'API YouTube
"""
import yt_dlp
from typing import Dict, Any

# Helper pour récupérer les infos d'une vidéo ou playlist YouTube via yt-dlp (scrapping)
def get_youtube_info(url: str) -> Dict[str, Any]:
    """Récupère les informations d'une vidéo ou playlist YouTube via yt-dlp."""
    ydl_opts = {'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)
        # Vérifier la configuration
        if not self.api_key:
            raise ValidationError("Clé API YouTube non configurée")
    
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
        return bool(self.api_key)
    
    async def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Recherche de vidéos sur YouTube."""
        try:
            # Préparer la requête
            params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'videoCategoryId': '10',  # Musique
                'maxResults': min(limit, 50),  # Maximum 50 résultats
                'key': self.api_key
            }
            
            # Faire la requête
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search",
                    params=params,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise ServiceError(f"\u00c9chec de la recherche: {error}")
                    
                    data = await response.json()
                    videos = data['items']
                    
                    # Récupérer les durées des vidéos
                    video_ids = [video['id']['videoId'] for video in videos]
                    durations = await self._get_video_durations(video_ids)
                    
                    # Formater les résultats
                    return [{
                        'id': video['id']['videoId'],
                        'title': video['snippet']['title'],
                        'artist': video['snippet']['channelTitle'],
                        'duration': durations.get(video['id']['videoId'], 0),
                        'url': f"https://www.youtube.com/watch?v={video['id']['videoId']}",
                        'thumbnail': video['snippet']['thumbnails']['high']['url'],
                        'source': 'youtube',
                        'score': 0.8  # Score de pertinence arbitraire
                    } for video in videos]
                    
        except Exception as e:
            raise ServiceError(f"Erreur de recherche: {str(e)}")
    
    async def _get_video_durations(self, video_ids: List[str]) -> Dict[str, int]:
        """Récupère la durée des vidéos YouTube."""
        if not video_ids:
            return {}
        
        try:
            # Préparer la requête
            params = {
                'part': 'contentDetails',
                'id': ','.join(video_ids),
                'key': self.api_key
            }
            
            # Faire la requête
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/videos",
                    params=params,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        return {}
                    
                    data = await response.json()
                    durations = {}
                    
                    for item in data['items']:
                        duration = item['contentDetails']['duration']
                        seconds = self._parse_duration(duration)
                        durations[item['id']] = seconds
                    
                    return durations
                    
        except Exception:
            return {}
    
    def _parse_duration(self, duration: str) -> int:
        """Convertit une durée ISO 8601 en secondes."""
        try:
            # Supprimer le "P" du début
            duration = duration[1:]
            
            # Convertir en secondes
            hours = minutes = seconds = 0
            
            # Trouver les heures
            match = re.search(r'(\d+)H', duration)
            if match:
                hours = int(match.group(1))
            
            # Trouver les minutes
            match = re.search(r'(\d+)M', duration)
            if match:
                minutes = int(match.group(1))
            
            # Trouver les secondes
            match = re.search(r'(\d+)S', duration)
            if match:
                seconds = int(match.group(1))
            
            return hours * 3600 + minutes * 60 + seconds
            
        except Exception:
            return 0
    
    async def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Récupère les informations d'une playlist."""
        try:
            # Récupérer les infos de la playlist
            params = {
                'part': 'snippet',
                'id': playlist_id,
                'key': self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/playlists",
                    params=params,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise ServiceError(
                            f"\u00c9chec de la récupération de la playlist: {error}"
                        )
                    
                    data = await response.json()
                    if not data['items']:
                        raise ServiceError("Playlist introuvable")
                    
                    playlist = data['items'][0]
                    
                    # Récupérer les vidéos de la playlist
                    tracks = []
                    next_page_token = None
                    
                    while True:
                        params = {
                            'part': 'snippet',
                            'playlistId': playlist_id,
                            'maxResults': 50,
                            'key': self.api_key
                        }
                        
                        if next_page_token:
                            params['pageToken'] = next_page_token
                        
                        async with session.get(
                            f"{self.base_url}/playlistItems",
                            params=params,
                            timeout=self.timeout
                        ) as response:
                            if response.status != 200:
                                break
                            
                            items_data = await response.json()
                            video_ids = [
                                item['snippet']['resourceId']['videoId']
                                for item in items_data['items']
                            ]
                            
                            # Récupérer les durées des vidéos
                            durations = await self._get_video_durations(video_ids)
                            
                            # Ajouter les vidéos à la liste
                            for i, item in enumerate(items_data['items']):
                                video = item['snippet']
                                video_id = video['resourceId']['videoId']
                                
                                tracks.append({
                                    'id': video_id,
                                    'title': video['title'],
                                    'artist': video['videoOwnerChannelTitle'],
                                    'duration': durations.get(video_id, 0),
                                    'url': f"https://www.youtube.com/watch?v={video_id}",
                                    'thumbnail': video['thumbnails']['high']['url'],
                                    'source': 'youtube',
                                    'position': i
                                })
                            
                            next_page_token = items_data.get('nextPageToken')
                            if not next_page_token:
                                break
                    
                    # Formater les résultats
                    return {
                        'id': playlist['id'],
                        'title': playlist['snippet']['title'],
                        'description': playlist['snippet']['description'],
                        'thumbnail': playlist['snippet']['thumbnails']['high']['url'],
                        'source': 'youtube',
                        'url': f"https://www.youtube.com/playlist?list={playlist['id']}",
                        'track_count': len(tracks),
                        'tracks': tracks
                    }
                    
        except Exception as e:
            raise ServiceError(f"Erreur de récupération de playlist: {str(e)}")

async def search_youtube(query: str) -> List[Dict[str, Any]]:
    """
    Recherche de vidéos sur YouTube
    """
    async with YouTubeClient() as client:
        return await client.search(query)

async def get_youtube_playlist(playlist_id: str) -> Dict[str, Any]:
    """
    Récupère les informations d'une playlist YouTube
    """
    async with YouTubeClient() as client:
        return await client.get_playlist(playlist_id)
