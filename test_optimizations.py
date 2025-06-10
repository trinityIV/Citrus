"""
Script de test des optimisations de base de données
"""

import os
import time
import logging
import sys
import sqlite3
from datetime import datetime
from sqlalchemy import func, text
from flask import Flask, g

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def create_test_app():
    """Crée une application Flask de test"""
    # Configurer manuellement l'application pour éviter les problèmes d'importation
    from flask import Flask
    from pathlib import Path
    
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///citrus.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_ENABLED=False,
        UPLOAD_FOLDER=str(Path('src/static/uploads')),
        MUSIC_FOLDER=str(Path('src/static/music')),
        PLAYLIST_FOLDER=str(Path('src/static/playlists')),
        SECRET_KEY='dev-key-for-testing',
        MAX_CONTENT_LENGTH=100 * 1024 * 1024  # 100MB
    )
    
    # Initialiser les extensions
    from src.database import db
    db.init_app(app)
    
    return app

def test_query_performance(app):
    """Teste les performances des requêtes"""
    from src.database import db_session
    from src.models.track import Track
    from src.models.playlist import Playlist
    from src.utils.query_optimizations import optimize_track_search, get_user_playlists_optimized
    
    with app.app_context():
        # Test de recherche de pistes
        logger.info("Test de recherche de pistes...")
        
        # Première recherche (sans cache)
        start_time = time.time()
        results1 = optimize_track_search("test", limit=20, offset=0)
        elapsed1 = time.time() - start_time
        logger.info(f"Recherche 1 (sans cache): {elapsed1:.4f}s - {len(results1)} résultats")
        
        # Deuxième recherche (avec cache)
        start_time = time.time()
        results2 = optimize_track_search("test", limit=20, offset=0)
        elapsed2 = time.time() - start_time
        logger.info(f"Recherche 2 (avec cache): {elapsed2:.4f}s - {len(results2)} résultats")
        
        # Calcul de l'amélioration
        if elapsed1 > 0:
            improvement = (elapsed1 - elapsed2) / elapsed1 * 100
            logger.info(f"Amélioration: {improvement:.2f}%")
        
        # Test de récupération des playlists
        logger.info("\nTest de récupération des playlists...")
        
        # Récupérer un utilisateur pour le test
        user_id = db_session.query(func.min(Playlist.user_id)).scalar()
        
        if user_id:
            # Première récupération (sans cache)
            start_time = time.time()
            playlists1 = get_user_playlists_optimized(user_id, page=1, per_page=20)
            elapsed1 = time.time() - start_time
            logger.info(f"Récupération 1 (sans cache): {elapsed1:.4f}s - {playlists1['total']} playlists")
            
            # Deuxième récupération (avec cache)
            start_time = time.time()
            playlists2 = get_user_playlists_optimized(user_id, page=1, per_page=20)
            elapsed2 = time.time() - start_time
            logger.info(f"Récupération 2 (avec cache): {elapsed2:.4f}s - {playlists2['total']} playlists")
            
            # Calcul de l'amélioration
            if elapsed1 > 0:
                improvement = (elapsed1 - elapsed2) / elapsed1 * 100
                logger.info(f"Amélioration: {improvement:.2f}%")
        else:
            logger.warning("Aucun utilisateur avec des playlists trouvé pour le test")

def test_db_stats(app):
    """Teste les statistiques de la base de données"""
    from src.utils.db_optimizations import get_db_stats, optimize_db
    
    with app.app_context():
        logger.info("\nTest des statistiques de la base de données...")
        
        # Récupérer les statistiques
        stats = get_db_stats()
        logger.info(f"Nombre de tables: {stats.get('table_count', 'N/A')}")
        logger.info(f"Taille de la base de données: {stats.get('db_size', 'N/A')} octets")
        
        # Afficher les statistiques par table
        if 'tables' in stats:
            logger.info("\nStatistiques par table:")
            for table, table_stats in stats['tables'].items():
                logger.info(f"  {table}: {table_stats.get('row_count', 'N/A')} lignes")
        
        # Optimiser la base de données
        logger.info("\nOptimisation de la base de données...")
        results = optimize_db()
        logger.info(f"Résultats de l'optimisation: {results}")

def make_admin_user(app):
    """Définit le premier utilisateur comme administrateur"""
    from src.database import db_session
    from src.models.user import User
    
    with app.app_context():
        logger.info("\nConfiguration d'un utilisateur administrateur...")
        
        # Récupérer le premier utilisateur
        user = db_session.query(User).first()
        
        if user:
            user.is_admin = True
            db_session.commit()
            logger.info(f"Utilisateur {user.username} (ID: {user.id}) défini comme administrateur")
        else:
            logger.warning("Aucun utilisateur trouvé")

def test_db_direct():
    """Teste directement les performances de la base de données sans Flask"""
    logger.info("\nTest direct des performances de la base de données...")
    
    try:
        # Connexion directe à la base de données SQLite
        db_path = os.path.join(os.getcwd(), 'instance', 'citrus.db')
        if not os.path.exists(db_path):
            logger.error(f"Base de données non trouvée à {db_path}")
            return
            
        logger.info(f"Connexion à la base de données: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tester les performances des requêtes
        logger.info("Test de performance des requêtes...")
        
        # 1. Compter le nombre d'utilisateurs
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        elapsed = time.time() - start_time
        logger.info(f"Nombre d'utilisateurs: {user_count} ({elapsed:.4f}s)")
        
        # 2. Compter le nombre de pistes
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM tracks")
        track_count = cursor.fetchone()[0]
        elapsed = time.time() - start_time
        logger.info(f"Nombre de pistes: {track_count} ({elapsed:.4f}s)")
        
        # 3. Compter le nombre de playlists
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM playlists")
        playlist_count = cursor.fetchone()[0]
        elapsed = time.time() - start_time
        logger.info(f"Nombre de playlists: {playlist_count} ({elapsed:.4f}s)")
        
        # 4. Tester une requête de recherche
        search_term = '%a%'  # Rechercher les pistes contenant 'a'
        start_time = time.time()
        cursor.execute(
            """SELECT id, title, artist, album FROM tracks 
               WHERE title LIKE ? OR artist LIKE ? OR album LIKE ? 
               LIMIT 20""", 
            (search_term, search_term, search_term)
        )
        search_results = cursor.fetchall()
        elapsed = time.time() - start_time
        logger.info(f"Recherche de pistes: {len(search_results)} résultats ({elapsed:.4f}s)")
        
        # 5. Tester une requête de jointure
        if playlist_count > 0:
            start_time = time.time()
            cursor.execute(
                """SELECT t.id, t.title, t.artist, t.album 
                   FROM tracks t 
                   JOIN playlist_tracks pt ON t.id = pt.track_id 
                   WHERE pt.playlist_id = 1 
                   LIMIT 20"""
            )
            playlist_tracks = cursor.fetchall()
            elapsed = time.time() - start_time
            logger.info(f"Pistes de playlist: {len(playlist_tracks)} résultats ({elapsed:.4f}s)")
        
        # Fermer la connexion
        conn.close()
        
    except Exception as e:
        logger.error(f"Erreur lors du test direct de la base de données: {str(e)}")

def main():
    """Fonction principale"""
    logger.info("Démarrage du script de test des optimisations...")
    
    # Créer l'application Flask
    app = create_test_app()
    
    # Tester directement la base de données
    test_db_direct()
    
    # Tester les performances des requêtes avec l'application Flask
    test_query_performance(app)
    
    # Tester les statistiques de la base de données
    test_db_stats(app)
    
    logger.info("\nTests terminés")

if __name__ == "__main__":
    main()
