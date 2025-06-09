"""
Service de gestion des playlists.
Gère la récupération et la manipulation des playlists de différentes plateformes.
"""

import asyncio
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, parse_qs
from pydantic import BaseModel

from utils.spotify import SpotifyClient
from utils.youtube import YouTubeClient
from utils.soundcloud import SoundCloudClient
from utils.deezer import DeezerClient
from utils.exceptions import ServiceError, ValidationError

class PlaylistTrack(BaseModel):
    id: str
    title: str
    artist: str
    duration: int
    thumbnail: Optional[str]
    preview_url: Optional[str]
    source: str
    url: str
    position: int

class Playlist(BaseModel):
    id: str
    title: str
    description: Optional[str]
    thumbnail: Optional[str]
    source: str
    url: str
    track_count: int
    tracks: List[PlaylistTrack]

class PlaylistService:
    def __init__(self):
        # Initialiser les clients
        self.spotify = SpotifyClient()
        self.youtube = YouTubeClient()
        self.soundcloud = SoundCloudClient()
        self.deezer = DeezerClient()
        
        # Cache des playlists (TTL: 5 minutes)
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # secondes
    
    async def get_playlist_info(self, url: str) -> Dict[str, Any]:
        """
        Récupère les informations d'une playlist.
        
        Args:
            url: URL de la playlist
            
        Returns:
            Informations de la playlist
        """
        try:
            # Valider l'URL
            if not url or not url.startswith('http'):
                raise ValidationError("URL invalide")
            
            # Vérifier le cache
            if url in self.cache:
                return self.cache[url]
            
            # Déterminer le service et l'ID
            service = self._get_service_from_url(url)
            playlist_id = self._get_playlist_id(url, service)
            
            # Récupérer les informations
            if service == 'spotify':
                playlist = await self._get_spotify_playlist(playlist_id)
            elif service == 'youtube':
                playlist = await self._get_youtube_playlist(playlist_id)
            elif service == 'soundcloud':
                playlist = await self._get_soundcloud_playlist(playlist_id)
            elif service == 'deezer':
                playlist = await self._get_deezer_playlist(playlist_id)
            else:
                raise ServiceError("Service non supporté")
            
            # Mettre en cache
            self.cache[url] = playlist.dict()
            
            return playlist.dict()
            
        except ValidationError as e:
            raise e
        except ServiceError as e:
            raise e
        except Exception as e:
            raise ServiceError(f"Erreur lors de la récupération de la playlist: {str(e)}")
    
    def _get_service_from_url(self, url: str) -> str:
        """
        Détermine le service à partir de l'URL.
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            if 'spotify.com' in domain:
                return 'spotify'
            elif 'youtube.com' in domain or 'youtu.be' in domain:
                return 'youtube'
            elif 'soundcloud.com' in domain:
                return 'soundcloud'
            elif 'deezer.com' in domain:
                return 'deezer'
            else:
                raise ServiceError('Service non supporté')
                
        except Exception as e:
            raise ValidationError(f"URL invalide: {str(e)}")
    
    def _get_playlist_id(self, url: str, service: str) -> str:
        """
        Extrait l'ID de la playlist de l'URL.
        """
        try:
            parsed = urlparse(url)
            
            if service == 'spotify':
                # Format: https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
                parts = parsed.path.split('/')
                if len(parts) >= 3 and parts[1] == 'playlist':
                    return parts[2]
            
            elif service == 'youtube':
                # Format: https://www.youtube.com/playlist?list=PLH6pfBXQXHEC2uDmDy5oi3tHW6X8kZ2Jo
                params = parse_qs(parsed.query)
                if 'list' in params:
                    return params['list'][0]
            
            elif service == 'soundcloud':
                # Format: https://soundcloud.com/user/sets/playlist-name
                parts = parsed.path.split('/')
                if len(parts) >= 4 and parts[2] == 'sets':
                    return parts[3]
            
            elif service == 'deezer':
                # Format: https://www.deezer.com/playlist/1234567890
                parts = parsed.path.split('/')
                if len(parts) >= 3 and parts[1] == 'playlist':
                    return parts[2]
            
            raise ValidationError('Format de playlist invalide')
            
        except Exception as e:
            raise ValidationError(f"URL invalide: {str(e)}")
    
    async def _get_spotify_playlist(self, playlist_id: str) -> Playlist:
        """
        Récupère une playlist Spotify.
        """
        try:
            data = await self.spotify.get_playlist(playlist_id)
            
            tracks = [
                PlaylistTrack(
                    id=track['track']['id'],
                    title=track['track']['name'],
                    artist=track['track']['artists'][0]['name'],
                    duration=track['track']['duration_ms'] // 1000,
                    thumbnail=track['track']['album']['images'][0]['url'],
                    preview_url=track['track']['preview_url'],
                    source='spotify',
                    url=track['track']['external_urls']['spotify'],
                    position=i
                )
                for i, track in enumerate(data['tracks']['items'])
            ]
            
            return Playlist(
                id=data['id'],
                title=data['name'],
                description=data['description'],
                thumbnail=data['images'][0]['url'] if data['images'] else None,
                source='spotify',
                url=data['external_urls']['spotify'],
                track_count=data['tracks']['total'],
                tracks=tracks
            )
            
        except Exception as e:
            raise ServiceError(f"Erreur Spotify: {str(e)}")
    
    async def _get_youtube_playlist(self, playlist_id: str) -> Playlist:
        """
        Récupère une playlist YouTube.
        """
        try:
            data = await self.youtube.get_playlist(playlist_id)
            
            tracks = [
                PlaylistTrack(
                    id=video['id'],
                    title=video['title'],
                    artist=video['channel'],
                    duration=video['duration'],
                    thumbnail=video['thumbnail'],
                    preview_url=None,
                    source='youtube',
                    url=f"https://youtube.com/watch?v={video['id']}",
                    position=i
                )
                for i, video in enumerate(data['videos'])
            ]
            
            return Playlist(
                id=data['id'],
                title=data['title'],
                description=data['description'],
                thumbnail=data['thumbnail'],
                source='youtube',
                url=f"https://youtube.com/playlist?list={data['id']}",
                track_count=len(tracks),
                tracks=tracks
            )
            
        except Exception as e:
            raise ServiceError(f"Erreur YouTube: {str(e)}")
    
    async def _get_soundcloud_playlist(self, playlist_id: str) -> Playlist:
        """
        Récupère une playlist SoundCloud.
        """
        try:
            data = await self.soundcloud.get_playlist(playlist_id)
            
            tracks = [
                PlaylistTrack(
                    id=str(track['id']),
                    title=track['title'],
                    artist=track['user']['username'],
                    duration=track['duration'] // 1000,
                    thumbnail=track['artwork_url'],
                    preview_url=track['preview_url'],
                    source='soundcloud',
                    url=track['permalink_url'],
                    position=i
                )
                for i, track in enumerate(data['tracks'])
            ]
            
            return Playlist(
                id=str(data['id']),
                title=data['title'],
                description=data.get('description'),
                thumbnail=data.get('artwork_url'),
                source='soundcloud',
                url=data['permalink_url'],
                track_count=len(tracks),
                tracks=tracks
            )
            
        except Exception as e:
            raise ServiceError(f"Erreur SoundCloud: {str(e)}")
    
    async def _get_deezer_playlist(self, playlist_id: str) -> Playlist:
        """
        Récupère une playlist Deezer.
        """
        try:
            data = await self.deezer.get_playlist(playlist_id)
            
            tracks = [
                PlaylistTrack(
                    id=str(track['id']),
                    title=track['title'],
                    artist=track['artist']['name'],
                    duration=track['duration'],
                    thumbnail=track['album']['cover_xl'],
                    preview_url=track['preview'],
                    source='deezer',
                    url=track['link'],
                    position=i
                )
                for i, track in enumerate(data['tracks']['data'])
            ]
            
            return Playlist(
                id=str(data['id']),
                title=data['title'],
                description=None,
                thumbnail=data['picture_xl'],
                source='deezer',
                url=data['link'],
                track_count=data['nb_tracks'],
                tracks=tracks
            )
            
        except Exception as e:
            raise ServiceError(f"Erreur Deezer: {str(e)}")
