"""
Service de gestion des téléchargements.
Gère les téléchargements individuels et en lot avec file d'attente et priorités.
"""

import os
import asyncio
import aiohttp
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel

from utils.exceptions import DownloadError, ValidationError
from utils.spotify import SpotifyClient
from utils.youtube import YouTubeClient
from utils.soundcloud import SoundCloudClient
from utils.deezer import DeezerClient

class DownloadStatus(BaseModel):
    id: str
    url: str
    source: str
    title: str
    artist: Optional[str]
    status: str  # pending, downloading, completed, error, cancelled
    progress: float
    error: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    file_path: Optional[str]
    playlist_id: Optional[str]
    playlist_title: Optional[str]

class BatchStatus(BaseModel):
    id: str
    tracks: List[DownloadStatus]
    total_tracks: int
    completed_tracks: int
    failed_tracks: int
    cancelled_tracks: int
    status: str  # pending, processing, completed, cancelled
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    playlist_id: Optional[str]
    playlist_title: Optional[str]

class DownloadManager:
    def __init__(self):
        self.downloads: Dict[str, DownloadStatus] = {}
        self.batches: Dict[str, BatchStatus] = {}
        self.queue = asyncio.Queue()
        self.batch_queue = asyncio.Queue()
        self.max_concurrent = 3
        self.active_downloads = 0
        self.download_lock = asyncio.Lock()
        
        # Clients pour les différentes plateformes
        self.spotify = SpotifyClient()
        self.youtube = YouTubeClient()
        self.soundcloud = SoundCloudClient()
        self.deezer = DeezerClient()
        
        # Démarrer les workers
        asyncio.create_task(self._process_queue())
        asyncio.create_task(self._process_batch_queue())
    
    async def add_to_queue(self, track: dict) -> str:
        """
        Ajoute un téléchargement à la file d'attente.
        """
        download_id = str(uuid.uuid4())
        
        status = DownloadStatus(
            id=download_id,
            url=track["url"],
            source=track["source"],
            title=track["title"],
            artist=track.get("artist"),
            status="pending",
            progress=0.0,
            error=None,
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            file_path=None,
            playlist_id=track.get("playlist_id"),
            playlist_title=track.get("playlist_title")
        )
        
        self.downloads[download_id] = status
        await self.queue.put(download_id)
        
        return download_id
    
    async def create_batch(
        self,
        tracks: List[dict],
        playlist_id: Optional[str] = None,
        playlist_title: Optional[str] = None
    ) -> str:
        """
        Crée un nouveau lot de téléchargements.
        """
        batch_id = str(uuid.uuid4())
        
        # Créer les téléchargements individuels
        download_ids = []
        for track in tracks:
            track["playlist_id"] = playlist_id
            track["playlist_title"] = playlist_title
            download_id = await self.add_to_queue(track)
            download_ids.append(download_id)
        
        # Créer le statut du lot
        batch_status = BatchStatus(
            id=batch_id,
            tracks=[self.downloads[did] for did in download_ids],
            total_tracks=len(tracks),
            completed_tracks=0,
            failed_tracks=0,
            cancelled_tracks=0,
            status="pending",
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            playlist_id=playlist_id,
            playlist_title=playlist_title
        )
        
        self.batches[batch_id] = batch_status
        await self.batch_queue.put(batch_id)
        
        return batch_id
    
    async def get_status(self, download_id: str) -> dict:
        """
        Récupère le statut d'un téléchargement.
        """
        if download_id not in self.downloads:
            raise ValidationError(f"Téléchargement {download_id} non trouvé")
            
        return self.downloads[download_id].dict()
    
    async def get_batch_status(self, batch_id: str) -> dict:
        """
        Récupère le statut d'un lot de téléchargements.
        """
        if batch_id not in self.batches:
            raise ValidationError(f"Lot {batch_id} non trouvé")
            
        return self.batches[batch_id].dict()
    
    async def cancel_download(self, download_id: str):
        """
        Annule un téléchargement.
        """
        if download_id not in self.downloads:
            raise ValidationError(f"Téléchargement {download_id} non trouvé")
            
        status = self.downloads[download_id]
        if status.status in ["completed", "error", "cancelled"]:
            return
            
        status.status = "cancelled"
        status.completed_at = datetime.now()
    
    async def cancel_batch(self, batch_id: str):
        """
        Annule un lot de téléchargements.
        """
        if batch_id not in self.batches:
            raise ValidationError(f"Lot {batch_id} non trouvé")
            
        batch = self.batches[batch_id]
        if batch.status in ["completed", "cancelled"]:
            return
            
        batch.status = "cancelled"
        batch.completed_at = datetime.now()
        
        # Annuler tous les téléchargements en attente
        for track in batch.tracks:
            if track.status == "pending":
                await self.cancel_download(track.id)
    
    async def _process_queue(self):
        """
        Traite la file d'attente des téléchargements.
        """
        while True:
            try:
                # Attendre qu'il y ait de la place
                async with self.download_lock:
                    if self.active_downloads >= self.max_concurrent:
                        await asyncio.sleep(1)
                        continue
                    
                    self.active_downloads += 1
                
                # Récupérer le prochain téléchargement
                download_id = await self.queue.get()
                status = self.downloads[download_id]
                
                # Vérifier si le téléchargement n'a pas été annulé
                if status.status == "cancelled":
                    self.queue.task_done()
                    continue
                
                # Mettre à jour le statut
                status.status = "downloading"
                status.started_at = datetime.now()
                
                try:
                    # Télécharger selon la source
                    if status.source == "spotify":
                        await self._download_spotify(status)
                    elif status.source == "youtube":
                        await self._download_youtube(status)
                    elif status.source == "soundcloud":
                        await self._download_soundcloud(status)
                    elif status.source == "deezer":
                        await self._download_deezer(status)
                    else:
                        raise DownloadError(f"Source non supportée: {status.source}")
                    
                    # Marquer comme terminé
                    status.status = "completed"
                    status.progress = 100.0
                    status.completed_at = datetime.now()
                    
                except Exception as e:
                    status.status = "error"
                    status.error = str(e)
                    status.completed_at = datetime.now()
                
                finally:
                    # Libérer un slot
                    async with self.download_lock:
                        self.active_downloads -= 1
                    
                    self.queue.task_done()
                
            except Exception as e:
                print(f"Erreur dans le worker de téléchargement: {e}")
                await asyncio.sleep(1)
    
    async def _process_batch_queue(self):
        """
        Traite la file d'attente des lots.
        """
        while True:
            try:
                # Récupérer le prochain lot
                batch_id = await self.batch_queue.get()
                batch = self.batches[batch_id]
                
                # Vérifier si le lot n'a pas été annulé
                if batch.status == "cancelled":
                    self.batch_queue.task_done()
                    continue
                
                # Mettre à jour le statut
                batch.status = "processing"
                batch.started_at = datetime.now()
                
                try:
                    # Attendre que tous les téléchargements soient terminés
                    while True:
                        # Compter les téléchargements terminés
                        completed = 0
                        failed = 0
                        cancelled = 0
                        
                        for track in batch.tracks:
                            if track.status == "completed":
                                completed += 1
                            elif track.status == "error":
                                failed += 1
                            elif track.status == "cancelled":
                                cancelled += 1
                        
                        # Mettre à jour les compteurs
                        batch.completed_tracks = completed
                        batch.failed_tracks = failed
                        batch.cancelled_tracks = cancelled
                        
                        # Vérifier si tout est terminé
                        total_done = completed + failed + cancelled
                        if total_done == batch.total_tracks:
                            break
                        
                        await asyncio.sleep(1)
                    
                    # Marquer comme terminé
                    batch.status = "completed"
                    batch.completed_at = datetime.now()
                    
                except Exception as e:
                    print(f"Erreur dans le traitement du lot: {e}")
                
                finally:
                    self.batch_queue.task_done()
                
            except Exception as e:
                print(f"Erreur dans le worker de lots: {e}")
                await asyncio.sleep(1)
    
    async def _download_spotify(self, status: DownloadStatus):
        """
        Télécharge une piste Spotify.
        """
        try:
            # Obtenir l'URL de téléchargement
            download_url = await self.spotify.get_download_url(status.url)
            
            # Télécharger le fichier
            await self._download_file(download_url, status)
            
        except Exception as e:
            raise DownloadError(f"Erreur Spotify: {str(e)}")
    
    async def _download_youtube(self, status: DownloadStatus):
        """
        Télécharge une vidéo YouTube.
        """
        try:
            # Obtenir l'URL de téléchargement
            download_url = await self.youtube.get_download_url(status.url)
            
            # Télécharger le fichier
            await self._download_file(download_url, status)
            
        except Exception as e:
            raise DownloadError(f"Erreur YouTube: {str(e)}")
    
    async def _download_soundcloud(self, status: DownloadStatus):
        """
        Télécharge une piste SoundCloud.
        """
        try:
            # Obtenir l'URL de téléchargement
            download_url = await self.soundcloud.get_download_url(status.url)
            
            # Télécharger le fichier
            await self._download_file(download_url, status)
            
        except Exception as e:
            raise DownloadError(f"Erreur SoundCloud: {str(e)}")
    
    async def _download_deezer(self, status: DownloadStatus):
        """
        Télécharge une piste Deezer.
        """
        try:
            # Obtenir l'URL de téléchargement
            download_url = await self.deezer.get_download_url(status.url)
            
            # Télécharger le fichier
            await self._download_file(download_url, status)
            
        except Exception as e:
            raise DownloadError(f"Erreur Deezer: {str(e)}")
    
    async def _download_file(self, url: str, status: DownloadStatus):
        """
        Télécharge un fichier avec suivi de progression.
        """
        try:
            # Créer le dossier de destination
            os.makedirs("downloads", exist_ok=True)
            
            # Générer le nom du fichier
            filename = f"{status.title} - {status.artist or 'Unknown'}.mp3"
            filename = "".join(c for c in filename if c.isalnum() or c in "- ")
            filepath = os.path.join("downloads", filename)
            
            # Télécharger le fichier
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise DownloadError(
                            f"Erreur HTTP {response.status}: {response.reason}"
                        )
                    
                    # Obtenir la taille totale
                    total_size = int(response.headers.get("content-length", 0))
                    
                    # Écrire le fichier
                    with open(filepath, "wb") as f:
                        downloaded = 0
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                status.progress = (downloaded / total_size) * 100
            
            # Mettre à jour le chemin du fichier
            status.file_path = filepath
            
        except Exception as e:
            raise DownloadError(f"Erreur de téléchargement: {str(e)}")
