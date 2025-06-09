"""
Gestionnaire de traitement média (conversion, sous-titres, etc.)
"""

import ffmpeg
import pysrt
import schedule
from pathlib import Path
import threading
import queue
import json
from datetime import datetime, timedelta
import psutil
import logging
from typing import Optional, Dict, List

class MediaProcessor:
    def __init__(self):
        self.conversion_queue = queue.Queue()
        self.active_conversions = {}
        self.bandwidth_limit = None  # en KB/s
        self.scheduler = schedule.Scheduler()
        self.logger = logging.getLogger(__name__)
        
        # Démarrer le thread de conversion
        self.conversion_thread = threading.Thread(target=self._process_conversion_queue, daemon=True)
        self.conversion_thread.start()
        
        # Démarrer le thread du scheduler
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def convert_media(self, input_path: str, output_format: str, 
                     subtitle_path: Optional[str] = None,
                     quality: str = 'high',
                     schedule_time: Optional[datetime] = None) -> str:
        """
        Convertit un fichier média vers le format spécifié
        """
        try:
            output_path = str(Path(input_path).with_suffix(f'.{output_format}'))
            
            # Paramètres de qualité
            quality_presets = {
                'low': {'video_bitrate': '1000k', 'audio_bitrate': '128k'},
                'medium': {'video_bitrate': '2500k', 'audio_bitrate': '192k'},
                'high': {'video_bitrate': '5000k', 'audio_bitrate': '320k'}
            }
            
            conversion_params = {
                'input_path': input_path,
                'output_path': output_path,
                'format': output_format,
                'subtitle_path': subtitle_path,
                'quality': quality_presets[quality],
                'status': 'pending'
            }

            if schedule_time:
                # Programmer la conversion
                self.scheduler.every().day.at(schedule_time.strftime('%H:%M')).do(
                    self.conversion_queue.put, conversion_params
                )
                return f"Conversion programmée pour {schedule_time}"
            else:
                # Conversion immédiate
                self.conversion_queue.put(conversion_params)
                return output_path

        except Exception as e:
            self.logger.error(f"Erreur de conversion: {str(e)}")
            raise

    def _process_conversion_queue(self):
        """
        Traite la file d'attente des conversions
        """
        while True:
            try:
                params = self.conversion_queue.get()
                conversion_id = str(len(self.active_conversions))
                self.active_conversions[conversion_id] = params
                
                stream = ffmpeg.input(params['input_path'])
                
                # Appliquer les paramètres de qualité
                stream = ffmpeg.output(stream, params['output_path'],
                    **params['quality'],
                    f=params['format']
                )
                
                # Ajouter les sous-titres si présents
                if params['subtitle_path']:
                    stream = ffmpeg.filter(stream, 'subtitles', params['subtitle_path'])
                
                # Appliquer la limite de bande passante si définie
                if self.bandwidth_limit:
                    stream = ffmpeg.filter(stream, 'throttle', 
                        rate=str(self.bandwidth_limit * 1024))
                
                # Lancer la conversion
                self.active_conversions[conversion_id]['status'] = 'converting'
                ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
                self.active_conversions[conversion_id]['status'] = 'completed'
                
            except Exception as e:
                self.logger.error(f"Erreur pendant la conversion: {str(e)}")
                if conversion_id in self.active_conversions:
                    self.active_conversions[conversion_id]['status'] = 'failed'
                    self.active_conversions[conversion_id]['error'] = str(e)
            
            finally:
                self.conversion_queue.task_done()

    def _run_scheduler(self):
        """
        Exécute le planificateur de tâches
        """
        while True:
            self.scheduler.run_pending()
            threading.Event().wait(1)

    def get_conversion_status(self, conversion_id: str) -> Dict:
        """
        Récupère le statut d'une conversion
        """
        if conversion_id not in self.active_conversions:
            return {'error': 'Conversion non trouvée'}
            
        conversion = self.active_conversions[conversion_id]
        status = {
            'status': conversion['status'],
            'input': conversion['input_path'],
            'output': conversion['output_path'],
            'format': conversion['format']
        }
        
        if conversion['status'] == 'converting':
            # Calculer la progression
            try:
                output_file = Path(conversion['output_path'])
                if output_file.exists():
                    progress = (output_file.stat().st_size / 
                              Path(conversion['input_path']).stat().st_size * 100)
                    status['progress'] = min(progress, 99.9)
                else:
                    status['progress'] = 0
            except:
                status['progress'] = 0
                
        elif conversion['status'] == 'failed':
            status['error'] = conversion.get('error', 'Erreur inconnue')
            
        return status

    def set_bandwidth_limit(self, limit_kb: int):
        """
        Définit une limite de bande passante en KB/s
        """
        self.bandwidth_limit = limit_kb

    def get_system_stats(self) -> Dict:
        """
        Récupère les statistiques système
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'disk_usage': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            },
            'bandwidth_limit': self.bandwidth_limit
        }

# Instance globale du processeur média
media_processor = MediaProcessor()
