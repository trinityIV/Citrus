"""
Script pour optimiser les index de la base de données
"""

import os
import sys
import logging
import sqlite3
import time
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

def get_db_connection():
    """Établit une connexion à la base de données SQLite"""
    db_path = os.path.join(os.getcwd(), 'instance', 'citrus.db')
    
    if not os.path.exists(db_path):
        logger.error(f"Base de données non trouvée à {db_path}")
        return None
    
    logger.info(f"Connexion à la base de données: {db_path}")
    return sqlite3.connect(db_path)

def list_existing_indexes(conn):
    """Liste les index existants dans la base de données"""
    cursor = conn.cursor()
    cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type = 'index'")
    indexes = cursor.fetchall()
    
    logger.info("Index existants:")
    for index_name, table_name in indexes:
        logger.info(f"  {index_name} sur la table {table_name}")
    
    return indexes

def measure_query_performance(conn, query, params=None, iterations=5):
    """Mesure les performances d'une requête"""
    cursor = conn.cursor()
    total_time = 0
    
    for i in range(iterations):
        start_time = time.time()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        elapsed = time.time() - start_time
        total_time += elapsed
        
        if i == 0:
            result_count = len(results)
    
    avg_time = total_time / iterations
    logger.info(f"Requête: {query[:60]}...")
    logger.info(f"  Temps moyen: {avg_time:.6f}s pour {result_count} résultats")
    
    return avg_time, result_count

def create_index(conn, table, columns, index_name=None):
    """Crée un index sur une table"""
    cursor = conn.cursor()
    
    if not index_name:
        index_name = f"idx_{table}_{'_'.join(columns)}"
    
    columns_str = ', '.join(columns)
    
    try:
        logger.info(f"Création de l'index {index_name} sur {table}({columns_str})...")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({columns_str})")
        conn.commit()
        logger.info(f"Index {index_name} créé avec succès")
        return True
    except sqlite3.Error as e:
        logger.error(f"Erreur lors de la création de l'index: {str(e)}")
        return False

def test_search_performance(conn, before_after="before"):
    """Teste les performances des requêtes de recherche"""
    logger.info(f"\nTest des performances de recherche ({before_after} optimisation):")
    
    # Test 1: Recherche de pistes par titre
    query1 = "SELECT id, title, artist, album FROM tracks WHERE title LIKE ? LIMIT 20"
    params1 = ('%Love%',)
    time1, count1 = measure_query_performance(conn, query1, params1)
    
    # Test 2: Recherche de pistes par artiste
    query2 = "SELECT id, title, artist, album FROM tracks WHERE artist LIKE ? LIMIT 20"
    params2 = ('%John%',)
    time2, count2 = measure_query_performance(conn, query2, params2)
    
    # Test 3: Recherche combinée
    query3 = """
        SELECT id, title, artist, album 
        FROM tracks 
        WHERE title LIKE ? OR artist LIKE ? OR album LIKE ? 
        LIMIT 20
    """
    params3 = ('%a%', '%a%', '%a%')
    time3, count3 = measure_query_performance(conn, query3, params3)
    
    return {
        "title_search": {"time": time1, "count": count1},
        "artist_search": {"time": time2, "count": count2},
        "combined_search": {"time": time3, "count": count3}
    }

def test_playlist_performance(conn, before_after="before"):
    """Teste les performances des requêtes de playlists"""
    logger.info(f"\nTest des performances de playlists ({before_after} optimisation):")
    
    # Test 1: Récupération des playlists d'un utilisateur
    query1 = """
        SELECT p.id, p.name, p.description, COUNT(pt.track_id) as track_count
        FROM playlists p
        LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
        WHERE p.user_id = ?
        GROUP BY p.id
        LIMIT 20
    """
    params1 = (1,)  # Utilisateur avec ID 1
    time1, count1 = measure_query_performance(conn, query1, params1)
    
    # Test 2: Récupération des pistes d'une playlist
    query2 = """
        SELECT t.id, t.title, t.artist, t.album, t.duration
        FROM tracks t
        JOIN playlist_tracks pt ON t.id = pt.track_id
        WHERE pt.playlist_id = ?
        ORDER BY pt.position
        LIMIT 50
    """
    params2 = (1,)  # Playlist avec ID 1
    time2, count2 = measure_query_performance(conn, query2, params2)
    
    return {
        "user_playlists": {"time": time1, "count": count1},
        "playlist_tracks": {"time": time2, "count": count2}
    }

def optimize_indexes(conn):
    """Optimise les index de la base de données"""
    logger.info("\nOptimisation des index...")
    
    # 1. Index pour la recherche de pistes
    create_index(conn, "tracks", ["title"])
    create_index(conn, "tracks", ["artist"])
    create_index(conn, "tracks", ["album"])
    
    # 2. Index pour les playlists
    create_index(conn, "playlists", ["user_id"])
    create_index(conn, "playlist_tracks", ["playlist_id"])
    create_index(conn, "playlist_tracks", ["track_id"])
    create_index(conn, "playlist_tracks", ["playlist_id", "position"])
    
    # 3. Index pour les utilisateurs
    create_index(conn, "users", ["username"])
    create_index(conn, "users", ["email"])
    
    logger.info("Optimisation des index terminée")

def main():
    """Fonction principale"""
    logger.info("Démarrage du script d'optimisation des index...")
    
    # Établir la connexion à la base de données
    conn = get_db_connection()
    if not conn:
        sys.exit(1)
    
    try:
        # Lister les index existants
        list_existing_indexes(conn)
        
        # Tester les performances avant optimisation
        before_search = test_search_performance(conn, "avant")
        before_playlist = test_playlist_performance(conn, "avant")
        
        # Optimiser les index
        optimize_indexes(conn)
        
        # Lister les index après optimisation
        list_existing_indexes(conn)
        
        # Tester les performances après optimisation
        after_search = test_search_performance(conn, "après")
        after_playlist = test_playlist_performance(conn, "après")
        
        # Afficher les améliorations
        logger.info("\nRésumé des améliorations:")
        
        for test_name, before in before_search.items():
            after = after_search[test_name]
            if before["time"] > 0:
                improvement = (before["time"] - after["time"]) / before["time"] * 100
                logger.info(f"  {test_name}: {improvement:.2f}% d'amélioration")
        
        for test_name, before in before_playlist.items():
            after = after_playlist[test_name]
            if before["time"] > 0:
                improvement = (before["time"] - after["time"]) / before["time"] * 100
                logger.info(f"  {test_name}: {improvement:.2f}% d'amélioration")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation des index: {str(e)}")
    finally:
        conn.close()
        logger.info("Script d'optimisation des index terminé")

if __name__ == "__main__":
    main()
