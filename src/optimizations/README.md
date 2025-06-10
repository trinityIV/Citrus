# Outils d'Optimisation pour Citrus Music Server

Ce dossier contient un ensemble d'outils et de scripts pour optimiser, surveiller et améliorer les performances de Citrus Music Server.

## Scripts disponibles

### 1. Benchmark (`benchmark.py`)

Script de benchmark qui permet de mesurer précisément les performances des requêtes avec et sans optimisations.

**Fonctionnalités :**
- Teste plusieurs types de requêtes fréquentes (recherche par titre, artiste, récupération de playlists, etc.)
- Mesure les temps d'exécution avec et sans cache pour chaque requête
- Calcule le pourcentage d'amélioration apporté par les optimisations
- Génère un rapport détaillé au format Markdown

**Utilisation :**
```bash
python src/optimizations/benchmark.py
```

### 2. Génération de données de test (`generate_test_data.py`)

Script pour générer un jeu de données de test substantiel pour évaluer les performances.

**Fonctionnalités :**
- Génère 1000 pistes musicales aléatoires avec titres, artistes, albums, genres, etc.
- Crée 50 playlists aléatoires associées aux utilisateurs existants
- Associe un nombre aléatoire de pistes à chaque playlist (entre 5 et 100)

**Utilisation :**
```bash
python src/optimizations/generate_test_data.py
```

### 3. Optimisation des index (`optimize_indexes.py`)

Script pour créer et optimiser les index de la base de données.

**Fonctionnalités :**
- Mesure les performances des requêtes avant optimisation
- Crée des index stratégiques sur les colonnes fréquemment utilisées
- Mesure les performances après optimisation pour quantifier les améliorations
- Génère un rapport comparatif

**Utilisation :**
```bash
python src/optimizations/optimize_indexes.py
```

### 4. Monitoring des performances (`performance_monitor.py`)

Script de surveillance des performances de la base de données et des requêtes.

**Fonctionnalités :**
- Mesure les performances des requêtes les plus fréquentes
- Identifie les requêtes lentes dépassant un seuil configurable (actuellement 0.1s)
- Collecte des statistiques sur la base de données (taille, nombre de tables, d'enregistrements, d'index)
- Génère un rapport détaillé au format Markdown avec les métriques de performance
- Crée des graphiques visualisant les temps d'exécution et leur évolution

**Utilisation :**
```bash
python src/optimizations/performance_monitor.py
```

## Modules d'optimisation

Ces scripts utilisent les modules d'optimisation situés dans `src/utils/` :

- **`db_optimizations.py`** : Système de cache de requêtes avec TTL configurable
- **`query_optimizations.py`** : Fonctions optimisées pour les recherches de pistes avec mise en cache

## Utilisation recommandée

1. Commencez par générer des données de test avec `generate_test_data.py`
2. Exécutez `performance_monitor.py` pour établir une référence de performance
3. Optimisez les index avec `optimize_indexes.py`
4. Utilisez `benchmark.py` pour mesurer précisément les améliorations
5. Exécutez régulièrement `performance_monitor.py` pour suivre l'évolution des performances

## Intégration avec l'application

Les optimisations sont automatiquement utilisées par l'application principale via les modules dans `src/utils/`. Aucune configuration supplémentaire n'est nécessaire pour en bénéficier.
