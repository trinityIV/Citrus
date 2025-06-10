#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de monitoring des performances pour Citrus Music Server
Mesure les performances des requêtes et génère un rapport détaillé
"""

import os
import sys
import time
import sqlite3
import datetime
import json
import matplotlib.pyplot as plt
from collections import defaultdict

# Ajouter le répertoire parent au path pour pouvoir importer les modules du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'citrus.db')
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'performance_reports')
SLOW_QUERY_THRESHOLD = 0.1  # secondes
HISTORY_FILE = os.path.join(RESULTS_DIR, 'performance_history.json')

# Requêtes à surveiller
MONITORED_QUERIES = [
    {
        'name': 'Récupération de la bibliothèque',
        'query': 'SELECT * FROM track ORDER BY title LIMIT 100',
        'params': ()
    },
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
        'name': 'Playlists utilisateur',
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
        'name': 'Statistiques globales',
        'query': '''
            SELECT 
                (SELECT COUNT(*) FROM track) as track_count,
                (SELECT COUNT(*) FROM playlist) as playlist_count,
                (SELECT COUNT(*) FROM user) as user_count,
                (SELECT SUM(duration) FROM track) as total_duration
        ''',
        'params': ()
    }
]

class PerformanceMonitor:
    """Classe pour surveiller les performances de la base de données"""
    
    def __init__(self):
        """Initialisation du moniteur de performances"""
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.results = {}
        self.db_stats = {}
        self.slow_queries = []
        
        # Créer le répertoire de résultats s'il n'existe pas
        os.makedirs(RESULTS_DIR, exist_ok=True)
    
    def get_db_statistics(self):
        """Récupère des statistiques sur la base de données"""
        print("Collecte des statistiques de la base de données...")
        
        # Taille de la base de données
        db_size = os.path.getsize(DB_PATH) / (1024 * 1024)  # en MB
        
        # Nombre de tables
        self.cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
        table_count = self.cursor.fetchone()[0]
        
        # Nombre d'index
        self.cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='index'")
        index_count = self.cursor.fetchone()[0]
        
        # Statistiques par table
        tables = []
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for row in self.cursor.fetchall():
            table_name = row[0]
            if table_name.startswith('sqlite_'):
                continue
                
            self.cursor.execute(f"SELECT count(*) FROM {table_name}")
            row_count = self.cursor.fetchone()[0]
            
            # Récupérer les informations sur les colonnes
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [dict(row) for row in self.cursor.fetchall()]
            
            # Récupérer les index de la table
            self.cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = [dict(row) for row in self.cursor.fetchall()]
            
            tables.append({
                'name': table_name,
                'row_count': row_count,
                'column_count': len(columns),
                'index_count': len(indexes)
            })
        
        self.db_stats = {
            'size_mb': db_size,
            'table_count': table_count,
            'index_count': index_count,
            'tables': tables
        }
        
        print(f"  Taille de la base: {db_size:.2f} MB")
        print(f"  Nombre de tables: {table_count}")
        print(f"  Nombre d'index: {index_count}")
    
    def measure_query_performance(self, query_info, iterations=3):
        """Mesure les performances d'une requête"""
        query = query_info['query']
        params = query_info['params']
        name = query_info['name']
        
        print(f"  Mesure de '{name}'...")
        
        # Exécuter EXPLAIN QUERY PLAN pour voir si des index sont utilisés
        self.cursor.execute(f"EXPLAIN QUERY PLAN {query}", params)
        plan = self.cursor.fetchall()
        uses_index = any('USING INDEX' in str(row) for row in plan)
        
        # Mesurer le temps d'exécution
        times = []
        for i in range(iterations):
            start_time = time.time()
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            end_time = time.time()
            execution_time = end_time - start_time
            times.append(execution_time)
            
            # Vérifier si c'est une requête lente
            if execution_time > SLOW_QUERY_THRESHOLD:
                self.slow_queries.append({
                    'name': name,
                    'time': execution_time,
                    'query': query,
                    'iteration': i + 1
                })
        
        avg_time = sum(times) / len(times)
        result_count = len(results) if results else 0
        
        return {
            'avg_time': avg_time,
            'min_time': min(times),
            'max_time': max(times),
            'uses_index': uses_index,
            'result_count': result_count,
            'is_slow': avg_time > SLOW_QUERY_THRESHOLD
        }
    
    def monitor_all_queries(self):
        """Mesure les performances de toutes les requêtes surveillées"""
        print("\nSurveillance des performances des requêtes...")
        
        for query_info in MONITORED_QUERIES:
            name = query_info['name']
            result = self.measure_query_performance(query_info)
            self.results[name] = result
            
            status = "LENT" if result['is_slow'] else "OK"
            print(f"    {name}: {result['avg_time']:.4f}s ({status})")
    
    def update_history(self):
        """Met à jour l'historique des performances"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        history_data = {}
        
        # Charger l'historique existant s'il existe
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                try:
                    history_data = json.load(f)
                except json.JSONDecodeError:
                    history_data = {}
        
        # Ajouter les données d'aujourd'hui
        history_data[today] = {
            'db_size_mb': self.db_stats['size_mb'],
            'queries': {name: result['avg_time'] for name, result in self.results.items()}
        }
        
        # Sauvegarder l'historique
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history_data, f, indent=2)
    
    def generate_charts(self):
        """Génère des graphiques de performance"""
        if not os.path.exists(HISTORY_FILE):
            print("Pas d'historique disponible pour générer des graphiques")
            return
        
        with open(HISTORY_FILE, 'r') as f:
            history_data = json.load(f)
        
        # Extraire les dates et les données
        dates = sorted(history_data.keys())
        if len(dates) < 2:
            print("Pas assez de données historiques pour générer des graphiques")
            return
        
        # Graphique de la taille de la base de données
        plt.figure(figsize=(10, 6))
        db_sizes = [history_data[date]['db_size_mb'] for date in dates]
        plt.plot(dates, db_sizes, marker='o')
        plt.title('Évolution de la taille de la base de données')
        plt.xlabel('Date')
        plt.ylabel('Taille (MB)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, 'db_size_evolution.png'))
        
        # Graphique des temps de requête
        plt.figure(figsize=(12, 8))
        query_names = list(history_data[dates[0]]['queries'].keys())
        
        for query_name in query_names:
            query_times = [history_data[date]['queries'].get(query_name, 0) for date in dates]
            plt.plot(dates, query_times, marker='o', label=query_name)
        
        plt.title('Évolution des temps de requête')
        plt.xlabel('Date')
        plt.ylabel('Temps (secondes)')
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, 'query_times_evolution.png'))
        
        print(f"Graphiques générés dans le dossier {RESULTS_DIR}")
    
    def generate_report(self):
        """Génère un rapport détaillé au format Markdown"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_file = os.path.join(RESULTS_DIR, f"performance_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Rapport de Performance - Citrus Music Server\n\n")
            f.write(f"Date: {now}\n\n")
            
            # Statistiques de la base de données
            f.write(f"## Statistiques de la base de données\n\n")
            f.write(f"- **Taille**: {self.db_stats['size_mb']:.2f} MB\n")
            f.write(f"- **Tables**: {self.db_stats['table_count']}\n")
            f.write(f"- **Index**: {self.db_stats['index_count']}\n\n")
            
            f.write(f"### Détails des tables\n\n")
            f.write(f"| Table | Lignes | Colonnes | Index |\n")
            f.write(f"|-------|--------|----------|-------|\n")
            
            for table in self.db_stats['tables']:
                f.write(f"| {table['name']} | {table['row_count']} | {table['column_count']} | {table['index_count']} |\n")
            
            # Performances des requêtes
            f.write(f"\n## Performances des requêtes\n\n")
            f.write(f"| Requête | Temps moyen (s) | Min (s) | Max (s) | Résultats | Utilise index | Status |\n")
            f.write(f"|---------|-----------------|---------|---------|-----------|--------------|--------|\n")
            
            for name, result in self.results.items():
                status = "⚠️ LENT" if result['is_slow'] else "✅ OK"
                uses_index = "✅" if result['uses_index'] else "❌"
                
                f.write(f"| {name} | {result['avg_time']:.4f} | {result['min_time']:.4f} | {result['max_time']:.4f} | {result['result_count']} | {uses_index} | {status} |\n")
            
            # Requêtes lentes
            if self.slow_queries:
                f.write(f"\n## Requêtes lentes détectées\n\n")
                f.write(f"Seuil: {SLOW_QUERY_THRESHOLD} secondes\n\n")
                
                for i, query in enumerate(self.slow_queries):
                    f.write(f"### {i+1}. {query['name']} ({query['time']:.4f}s)\n\n")
                    f.write(f"```sql\n{query['query']}\n```\n\n")
            
            # Recommandations
            f.write(f"\n## Recommandations\n\n")
            
            if self.slow_queries:
                f.write(f"1. **Optimiser les requêtes lentes** identifiées ci-dessus\n")
                f.write(f"2. **Ajouter des index** pour les requêtes qui n'en utilisent pas\n")
            else:
                f.write(f"✅ Toutes les requêtes surveillées s'exécutent en dessous du seuil de {SLOW_QUERY_THRESHOLD} secondes\n")
            
            # Si des graphiques ont été générés
            if os.path.exists(os.path.join(RESULTS_DIR, 'db_size_evolution.png')):
                f.write(f"\n## Graphiques\n\n")
                f.write(f"### Évolution de la taille de la base de données\n\n")
                f.write(f"![Taille de la base](./db_size_evolution.png)\n\n")
                
                f.write(f"### Évolution des temps de requête\n\n")
                f.write(f"![Temps de requête](./query_times_evolution.png)\n\n")
        
        print(f"\nRapport généré: {report_file}")
    
    def run_monitoring(self):
        """Exécute le processus complet de monitoring des performances"""
        print("Démarrage du monitoring des performances...")
        
        # Collecter les statistiques de la base de données
        self.get_db_statistics()
        
        # Mesurer les performances des requêtes
        self.monitor_all_queries()
        
        # Mettre à jour l'historique
        self.update_history()
        
        # Générer des graphiques si des données historiques sont disponibles
        self.generate_charts()
        
        # Générer le rapport
        self.generate_report()
        
        print("\nMonitoring des performances terminé avec succès!")

def main():
    """Fonction principale"""
    app = create_app()
    
    with app.app_context():
        monitor = PerformanceMonitor()
        monitor.run_monitoring()

if __name__ == "__main__":
    main()
