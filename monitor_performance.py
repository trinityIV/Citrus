"""
Script de monitoring des performances de la base de données
"""

import os
import sys
import time
import logging
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('performance_log.txt')
    ]
)

logger = logging.getLogger(__name__)

# Configuration
PERFORMANCE_LOG_FILE = 'performance_metrics.json'
SLOW_QUERY_THRESHOLD = 0.1  # secondes
QUERY_SAMPLES = {
    'track_search': "SELECT id, title, artist, album FROM tracks WHERE title LIKE '%a%' OR artist LIKE '%a%' LIMIT 20",
    'playlist_tracks': "SELECT t.id, t.title, t.artist FROM tracks t JOIN playlist_tracks pt ON t.id = pt.track_id WHERE pt.playlist_id = 1 ORDER BY pt.position",
    'user_playlists': "SELECT p.id, p.name, COUNT(pt.track_id) as track_count FROM playlists p LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id WHERE p.user_id = 1 GROUP BY p.id",
    'recent_tracks': "SELECT id, title, artist, album FROM tracks ORDER BY created_at DESC LIMIT 10",
    'track_count': "SELECT COUNT(*) FROM tracks",
    'playlist_count': "SELECT COUNT(*) FROM playlists",
}

def get_db_connection():
    """Établit une connexion à la base de données SQLite"""
    db_path = os.path.join(os.getcwd(), 'instance', 'citrus.db')
    
    if not os.path.exists(db_path):
        logger.error(f"Base de données non trouvée à {db_path}")
        return None
    
    logger.info(f"Connexion à la base de données: {db_path}")
    return sqlite3.connect(db_path)

def measure_query_performance(conn, query_name, query, params=None, iterations=3):
    """Mesure les performances d'une requête"""
    cursor = conn.cursor()
    times = []
    
    for i in range(iterations):
        start_time = time.time()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        elapsed = time.time() - start_time
        times.append(elapsed)
        
        if i == 0:
            result_count = len(results)
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    if avg_time > SLOW_QUERY_THRESHOLD:
        logger.warning(f"Requête lente détectée: {query_name} - {avg_time:.6f}s")
    
    logger.info(f"Requête: {query_name}")
    logger.info(f"  Temps moyen: {avg_time:.6f}s (min: {min_time:.6f}s, max: {max_time:.6f}s)")
    logger.info(f"  Résultats: {result_count}")
    
    return {
        'name': query_name,
        'avg_time': avg_time,
        'min_time': min_time,
        'max_time': max_time,
        'result_count': result_count,
        'timestamp': datetime.now().isoformat(),
        'is_slow': avg_time > SLOW_QUERY_THRESHOLD
    }

def get_db_stats(conn):
    """Récupère les statistiques de la base de données"""
    cursor = conn.cursor()
    
    # Taille de la base de données
    db_path = os.path.join(os.getcwd(), 'instance', 'citrus.db')
    db_size = os.path.getsize(db_path)
    
    # Nombre de tables
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    table_count = cursor.fetchone()[0]
    
    # Statistiques par table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    table_stats = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        table_stats[table_name] = row_count
    
    # Nombre d'index
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
    index_count = cursor.fetchone()[0]
    
    return {
        'db_size': db_size,
        'table_count': table_count,
        'index_count': index_count,
        'table_stats': table_stats,
        'timestamp': datetime.now().isoformat()
    }

def save_metrics(metrics):
    """Sauvegarde les métriques dans un fichier JSON"""
    if os.path.exists(PERFORMANCE_LOG_FILE):
        with open(PERFORMANCE_LOG_FILE, 'r') as f:
            try:
                existing_metrics = json.load(f)
            except json.JSONDecodeError:
                existing_metrics = {'query_metrics': [], 'db_stats': []}
    else:
        existing_metrics = {'query_metrics': [], 'db_stats': []}
    
    existing_metrics['query_metrics'].extend(metrics['query_metrics'])
    existing_metrics['db_stats'].append(metrics['db_stats'])
    
    with open(PERFORMANCE_LOG_FILE, 'w') as f:
        json.dump(existing_metrics, f, indent=2)
    
    logger.info(f"Métriques sauvegardées dans {PERFORMANCE_LOG_FILE}")

