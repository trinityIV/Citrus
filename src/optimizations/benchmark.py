#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de benchmark pour Citrus Music Server
Ce script mesure les performances des requêtes avec et sans optimisations
"""

import os
import sys
import time
import sqlite3
import statistics
from datetime import datetime

# Ajouter le répertoire parent au path pour pouvoir importer les modules du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import db, Track, Playlist, User
from utils.db_optimizations import QueryCache
from utils.query_optimizations import get_tracks_optimized, get_playlists_optimized

# Configuration
ITERATIONS = 10  # Nombre d'exécutions pour chaque requête
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'citrus.db')
RESULTS_FILE = os.path.join(os.path.dirname(__file__), 'benchmark_results.md')

class BenchmarkRunner:
    """Classe pour exécuter des benchmarks sur les requêtes de base de données"""
    
    def __init__(self):
        """Initialisation du benchmark runner"""
        self.results = {}
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        
        # Vérifier que la base de données contient suffisamment de données
        self._check_data_volume()
    
    def _check_data_volume(self):
        """Vérifie que la base de données contient suffisamment de données pour un benchmark significatif"""
        cursor = self.conn.cursor()
        track_count = cursor.execute("SELECT COUNT(*) FROM track").fetchone()[0]
        playlist_count = cursor.execute("SELECT COUNT(*) FROM playlist").fetchone()[0]
        
        if track_count < 100 or playlist_count < 10:
            print(f"AVERTISSEMENT: Volume de données insuffisant pour un benchmark significatif.")
            print(f"Pistes: {track_count} (min. recommandé: 100)")
            print(f"Playlists: {playlist_count} (min. recommandé: 10)")
            print("Exécutez d'abord le script generate_test_data.py pour créer des données de test.")
    
    def run_benchmark(self, name, query_func, *args, **kwargs):
        """Exécute un benchmark sur une fonction de requête donnée"""
        print(f"Exécution du benchmark pour: {name}")
        times = []
        
        # Exécuter la requête plusieurs fois et mesurer le temps
        for i in range(ITERATIONS):
            start_time = time.time()
            result = query_func(*args, **kwargs)
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convertir en ms
            times.append(execution_time)
            print(f"  Itération {i+1}/{ITERATIONS}: {execution_time:.2f} ms")
        
        # Calculer les statistiques
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)
        
        self.results[name] = {
            'avg': avg_time,
            'median': median_time,
            'min': min_time,
            'max': max_time,
            'iterations': ITERATIONS
        }
        
        print(f"  Temps moyen: {avg_time:.2f} ms")
        print(f"  Temps médian: {median_time:.2f} ms")
        print(f"  Temps min/max: {min_time:.2f} ms / {max_time:.2f} ms")
        print("")
        
        return avg_time
    
    def compare_queries(self, standard_name, optimized_name):
        """Compare les performances entre deux requêtes (standard vs optimisée)"""
        if standard_name in self.results and optimized_name in self.results:
            std_time = self.results[standard_name]['avg']
            opt_time = self.results[optimized_name]['avg']
            
            if std_time > 0:
                improvement = ((std_time - opt_time) / std_time) * 100
                self.results[f"comparison_{standard_name}_vs_{optimized_name}"] = {
                    'standard': std_time,
                    'optimized': opt_time,
                    'improvement': improvement
                }
                
                print(f"Comparaison: {standard_name} vs {optimized_name}")
                print(f"  Standard: {std_time:.2f} ms")
                print(f"  Optimisé: {opt_time:.2f} ms")
                print(f"  Amélioration: {improvement:.2f}%")
                print("")
    
    def generate_report(self):
        """Génère un rapport de benchmark au format Markdown"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# Rapport de Benchmark Citrus Music Server\n\n")
            f.write(f"Date: {now}\n\n")
            f.write(f"## Configuration\n\n")
            f.write(f"- Itérations par requête: {ITERATIONS}\n")
            f.write(f"- Base de données: {DB_PATH}\n\n")
            
            f.write(f"## Résultats des requêtes\n\n")
            f.write(f"| Requête | Temps moyen (ms) | Temps médian (ms) | Min (ms) | Max (ms) |\n")
            f.write(f"|---------|-----------------|-------------------|----------|----------|\n")
            
            for name, data in self.results.items():
                if not name.startswith('comparison_'):
                    f.write(f"| {name} | {data['avg']:.2f} | {data['median']:.2f} | {data['min']:.2f} | {data['max']:.2f} |\n")
            
            f.write(f"\n## Comparaisons\n\n")
            f.write(f"| Comparaison | Standard (ms) | Optimisé (ms) | Amélioration |\n")
            f.write(f"|-------------|---------------|---------------|-------------|\n")
            
            for name, data in self.results.items():
                if name.startswith('comparison_'):
                    f.write(f"| {name.replace('comparison_', '').replace('_vs_', ' vs ')} | {data['standard']:.2f} | {data['optimized']:.2f} | {data['improvement']:.2f}% |\n")
        
        print(f"Rapport généré: {RESULTS_FILE}")

def standard_get_tracks(limit=20, offset=0, sort_by='title', order='asc'):
    """Requête standard pour récupérer des pistes"""
    cursor = sqlite3.connect(DB_PATH).cursor()
    query = f"SELECT * FROM track ORDER BY {sort_by} {order} LIMIT {limit} OFFSET {offset}"
    return cursor.execute(query).fetchall()

def standard_search_tracks(search_term, limit=20):
    """Requête standard pour rechercher des pistes"""
    cursor = sqlite3.connect(DB_PATH).cursor()
    query = f"""
        SELECT * FROM track 
        WHERE title LIKE ? OR artist LIKE ? OR album LIKE ? 
        LIMIT {limit}
    """
    search_param = f"%{search_term}%"
    return cursor.execute(query, (search_param, search_param, search_param)).fetchall()

def standard_get_playlists(user_id, limit=20):
    """Requête standard pour récupérer les playlists d'un utilisateur"""
    cursor = sqlite3.connect(DB_PATH).cursor()
    query = f"SELECT * FROM playlist WHERE user_id = ? LIMIT {limit}"
    return cursor.execute(query, (user_id,)).fetchall()

def run_benchmarks():
    """Exécute tous les benchmarks"""
    benchmark = BenchmarkRunner()
    
    # Benchmarks pour la récupération de pistes
    benchmark.run_benchmark("Récupération de pistes (standard)", standard_get_tracks, 20, 0, 'title', 'asc')
    benchmark.run_benchmark("Récupération de pistes (optimisée)", get_tracks_optimized, 20, 0, 'title', 'asc')
    benchmark.compare_queries("Récupération de pistes (standard)", "Récupération de pistes (optimisée)")
    
    # Benchmarks pour la recherche de pistes
    benchmark.run_benchmark("Recherche de pistes (standard)", standard_search_tracks, "love")
    benchmark.run_benchmark("Recherche de pistes (optimisée)", get_tracks_optimized, 20, 0, 'title', 'asc', "love")
    benchmark.compare_queries("Recherche de pistes (standard)", "Recherche de pistes (optimisée)")
    
    # Benchmarks pour la récupération de playlists
    user_id = 1  # Utiliser l'ID d'un utilisateur existant
    benchmark.run_benchmark("Récupération de playlists (standard)", standard_get_playlists, user_id)
    benchmark.run_benchmark("Récupération de playlists (optimisée)", get_playlists_optimized, user_id)
    benchmark.compare_queries("Récupération de playlists (standard)", "Récupération de playlists (optimisée)")
    
    # Générer le rapport
    benchmark.generate_report()

if __name__ == "__main__":
    run_benchmarks()
