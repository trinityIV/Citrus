import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, TPE1, TIT2, TALB
from PIL import Image
import io

logger = logging.getLogger(__name__)

class MetadataExtractor:
    def __init__(self):
        # Initialiser les balises ID3 supportées
        EasyID3.valid_keys['\xa9alb'] = 'TALB'  # Album
        EasyID3.valid_keys['\xa9ART'] = 'TPE1'  # Artiste
        EasyID3.valid_keys['\xa9nam'] = 'TIT2'  # Titre
        EasyID3.valid_keys['\xa9day'] = 'TDRC'  # Année
        EasyID3.valid_keys['trkn'] = 'TRCK'     # Piste
        
    def extract(self, filepath: Path) -> Dict[str, Any]:
        """Extrait les métadonnées d'un fichier audio"""
        try:
            audio = self._get_audio_metadata(filepath)
            if not audio:
                return {}
                
            metadata = {
                'title': self._get_tag(audio, 'title') or filepath.stem,
                'artist': self._get_tag(audio, 'artist') or 'Artiste inconnu',
                'album': self._get_tag(audio, 'album') or 'Album inconnu',
                'year': self._get_tag(audio, 'date') or '',
                'track': self._get_tag(audio, 'tracknumber') or '0',
                'duration': self._get_duration(audio),
                'bitrate': getattr(audio.info, 'bitrate', 0) // 1000 if hasattr(audio.info, 'bitrate') else 0,
                'sample_rate': getattr(audio.info, 'sample_rate', 0) if hasattr(audio.info, 'sample_rate') else 0,
                'channels': getattr(audio.info, 'channels', 0) if hasattr(audio.info, 'channels') else 0,
            }
            
            # Essayer d'extraire la pochette d'album
            cover = self._extract_cover(audio, filepath)
            if cover:
                metadata['cover_art'] = cover
                
            return metadata
            
        except Exception as e:
            logger.error(f'Erreur lors de l\'extraction des métadonnées pour {filepath}: {str(e)}')
            return {
                'title': filepath.stem,
                'artist': 'Artiste inconnu',
                'album': 'Album inconnu',
                'year': '',
                'track': '0',
                'duration': 0,
                'bitrate': 0,
                'sample_rate': 0,
                'channels': 0,
            }
    
    def _get_audio_metadata(self, filepath: Path):
        """Obtient les métadonnées audio en utilisant mutagen"""
        try:
            return EasyID3(filepath)
        except Exception as e:
            try:
                return mutagen.File(filepath, easy=True)
            except Exception:
                return None
    
    def _get_tag(self, audio, tag_name: str) -> Optional[str]:
        """Récupère une balise spécifique"""
        if not audio:
            return None
            
        try:
            # Essayer différentes clés de balises
            for key in [tag_name, tag_name.upper(), tag_name.lower()]:
                if key in audio:
                    value = audio[key]
                    if isinstance(value, (list, tuple)) and len(value) > 0:
                        return str(value[0])
                    elif value:
                        return str(value)
            return None
        except Exception:
            return None
    
    def _get_duration(self, audio) -> int:
        """Récupère la durée en secondes"""
        if not audio or not hasattr(audio.info, 'length'):
            return 0
        return int(audio.info.length)
    
    def _extract_cover(self, audio, filepath: Path) -> Optional[str]:
        """Extrait et enregistre la pochette d'album"""
        try:
            # Essayer d'abord avec les tags ID3
            if hasattr(audio, 'tags') and 'APIC:' in audio.tags:
                pic = audio.tags['APIC:'].data
                return self._save_cover(pic, filepath)
                
            # Essayer avec les tags mutagens
            if hasattr(audio, 'pictures') and audio.pictures:
                return self._save_cover(audio.pictures[0].data, filepath)
                
            # Essayer avec les fichiers externes
            for ext in ['.jpg', '.jpeg', '.png']:
                cover_path = filepath.with_suffix(ext)
                if cover_path.exists():
                    return f'/static/music/{cover_path.name}'
                    
            return None
            
        except Exception as e:
            logger.warning(f'Impossible d\'extraire la pochette pour {filepath}: {str(e)}')
            return None
    
    def _save_cover(self, image_data: bytes, filepath: Path) -> str:
        """Enregistre la pochette et retourne le chemin relatif"""
        try:
            # Créer le dossier des pochettes s'il n'existe pas
            covers_dir = filepath.parent / 'covers'
            covers_dir.mkdir(exist_ok=True)
            
            # Générer un nom de fichier unique
            cover_path = covers_dir / f'{filepath.stem}_cover.jpg'
            
            # Redimensionner et enregistrer l'image
            img = Image.open(io.BytesIO(image_data))
            img.thumbnail((300, 300))  # Redimensionner pour économiser de l'espace
            img = img.convert('RGB')  # Convertir en RGB pour le format JPEG
            img.save(cover_path, 'JPEG', quality=85)
            
            return f'/static/music/covers/{cover_path.name}'
            
        except Exception as e:
            logger.error(f'Erreur lors de l\'enregistrement de la pochette: {str(e)}')
            return ''
