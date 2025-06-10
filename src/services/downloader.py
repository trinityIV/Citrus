import os
import json
import uuid
import logging
import threading
import yt_dlp
from pathlib import Path
from typing import Dict, Optional, List, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

@dataclass
class DownloadTask:
    id: str
    url: str
    service: str
    status: str = 'pending'  # pending, downloading, converting, completed, failed
    progress: float = 0.0
    filename: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self):
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat() if self.start_time else None
        result['end_time'] = self.end_time.isoformat() if self.end_time else None
        return result

class DownloadManager:
    def __init__(self, download_dir: Path):
        self.download_dir = download_dir
        self.tasks: Dict[str, DownloadTask] = {}
        self.lock = threading.Lock()
        self.active_threads: List[threading.Thread] = []
        
        # Créer le répertoire de téléchargement s'il n'existe pas
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)
        
        # yt-dlp options avec configuration améliorée
        self.ydl_opts = {
            # Format audio
            'format': 'bestaudio/best',
            'outtmpl': str(download_dir / '%(title)s.%(ext)s'),
            
            # Extraction audio
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            
            # Métadonnées
            'writethumbnail': True,
            'writeinfojson': True,
            'embedthumbnail': True,
            'addmetadata': True,
            
            # Hooks et configuration
            'progress_hooks': [self._progress_hook],
            'logger': logger,
            'quiet': False,
            'no_warnings': False,
            
            # Timeouts et réessais
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            
            # Autres options
            'noplaylist': False,  # Permettre les playlists
            'ignoreerrors': True,  # Continuer en cas d'erreur
        }
    
    def _progress_hook(self, d):
        """Hook pour suivre la progression du téléchargement"""
        # Essayer d'obtenir l'ID de la tâche de différentes façons selon la version de yt-dlp
        task_id = None
        if 'info_dict' in d and isinstance(d['info_dict'], dict):
            task_id = d['info_dict'].get('id')
        elif 'id' in d:
            task_id = d['id']
            
        if not task_id:
            logger.warning(f"Impossible d'identifier la tâche pour la progression: {d.get('filename', 'unknown')}")
            return
            
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return
                
            # Vérifier si la tâche a été annulée
            if task.status == 'cancelled':
                return
                
            if d['status'] == 'downloading':
                task.status = 'downloading'
                
                # Calculer la progression
                if 'total_bytes' in d and d['total_bytes'] > 0:
                    task.progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                    task.progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                
                # Ajouter des informations de progression détaillées
                if 'speed' in d and d['speed'] is not None:
                    speed_mb = d['speed'] / 1024 / 1024  # Convertir en MB/s
                    task.error = f"Téléchargement en cours: {speed_mb:.2f} MB/s"
                    
            elif d['status'] == 'finished':
                task.status = 'converting'
                task.progress = 100
                task.error = "Conversion audio en cours..."
                
            elif d['status'] == 'error':
                task.status = 'failed'
                task.error = str(d.get('error', 'Erreur inconnue'))
                task.end_time = datetime.now()
    
    def add_download(self, url: str, service: str = 'youtube') -> str:
        """Ajoute une nouvelle tâche de téléchargement"""
        # Générer un ID unique pour la tâche
        task_id = str(uuid.uuid4())[:8]
        
        # Créer la tâche
        task = DownloadTask(
            id=task_id,
            url=url,
            service=service,
            start_time=datetime.now(UTC)
        )
        
        # Enregistrer la tâche
        with self.lock:
            self.tasks[task_id] = task
        
        # Nettoyer les threads terminés
        self._cleanup_threads()
        
        # Démarrer le téléchargement dans un thread séparé
        thread = threading.Thread(target=self._download, args=(task_id, url, service))
        thread.daemon = True
        thread.start()
        
        # Garder une référence au thread
        with self.lock:
            self.active_threads.append(thread)
        
        return task_id
        
    def _cleanup_threads(self):
        """Nettoie les threads terminés de la liste"""
        with self.lock:
            # Filtrer les threads qui sont encore en vie
            self.active_threads = [t for t in self.active_threads if t.is_alive()]
            
            # Limiter le nombre de tâches conservées en mémoire
            if len(self.tasks) > 100:
                # Garder uniquement les 50 tâches les plus récentes
                sorted_tasks = sorted(
                    self.tasks.items(),
                    key=lambda x: x[1].start_time if x[1].start_time else datetime.min,
                    reverse=True
                )
                self.tasks = dict(sorted_tasks[:50])
    
    def _download(self, task_id: str, url: str, service: str):
        """Fonction interne pour gérer le téléchargement"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return
            
            task.status = 'downloading'
            task.start_time = datetime.now()
        
        try:
            # Configuration spécifique au service
            ydl_opts = self.ydl_opts.copy()
            
            if service == 'spotify':
                # Pour Spotify, on utilise yt-dlp avec le plugin spotify
                ydl_opts['extract_flat'] = True
                ydl_opts['force_generic_extractor'] = True
            
            # Ajouter un timeout pour éviter les blocages
            ydl_opts['socket_timeout'] = 30
            
            # Exécuter le téléchargement
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Vérifier si la tâche a été annulée avant de commencer
                with self.lock:
                    if self.tasks.get(task_id).status == 'cancelled':
                        return
                
                try:
                    info = ydl.extract_info(url, download=True)
                    
                    with self.lock:
                        task = self.tasks.get(task_id)
                        if task and task.status != 'cancelled':
                            # Vérifier si info est un dictionnaire ou une liste (playlist)
                            if isinstance(info, dict):
                                task.filename = ydl.prepare_filename(info)
                            elif isinstance(info, list) and info:
                                task.filename = f"Playlist: {len(info)} tracks"
                            
                            task.status = 'completed'
                            task.progress = 100
                            task.end_time = datetime.now()
                except yt_dlp.utils.DownloadError as e:
                    logger.error(f'Erreur yt-dlp: {str(e)}')
                    with self.lock:
                        task = self.tasks.get(task_id)
                        if task:
                            task.status = 'failed'
                            task.error = f'Erreur de téléchargement: {str(e)}'
                            task.end_time = datetime.now()
                    
        except Exception as e:
            logger.error(f'Erreur lors du téléchargement: {str(e)}')
            with self.lock:
                task = self.tasks.get(task_id)
                if task:
                    task.status = 'failed'
                    task.error = f'Erreur inattendue: {str(e)}'
                    task.end_time = datetime.now()
    
    def get_status(self, task_id: str) -> Optional[dict]:
        """Récupère l'état d'une tâche"""
        with self.lock:
            task = self.tasks.get(task_id)
            return task.to_dict() if task else None
    
    def get_all_tasks(self) -> list:
        """Récupère toutes les tâches"""
        with self.lock:
            return [task.to_dict() for task in self.tasks.values()]
            
    def cancel_task(self, task_id: str) -> bool:
        """Annule un téléchargement en cours"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
                
            if task.status in ['pending', 'downloading', 'converting']:
                task.status = 'cancelled'
                task.error = 'Téléchargement annulé par l\'utilisateur'
                task.end_time = datetime.now()
                return True
            
            return False
            
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """Récupère une tâche par son ID"""
        with self.lock:
            return self.tasks.get(task_id)