def load_metrics():
    """Charge les métriques depuis le fichier JSON"""
    if not os.path.exists(PERFORMANCE_LOG_FILE):
        return {'query_metrics': [], 'db_stats': []}
    
    with open(PERFORMANCE_LOG_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {'query_metrics': [], 'db_stats': []}

def generate_performance_report(metrics=None):
    """Génère un rapport de performance"""
    if metrics is None:
        metrics = load_metrics()
    
    if not metrics['query_metrics']:
        logger.warning("Aucune métrique disponible pour générer un rapport")
        return
    
    # Regrouper les métriques par nom de requête
    query_groups = {}
    for metric in metrics['query_metrics']:
        name = metric['name']
        if name not in query_groups:
            query_groups[name] = []
        query_groups[name].append(metric)
    
    # Générer le rapport
    report = ["# Rapport de performance de la base de données\n"]
    report.append(f"Date du rapport: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Statistiques de la base de données
    if metrics['db_stats']:
        latest_stats = metrics['db_stats'][-1]
        report.append("## Statistiques de la base de données\n")
        report.append(f"- Taille: {latest_stats['db_size'] / 1024:.2f} Ko")
        report.append(f"- Tables: {latest_stats['table_count']}")
        report.append(f"- Index: {latest_stats['index_count']}")
        report.append("\n### Nombre d'enregistrements par table\n")
        for table, count in latest_stats['table_stats'].items():
            report.append(f"- {table}: {count}")
        report.append("\n")
    
    # Performance des requêtes
    report.append("## Performance des requêtes\n")
    for name, metrics_list in query_groups.items():
        avg_times = [m['avg_time'] for m in metrics_list]
        avg_time = sum(avg_times) / len(avg_times) if avg_times else 0
        min_time = min(avg_times) if avg_times else 0
        max_time = max(avg_times) if avg_times else 0
        
        report.append(f"### {name}\n")
        report.append(f"- Temps moyen: {avg_time:.6f}s")
        report.append(f"- Temps min: {min_time:.6f}s")
        report.append(f"- Temps max: {max_time:.6f}s")
        report.append(f"- Nombre d'exécutions: {len(metrics_list)}")
        
        if avg_time > SLOW_QUERY_THRESHOLD:
            report.append(f"- **ATTENTION**: Cette requête est lente (> {SLOW_QUERY_THRESHOLD}s)")
        
        report.append("\n")
    
    # Requêtes lentes
    slow_queries = [m for m in metrics['query_metrics'] if m['is_slow']]
    if slow_queries:
        report.append("## Requêtes lentes détectées\n")
        for query in slow_queries:
            report.append(f"- {query['name']}: {query['avg_time']:.6f}s ({query['timestamp']})")
        report.append("\n")
    
    # Écrire le rapport dans un fichier
    report_file = 'performance_report.md'
    with open(report_file, 'w') as f:
        f.write('\n'.join(report))
    
    logger.info(f"Rapport de performance généré: {report_file}")
    return report_file

def generate_performance_charts(metrics=None):
    """Génère des graphiques de performance"""
    if metrics is None:
        metrics = load_metrics()
    
    if not metrics['query_metrics']:
        logger.warning("Aucune métrique disponible pour générer des graphiques")
        return
    
    # Regrouper les métriques par nom de requête
    query_groups = {}
    for metric in metrics['query_metrics']:
        name = metric['name']
        if name not in query_groups:
            query_groups[name] = []
        query_groups[name].append(metric)
    
    # Créer un graphique pour chaque requête
    plt.figure(figsize=(12, 8))
    
    # Graphique des temps moyens
    plt.subplot(2, 1, 1)
    names = list(query_groups.keys())
    avg_times = [sum(m['avg_time'] for m in group) / len(group) for group in query_groups.values()]
    
    bars = plt.bar(names, avg_times)
    plt.axhline(y=SLOW_QUERY_THRESHOLD, color='r', linestyle='-', label=f'Seuil de lenteur ({SLOW_QUERY_THRESHOLD}s)')
    
    # Colorer les barres en fonction du seuil
    for i, bar in enumerate(bars):
        if avg_times[i] > SLOW_QUERY_THRESHOLD:
            bar.set_color('red')
    
    plt.title('Temps moyen d\'exécution par requête')
    plt.ylabel('Temps (secondes)')
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    
    # Graphique de l'évolution des temps pour une requête spécifique
    if query_groups:
        plt.subplot(2, 1, 2)
        
        # Prendre la requête avec le plus de mesures
        query_name = max(query_groups.items(), key=lambda x: len(x[1]))[0]
        metrics_list = query_groups[query_name]
        
        times = [m['avg_time'] for m in metrics_list]
        timestamps = [datetime.fromisoformat(m['timestamp']) for m in metrics_list]
        
        plt.plot(timestamps, times, marker='o')
        plt.axhline(y=SLOW_QUERY_THRESHOLD, color='r', linestyle='-', label=f'Seuil de lenteur ({SLOW_QUERY_THRESHOLD}s)')
        plt.title(f'Évolution du temps d\'exécution pour {query_name}')
        plt.ylabel('Temps (secondes)')
        plt.xlabel('Date')
        plt.xticks(rotation=45, ha='right')
        plt.legend()
    
    plt.tight_layout()
    
    # Sauvegarder le graphique
    chart_file = 'performance_charts.png'
    plt.savefig(chart_file)
    logger.info(f"Graphiques de performance générés: {chart_file}")
    return chart_file

def run_performance_tests():
    """Exécute les tests de performance"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        logger.info("Démarrage des tests de performance...")
        
        # Mesurer les performances des requêtes
        query_metrics = []
        for name, query in QUERY_SAMPLES.items():
            metric = measure_query_performance(conn, name, query)
            query_metrics.append(metric)
        
        # Récupérer les statistiques de la base de données
        db_stats = get_db_stats(conn)
        
        # Sauvegarder les métriques
        metrics = {
            'query_metrics': query_metrics,
            'db_stats': db_stats
        }
        save_metrics(metrics)
        
        # Générer le rapport et les graphiques
        generate_performance_report(metrics)
        generate_performance_charts(metrics)
        
    except Exception as e:
        logger.error(f"Erreur lors des tests de performance: {str(e)}")
    finally:
        conn.close()

def main():
    """Fonction principale"""
    logger.info("Démarrage du script de monitoring des performances...")
    run_performance_tests()
    logger.info("Script de monitoring des performances terminé")

if __name__ == "__main__":
    main()
