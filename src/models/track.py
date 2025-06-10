"""
Modèle de données pour les pistes audio
"""

from datetime import datetime, UTC
from ..database import db

class Track(db.Model):
    """Modèle pour une piste audio"""
    __tablename__ = 'tracks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200))
    album = db.Column(db.String(200))
    duration = db.Column(db.Float)
    file_path = db.Column(db.String(500), nullable=False, unique=True)
    file_size = db.Column(db.Integer)  # Taille en octets
    bitrate = db.Column(db.Integer)  # Bitrate en kbps
    sample_rate = db.Column(db.Integer)  # Fréquence d'échantillonnage en Hz
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relations
    playlists = db.relationship(
        'Playlist',
        secondary='playlist_tracks',
        back_populates='tracks'
    )

    def to_dict(self):
        """Convertit la piste en dictionnaire"""
        return {
            'id': self.id,
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'duration': self.duration,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'bitrate': self.bitrate,
            'sample_rate': self.sample_rate,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @property
    def duration_formatted(self):
        """Retourne la durée formatée (MM:SS)"""
        if not self.duration:
            return '00:00'
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f'{minutes:02d}:{seconds:02d}'

    @property
    def file_size_formatted(self):
        """Retourne la taille formatée (Ko, Mo, Go)"""
        if not self.file_size:
            return '0 Ko'
        
        units = ['o', 'Ko', 'Mo', 'Go']
        size = float(self.file_size)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
            
        return f'{size:.1f} {units[unit_index]}'
