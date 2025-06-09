import os
import json
import logging
import threading
import yt_dlp
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

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
        
        # Configuration yt-dlp
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(download_dir / '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'writethumbnail': True,
            'progress_hooks': [self._progress_hook],
            'logger': logger,
        }
    
    def _progress_hook(self, d):
        """Hook pour suivre la progression du téléchargement"""
        task_id = d.get('info_dict', {}).get('id')
        if not task_id:
            return
            
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return
                
            if d['status'] == 'downloading':
                task.status = 'downloading'
                if 'total_bytes' in d:
                    task.progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif d['status'] == 'finished':
                task.status = 'converting'
                task.progress = 100
            elif d['status'] == 'error':
                task.status = 'failed'
                task.error = str(d.get('error', 'Unknown error'))
                task.end_time = datetime.now()
    
    def add_download(self, url: str, service: str = 'youtube') -> str:
        """Ajoute une nouvelle tâche de téléchargement"""
        task_id = str(len(self.tasks) + 1)
        task = DownloadTask(
            id=task_id,
            url=url,
            service=service,
            start_time=datetime.now()
        )
        
        with self.lock:
            self.tasks[task_id] = task
        
        # Démarrer le téléchargement dans un thread séparé
        thread = threading.Thread(target=self._download, args=(task_id, url, service))
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _download(self, task_id: str, url: str, service: str):
        """Fonction interne pour gérer le téléchargement"""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return
            
            task.status = 'downloading'
        
        try:
            # Configuration spécifique au service
            ydl_opts = self.ydl_opts.copy()
            
            if service == 'spotify':
                # Pour Spotify, on utilise yt-dlp avec le plugin spotify
                ydl_opts['extract_flat'] = True
                ydl_opts['force_generic_extractor'] = True
            
            # Exécuter le téléchargement
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                with self.lock:
                    task.filename = ydl.prepare_filename(info)
                    task.status = 'completed'
                    task.progress = 100
                    task.end_time = datetime.now()
                    
        except Exception as e:
            logger.error(f'Erreur lors du téléchargement: {str(e)}')
            with self.lock:
                task.status = 'failed'
                task.error = str(e)
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
