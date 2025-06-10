"""
Ajoute des index pour optimiser les requêtes de base de données
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_indexes_20250610'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Index sur les colonnes fréquemment utilisées dans les requêtes
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # Index sur les clés étrangères pour accélérer les jointures
    op.create_index('ix_playlists_user_id', 'playlists', ['user_id'])
    
    # Index sur les colonnes utilisées pour le tri
    op.create_index('ix_tracks_title', 'tracks', ['title'])
    op.create_index('ix_tracks_artist', 'tracks', ['artist'])
    op.create_index('ix_tracks_created_at', 'tracks', ['created_at'])
    
    # Index composite pour les recherches fréquentes
    op.create_index('ix_playlist_tracks_playlist_position', 'playlist_tracks', ['playlist_id', 'position'])

def downgrade():
    # Suppression des index en cas de rollback
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_playlists_user_id', table_name='playlists')
    op.drop_index('ix_tracks_title', table_name='tracks')
    op.drop_index('ix_tracks_artist', table_name='tracks')
    op.drop_index('ix_tracks_created_at', table_name='tracks')
    op.drop_index('ix_playlist_tracks_playlist_position', table_name='playlist_tracks')
