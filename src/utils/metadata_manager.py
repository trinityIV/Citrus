"""
Gestionnaire de métadonnées et de playlists
"""

import eyed3
from mutagen import File
from pathlib import Path
import json
import shutil
from typing import Dict, List, Optional
import logging
from datetime import datetime

class MetadataManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.playlists_path = Path("data/playlists")
        self.playlists_path.mkdir(parents=True, exist_ok=True)

    def edit_metadata(self, file_path: str, metadata: Dict) -> bool:
        """
        Édite les métadonnées d'un fichier audio
        """
        try:
            ext = Path(file_path).suffix.lower()
            
            if ext in ['.mp3']:
                audiofile = eyed3.load(file_path)
                if audiofile is None:
                    return False
                
                # Mettre à jour les tags
                if 'title' in metadata:
                    audiofile.tag.title = metadata['title']
                if 'artist' in metadata:
                    audiofile.tag.artist = metadata['artist']
                if 'album' in metadata:
                    audiofile.tag.album = metadata['album']
                if 'genre' in metadata:
                    audiofile.tag.genre = metadata['genre']
                if 'year' in metadata:
                    audiofile.tag.year = metadata['year']
                if 'track_num' in metadata:
                    audiofile.tag.track_num = metadata['track_num']
                if 'lyrics' in metadata:
                    audiofile.tag.lyrics.set(metadata['lyrics'])
                
                # Sauvegarder l'image de couverture
                if 'cover' in metadata:
                    with open(metadata['cover'], 'rb') as img_file:
                        img_data = img_file.read()
                        audiofile.tag.images.set(3, img_data, "image/jpeg")
                
                audiofile.tag.save()
                
            else:
                # Utiliser mutagen pour les autres formats
                audio = File(file_path)
                if audio is None:
                    return False
                
                for key, value in metadata.items():
                    if key in audio:
                        audio[key] = value
                
                audio.save()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'édition des métadonnées: {str(e)}")
            return False

    def extract_metadata(self, file_path: str) -> Dict:
        """
        Extrait les métadonnées d'un fichier audio
        """
        try:
            ext = Path(file_path).suffix.lower()
            metadata = {}
            
            if ext in ['.mp3']:
                audiofile = eyed3.load(file_path)
                if audiofile and audiofile.tag:
                    metadata = {
                        'title': audiofile.tag.title,
                        'artist': audiofile.tag.artist,
                        'album': audiofile.tag.album,
                        'genre': str(audiofile.tag.genre),
                        'year': audiofile.tag.year,
                        'track_num': audiofile.tag.track_num,
                        'duration': audiofile.info.time_secs,
                        'bitrate': audiofile.info.bit_rate[1],
                        'sample_rate': audiofile.info.sample_freq
                    }
                    
                    # Extraire les paroles
                    if audiofile.tag.lyrics:
                        metadata['lyrics'] = audiofile.tag.lyrics[0].text
                    
                    # Extraire la couverture
                    if audiofile.tag.images:
                        cover = audiofile.tag.images[0]
                        cover_path = Path(file_path).parent / f"{Path(file_path).stem}_cover.jpg"
                        with open(cover_path, 'wb') as img_file:
                            img_file.write(cover.image_data)
                        metadata['cover'] = str(cover_path)
            
            else:
                # Utiliser mutagen pour les autres formats
                audio = File(file_path)
                if audio:
                    metadata = dict(audio.tags)
                    metadata['duration'] = audio.info.length
                    if hasattr(audio.info, 'bitrate'):
                        metadata['bitrate'] = audio.info.bitrate
                    if hasattr(audio.info, 'sample_rate'):
                        metadata['sample_rate'] = audio.info.sample_rate
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction des métadonnées: {str(e)}")
            return {}

    def create_playlist(self, name: str, description: str = "") -> str:
        """
        Crée une nouvelle playlist
        """
        try:
            playlist_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            playlist_file = self.playlists_path / f"{playlist_id}.json"
            
            playlist_data = {
                'id': playlist_id,
                'name': name,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'tracks': []
            }
            
            with open(playlist_file, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, indent=2)
            
            return playlist_id
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de la playlist: {str(e)}")
            raise

    def add_to_playlist(self, playlist_id: str, tracks: List[Dict]) -> bool:
        """
        Ajoute des pistes à une playlist
        """
        try:
            playlist_file = self.playlists_path / f"{playlist_id}.json"
            if not playlist_file.exists():
                return False
            
            with open(playlist_file, 'r+', encoding='utf-8') as f:
                playlist = json.load(f)
                playlist['tracks'].extend(tracks)
                playlist['updated_at'] = datetime.now().isoformat()
                
                f.seek(0)
                json.dump(playlist, f, indent=2)
                f.truncate()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout à la playlist: {str(e)}")
            return False

    def get_playlist(self, playlist_id: str) -> Optional[Dict]:
        """
        Récupère les informations d'une playlist
        """
        try:
            playlist_file = self.playlists_path / f"{playlist_id}.json"
            if not playlist_file.exists():
                return None
            
            with open(playlist_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture de la playlist: {str(e)}")
            return None

    def list_playlists(self) -> List[Dict]:
        """
        Liste toutes les playlists disponibles
        """
        playlists = []
        for playlist_file in self.playlists_path.glob("*.json"):
            try:
                with open(playlist_file, 'r', encoding='utf-8') as f:
                    playlist = json.load(f)
                    playlists.append({
                        'id': playlist['id'],
                        'name': playlist['name'],
                        'description': playlist['description'],
                        'track_count': len(playlist['tracks']),
                        'updated_at': playlist['updated_at']
                    })
            except Exception as e:
                self.logger.error(f"Erreur lors de la lecture de {playlist_file}: {str(e)}")
                continue
        
        return sorted(playlists, key=lambda x: x['updated_at'], reverse=True)

# Instance globale du gestionnaire de métadonnées
metadata_manager = MetadataManager()
