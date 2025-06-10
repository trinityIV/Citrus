"""
Ajoute le champ is_admin à la table des utilisateurs
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_is_admin_20250610'
down_revision = 'add_indexes_20250610'
branch_labels = None
depends_on = None

def upgrade():
    # Ajouter la colonne is_admin à la table users
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))
    
    # Mettre à jour le premier utilisateur pour le rendre administrateur
    op.execute("UPDATE users SET is_admin = 1 WHERE id = 1")

def downgrade():
    # Supprimer la colonne is_admin
    op.drop_column('users', 'is_admin')
