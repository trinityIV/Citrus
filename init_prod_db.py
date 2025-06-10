"""
Script d'initialisation de la base de données de production pour Citrus Music Server
"""

from src import create_app
from src.database import db
from src.models.user import User
import os

# Créer l'application en mode production
app = create_app('production')

with app.app_context():
    # Créer toutes les tables
    db.create_all()
    
    # Créer un utilisateur administrateur
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@citrus.local', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Utilisateur administrateur créé avec succès !")
    else:
        print("L'utilisateur administrateur existe déjà.")
    
    # Vérifier que la table users existe et contient la colonne is_admin
    try:
        result = db.session.execute(db.text("PRAGMA table_info(users)")).fetchall()
        columns = [row[1] for row in result]
        if 'is_admin' not in columns:
            print("Ajout de la colonne is_admin à la table users...")
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            db.session.commit()
            print("Colonne is_admin ajoutée avec succès !")
    except Exception as e:
        print(f"Erreur lors de la vérification/ajout de la colonne is_admin : {e}")
    
    print("Base de données de production initialisée avec succès !")
