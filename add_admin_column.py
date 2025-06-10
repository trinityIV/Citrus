"""
Script pour ajouter manuellement la colonne is_admin à la table users
"""

import os
import sys
import logging
import sqlite3
from pathlib import Path

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def add_admin_column():
    """Ajoute manuellement la colonne is_admin à la table users"""
    # Chemin vers la base de données
    db_path = os.path.join(os.getcwd(), 'instance', 'citrus.db')
    
    if not os.path.exists(db_path):
        logger.error(f"Base de données non trouvée à {db_path}")
        return False
    
    logger.info(f"Connexion à la base de données: {db_path}")
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si la colonne existe déjà
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_admin' in columns:
            logger.info("La colonne is_admin existe déjà")
            conn.close()
            return True
        
        # Ajouter la colonne is_admin
        logger.info("Ajout de la colonne is_admin à la table users")
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        
        # Définir le premier utilisateur comme admin
        logger.info("Définition du premier utilisateur comme admin")
        cursor.execute("UPDATE users SET is_admin = 1 WHERE id = (SELECT MIN(id) FROM users)")
        
        # Valider les changements
        conn.commit()
        logger.info("Colonne is_admin ajoutée avec succès")
        
        # Fermer la connexion
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Erreur SQLite: {str(e)}")
        return False

def main():
    """Fonction principale"""
    logger.info("Démarrage du script d'ajout de colonne...")
    
    success = add_admin_column()
    
    if success:
        logger.info("Script terminé avec succès")
    else:
        logger.error("Échec du script")
        sys.exit(1)

if __name__ == "__main__":
    main()
