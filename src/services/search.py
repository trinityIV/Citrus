"""
Service de recherche multi-plateformes.
Gère la recherche asynchrone sur plusieurs plateformes de musique.
"""

import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from utils.spotify import SpotifyClient
from utils.youtube import YouTubeClient
from utils.soundcloud import SoundCloudClient
from utils.deezer import DeezerClient
from utils.exceptions import ServiceError, ValidationError

class SearchResult(BaseModel):
    id: str
    title: str
    artist: str
    duration: int
    thumbnail: Optional[str]
    preview_url: Optional[str]
    source: str
    url: str
    score: float

class SearchService:
    def __init__(self):
        # Initialiser les clients
        self.spotify = SpotifyClient()
        self.youtube = YouTubeClient()
        self.soundcloud = SoundCloudClient()
        self.deezer = DeezerClient()
        
        # Cache des résultats (TTL: 5 minutes)
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # secondes
    
    async def search(
        self,
        query: str,
        limit: int = 20,
        sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recherche sur toutes les plateformes configurées.
        
        Args:
            query: Terme de recherche
            limit: Nombre maximum de résultats (défaut: 20)
            sources: Liste des plateformes à utiliser (défaut: toutes)
            
        Returns:
            Liste des résultats de recherche
        """
        try:
            # Valider la requête
            if not query or len(query.strip()) < 2:
                raise ValidationError("La requête doit contenir au moins 2 caractères")
            
            # Normaliser la requête
            query = query.strip().lower()
            
            # Vérifier le cache
            cache_key = f"{query}:{limit}:{','.join(sources or [])}".lower()
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Déterminer les sources à utiliser
            available_sources = {
                'spotify': self.spotify.is_configured(),
                'youtube': self.youtube.is_configured(),
                'soundcloud': self.soundcloud.is_configured(),
                'deezer': self.deezer.is_configured()
            }
            
            if sources:
                # Filtrer les sources demandées
                search_sources = {
                    s: available_sources[s]
                    for s in sources
                    if s in available_sources
                }
            else:
                # Utiliser toutes les sources disponibles
                search_sources = available_sources
            
            # Créer les tâches de recherche
            tasks = []
            for source, enabled in search_sources.items():
                if not enabled:
                    continue
                    
                if source == 'spotify':
                    tasks.append(self._search_spotify(query))
                elif source == 'youtube':
                    tasks.append(self._search_youtube(query))
                elif source == 'soundcloud':
                    tasks.append(self._search_soundcloud(query))
                elif source == 'deezer':
                    tasks.append(self._search_deezer(query))
            
            # Exécuter les recherches en parallèle
            results = []
            async with asyncio.TaskGroup() as group:
                for task in tasks:
                    results.extend(await task)
            
            # Trier et filtrer les résultats
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:limit]
            
            # Mettre en cache
            self.cache[cache_key] = results
            
            return results
            
        except* asyncio.CancelledError:
            raise ServiceError("La recherche a été annulée")
        except* Exception as e:
            raise ServiceError(f"Erreur de recherche: {str(e)}")
    
    async def _search_spotify(self, query: str) -> List[SearchResult]:
        """
        Recherche sur Spotify.
        """
        try:
            tracks = await self.spotify.search(query)
            return [
                SearchResult(
                    id=track['id'],
                    title=track['name'],
                    artist=track['artists'][0]['name'],
                    duration=track['duration_ms'] // 1000,
                    thumbnail=track['album']['images'][0]['url'],
                    preview_url=track['preview_url'],
                    source='spotify',
                    url=track['external_urls']['spotify'],
                    score=track['popularity'] / 100.0
                )
                for track in tracks
            ]
        except Exception as e:
            print(f"Erreur Spotify: {e}")
            return []
    
    async def _search_youtube(self, query: str) -> List[SearchResult]:
        """
        Recherche sur YouTube.
        """
        try:
            videos = await self.youtube.search(query)
            return [
                SearchResult(
                    id=video['id'],
                    title=video['title'],
                    artist=video['channel'],
                    duration=video['duration'],
                    thumbnail=video['thumbnail'],
                    preview_url=None,
                    source='youtube',
                    url=f"https://youtube.com/watch?v={video['id']}",
                    score=video['relevance_score']
                )
                for video in videos
            ]
        except Exception as e:
            print(f"Erreur YouTube: {e}")
            return []
    
    async def _search_soundcloud(self, query: str) -> List[SearchResult]:
        """
        Recherche sur SoundCloud.
        """
        try:
            tracks = await self.soundcloud.search(query)
            return [
                SearchResult(
                    id=str(track['id']),
                    title=track['title'],
                    artist=track['user']['username'],
                    duration=track['duration'] // 1000,
                    thumbnail=track['artwork_url'],
                    preview_url=track['preview_url'],
                    source='soundcloud',
                    url=track['permalink_url'],
                    score=track['playback_count'] / 1000000.0
                )
                for track in tracks
            ]
        except Exception as e:
            print(f"Erreur SoundCloud: {e}")
            return []
    
    async def _search_deezer(self, query: str) -> List[SearchResult]:
        """
        Recherche sur Deezer.
        """
        try:
            tracks = await self.deezer.search(query)
            return [
                SearchResult(
                    id=str(track['id']),
                    title=track['title'],
                    artist=track['artist']['name'],
                    duration=track['duration'],
                    thumbnail=track['album']['cover_xl'],
                    preview_url=track['preview'],
                    source='deezer',
                    url=track['link'],
                    score=track['rank'] / 1000000.0
                )
                for track in tracks
            ]
        except Exception as e:
            print(f"Erreur Deezer: {e}")
            return []
