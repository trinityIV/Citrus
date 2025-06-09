"""
Modèle de données pour les playlists
"""

from datetime import datetime
from ..database import db

# Table d'association pour les pistes dans les playlists
playlist_tracks = db.Table('playlist_tracks',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlists.id'), primary_key=True),
    db.Column('track_id', db.Integer, db.ForeignKey('tracks.id'), primary_key=True),
    db.Column('position', db.Integer, nullable=False),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)

class Playlist(db.Model):
    """Modèle pour une playlist"""
    __tablename__ = 'playlists'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = None

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    cover_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relations
    user = db.relationship("User", back_populates="playlists")
    tracks = db.relationship(
        "Track",
        secondary=playlist_tracks,
        order_by=playlist_tracks.c.position,
        back_populates="playlists"
    )

    @property
    def track_count(self):
        """Retourne le nombre de pistes dans la playlist"""
        return len(self.tracks)

    @property
    def total_duration(self):
        """Retourne la durée totale de la playlist en secondes"""
        return sum(track.duration for track in self.tracks if track.duration)

    def to_dict(self):
        """Convertit la playlist en dictionnaire"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'cover_image': self.cover_image,
            'track_count': self.track_count,
            'total_duration': self.total_duration,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def add_track(self, track, position=None):
        """Ajoute une piste à la playlist"""
        if position is None:
            position = self.track_count + 1
        
        # Décaler les positions des pistes existantes si nécessaire
        if position <= self.track_count:
            for t in self.tracks:
                current_position = self.get_track_position(t)
                if current_position >= position:
                    self.set_track_position(t, current_position + 1)
        
        # Ajouter la nouvelle piste
        self.tracks.append(track)
        self.set_track_position(track, position)

    def remove_track(self, track):
        """Retire une piste de la playlist"""
        if track in self.tracks:
            position = self.get_track_position(track)
            self.tracks.remove(track)
            
            # Réorganiser les positions
            for t in self.tracks:
                current_position = self.get_track_position(t)
                if current_position > position:
                    self.set_track_position(t, current_position - 1)

    def get_track_position(self, track):
        """Obtient la position d'une piste dans la playlist"""
        if track not in self.tracks:
            return None
        
        from sqlalchemy import select
        result = self.session.execute(
            select(playlist_tracks.c.position)
            .where(playlist_tracks.c.playlist_id == self.id)
            .where(playlist_tracks.c.track_id == track.id)
        ).scalar_one_or_none()
        return result

    def set_track_position(self, track, position):
        """Définit la position d'une piste dans la playlist"""
        if track not in self.tracks:
            return
        
        from sqlalchemy import update
        self.session.execute(
            update(playlist_tracks)
            .where(playlist_tracks.c.playlist_id == self.id)
            .where(playlist_tracks.c.track_id == track.id)
            .values(position=position)
        )
        self.session.commit()
