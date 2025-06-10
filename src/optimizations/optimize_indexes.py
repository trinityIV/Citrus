#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script d'optimisation des index de base de données pour Citrus Music Server
Mesure les performances avant et après l'ajout d'index stratégiques
"""

import os
import sys
import time
import sqlite3
from datetime import datetime

# Ajouter le répertoire parent au path pour pouvoir importer les modules du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'citrus.db')
RESULTS_FILE = os.path.join(os.path.dirname(__file__), 'index_optimization_results.md')
TEST_QUERIES = [
    {
        'name': 'Recherche par titre',
        'query': 'SELECT * FROM track WHERE title LIKE ? LIMIT 20',
        'params': ('%love%',)
    },
    {
        'name': 'Recherche par artiste',
        'query': 'SELECT * FROM track WHERE artist LIKE ? LIMIT 20',
        'params': ('%john%',)
    },
    {
        'name': 'Recherche par album',
        'query': 'SELECT * FROM track WHERE album LIKE ? LIMIT 20',
        'params': ('%best%',)
    },
    {
        'name': 'Playlists par utilisateur',
        'query': 'SELECT * FROM playlist WHERE user_id = ?',
        'params': (1,)
    },
    {
        'name': 'Pistes dans playlist',
        'query': '''
            SELECT t.* FROM track t
            JOIN playlist_track pt ON t.id = pt.track_id
            WHERE pt.playlist_id = ?
        ''',
        'params': (1,)
    },
    {
        'name': 'Recherche utilisateur',
        'query': 'SELECT * FROM user WHERE username LIKE ? OR email LIKE ?',
        'params': ('%admin%', '%admin%')
    }
]

class IndexOptimizer:
    """Classe pour optimiser les index de la base de données"""
    
    def __init__(self):
        """Initialisation de l'optimiseur d'index"""
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.results = {'before': {}, 'after': {}}
    
    def get_existing_indexes(self):
        """Récupère les index existants dans la base de données"""
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        return [row[0] for row in self.cursor.fetchall()]
    
    def measure_query_performance(self, query_info, iterations=5):
        """Mesure les performances d'une requête"""
        query = query_info['query']
        params = query_info['params']
        name = query_info['name']
        
        # Exécuter EXPLAIN QUERY PLAN pour voir si des index sont utilisés
        self.cursor.execute(f"EXPLAIN QUERY PLAN {query}", params)
        plan = self.cursor.fetchall()
        uses_index = any('USING INDEX' in str(row) for row in plan)
        
        # Mesurer le temps d'exécution
        times = []
        for _ in range(iterations):
            start_time = time.time()
            self.cursor.execute(query, params)
            self.cursor.fetchall()  # Consommer les résultats
            end_time = time.time()
            times.append((end_time - start_time) * 1000)  # Convertir en ms
        
        avg_time = sum(times) / len(times)
        return {
            'avg_time': avg_time,
            'uses_index': uses_index,
            'plan': [dict(row) for row in plan]
        }
    
    def measure_all_queries(self, phase):
        """Mesure les performances de toutes les requêtes de test"""
        print(f"\nMesure des performances ({phase})...")
        
        for query_info in TEST_QUERIES:
            name = query_info['name']
            print(f"  Exécution de '{name}'...")
            result = self.measure_query_performance(query_info)
            self.results[phase][name] = result
            print(f"    Temps moyen: {result['avg_time']:.2f} ms")
            print(f"    Utilise un index: {'Oui' if result['uses_index'] else 'Non'}")
    
    def create_indexes(self):
        """Crée des index stratégiques pour optimiser les requêtes fréquentes"""
        print("\nCréation des index stratégiques...")
        
        # Index pour les recherches de pistes
        indexes = [
            ("CREATE INDEX IF NOT EXISTS idx_track_title ON track(title)", "Index sur titre des pistes"),
            ("CREATE INDEX IF NOT EXISTS idx_track_artist ON track(artist)", "Index sur artiste des pistes"),
            ("CREATE INDEX IF NOT EXISTS idx_track_album ON track(album)", "Index sur album des pistes"),
            
            # Index pour les playlists
            ("CREATE INDEX IF NOT EXISTS idx_playlist_user_id ON playlist(user_id)", "Index sur user_id des playlists"),
            
            # Index pour les associations playlist-piste
            ("CREATE INDEX IF NOT EXISTS idx_playlist_track_playlist_id ON playlist_track(playlist_id)", "Index sur playlist_id"),
            ("CREATE INDEX IF NOT EXISTS idx_playlist_track_track_id ON playlist_track(track_id)", "Index sur track_id"),
            
            # Index pour les utilisateurs
            ("CREATE INDEX IF NOT EXISTS idx_user_username ON user(username)", "Index sur username"),
            ("CREATE INDEX IF NOT EXISTS idx_user_email ON user(email)", "Index sur email")
        ]
        
        for sql, description in indexes:
            try:
                print(f"  {description}...")
                self.cursor.execute(sql)
                self.conn.commit()
            except sqlite3.Error as e:
                print(f"    ERREUR: {e}")
    
    def generate_report(self):
        """Génère un rapport sur les optimisations d'index"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# Rapport d'Optimisation des Index - Citrus Music Server\n\n")
            f.write(f"Date: {now}\n\n")
            
            # Liste des index
            f.write(f"## Index créés\n\n")
            indexes = self.get_existing_indexes()
            for idx in indexes:
                f.write(f"- `{idx}`\n")
            
            # Résultats des performances
            f.write(f"\n## Résultats des performances\n\n")
            f.write(f"| Requête | Temps avant (ms) | Temps après (ms) | Amélioration | Utilise index |\n")
            f.write(f"|---------|-----------------|------------------|--------------|---------------|\n")
            
            for name in self.results['before'].keys():
                before = self.results['before'][name]['avg_time']
                after = self.results['after'][name]['avg_time']
                improvement = ((before - after) / before) * 100 if before > 0 else 0
                uses_index = "Oui" if self.results['after'][name]['uses_index'] else "Non"
                
                f.write(f"| {name} | {before:.2f} | {after:.2f} | {improvement:.2f}% | {uses_index} |\n")
            
            # Résumé
            total_before = sum(q['avg_time'] for q in self.results['before'].values())
            total_after = sum(q['avg_time'] for q in self.results['after'].values())
            total_improvement = ((total_before - total_after) / total_before) * 100 if total_before > 0 else 0
            
            f.write(f"\n## Résumé\n\n")
            f.write(f"- Temps total avant optimisation: {total_before:.2f} ms\n")
            f.write(f"- Temps total après optimisation: {total_after:.2f} ms\n")
            f.write(f"- Amélioration globale: {total_improvement:.2f}%\n")
        
        print(f"\nRapport généré: {RESULTS_FILE}")
    
    def run_optimization(self):
        """Exécute le processus complet d'optimisation des index"""
        print("Démarrage de l'optimisation des index...")
        
        # Mesurer les performances avant optimisation
        self.measure_all_queries('before')
        
        # Créer les index
        self.create_indexes()
        
        # Mesurer les performances après optimisation
        self.measure_all_queries('after')
        
        # Générer le rapport
        self.generate_report()
        
        print("\nOptimisation des index terminée avec succès!")

def main():
    """Fonction principale"""
    app = create_app()
    
    with app.app_context():
        optimizer = IndexOptimizer()
        optimizer.run_optimization()

if __name__ == "__main__":
    main()
