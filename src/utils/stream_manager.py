"""
Gestionnaire de streams (IPTV et Torrents)
"""

import m3u8
import requests
import libtorrent as lt
from pathlib import Path
from urllib.parse import urlparse
import threading
import json
from flask import current_app
import logging

class StreamManager:
    def __init__(self):
        self.active_streams = {}
        self.torrent_sessions = {}
        self.logger = logging.getLogger(__name__)

    def add_iptv_stream(self, url, name=None):
        """
        Ajoute un stream IPTV (M3U/M3U8)
        """
        try:
            # Vérifier si c'est une playlist M3U/M3U8
            response = requests.get(url)
            if 'm3u' in response.headers.get('content-type', '').lower():
                playlist = m3u8.loads(response.text)
                streams = []
                
                for segment in playlist.segments:
                    streams.append({
                        'url': segment.uri,
                        'duration': segment.duration,
                        'title': segment.title or name or urlparse(url).path.split('/')[-1]
                    })
                
                stream_id = len(self.active_streams)
                self.active_streams[stream_id] = {
                    'type': 'iptv',
                    'url': url,
                    'name': name,
                    'streams': streams,
                    'status': 'ready'
                }
                return stream_id
            else:
                # Stream direct
                stream_id = len(self.active_streams)
                self.active_streams[stream_id] = {
                    'type': 'iptv',
                    'url': url,
                    'name': name or urlparse(url).path.split('/')[-1],
                    'status': 'ready'
                }
                return stream_id
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout du stream IPTV: {str(e)}")
            raise

    def add_torrent_stream(self, magnet_or_file, save_path=None):
        """
        Ajoute un stream torrent
        """
        try:
            session = lt.session()
            session.listen_port(6881, 6891)
            session.start_dht()
            
            # Configurer les paramètres du torrent
            params = {
                'save_path': save_path or str(Path.home() / 'Downloads'),
                'storage_mode': lt.storage_mode_t.storage_mode_sparse
            }

            if magnet_or_file.startswith('magnet:'):
                handle = lt.add_magnet_uri(session, magnet_or_file, params)
            else:
                info = lt.torrent_info(magnet_or_file)
                handle = session.add_torrent({'ti': info, **params})

            # Démarrer le téléchargement en streaming
            stream_id = len(self.active_streams)
            self.active_streams[stream_id] = {
                'type': 'torrent',
                'handle': handle,
                'session': session,
                'status': 'downloading',
                'progress': 0
            }
            
            # Démarrer un thread pour suivre la progression
            threading.Thread(
                target=self._monitor_torrent_progress,
                args=(stream_id,),
                daemon=True
            ).start()
            
            return stream_id
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout du torrent: {str(e)}")
            raise

    def _monitor_torrent_progress(self, stream_id):
        """
        Surveille la progression du téléchargement torrent
        """
        stream = self.active_streams.get(stream_id)
        if not stream or stream['type'] != 'torrent':
            return

        handle = stream['handle']
        while handle.status().progress < 1:
            status = handle.status()
            self.active_streams[stream_id].update({
                'progress': status.progress * 100,
                'download_rate': status.download_rate,
                'upload_rate': status.upload_rate,
                'num_peers': status.num_peers
            })
            if status.progress >= 1:
                self.active_streams[stream_id]['status'] = 'completed'
            threading.Event().wait(1.0)

    def get_stream_status(self, stream_id):
        """
        Récupère le statut d'un stream
        """
        stream = self.active_streams.get(stream_id)
        if not stream:
            return None
            
        status = {
            'id': stream_id,
            'type': stream['type'],
            'status': stream['status']
        }
        
        if stream['type'] == 'torrent':
            handle = stream['handle']
            torrent_status = handle.status()
            status.update({
                'progress': torrent_status.progress * 100,
                'download_rate': torrent_status.download_rate,
                'upload_rate': torrent_status.upload_rate,
                'num_peers': torrent_status.num_peers
            })
            
        return status

    def stop_stream(self, stream_id):
        """
        Arrête un stream
        """
        stream = self.active_streams.get(stream_id)
        if not stream:
            return False
            
        try:
            if stream['type'] == 'torrent':
                session = stream['session']
                handle = stream['handle']
                session.remove_torrent(handle)
                
            del self.active_streams[stream_id]
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'arrêt du stream: {str(e)}")
            return False

# Instance globale du gestionnaire de streams
stream_manager = StreamManager()
