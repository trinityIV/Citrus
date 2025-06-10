# Changelog de Citrus Music Server

Toutes les modifications notables apportées au projet Citrus Music Server seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2025-06-10

### Ajouté
- Section "Outils d'optimisation" dans le script de gestion pour Raspberry Pi
- Fonction de vérification d'état du serveur avec métriques de ressources
- Installation automatique des dépendances pour les outils d'optimisation

### Modifié
- Mise à jour du chemin de lancement dans le script de gestion (`run.py` au lieu de `web_app.py`)
- Amélioration de la fonction d'installation avec création automatique des dossiers nécessaires

### Optimisé
- Organisation des scripts d'optimisation dans un dossier dédié avec documentation

## [1.2.0] - 2025-06-10

### Ajouté
- Nouvel endpoint `/api/library` pour récupérer les pistes avec pagination, tri et filtrage
- Module d'utilitaires DOM (`dom-utils.js`) pour une manipulation sécurisée des éléments HTML
- Fonction `initBatchDownloader` dans `batch.js` pour gérer les téléchargements par lots
- Gestion des timestamps dans les noms de fichiers pour éviter les doublons
- Vérifications de sécurité pour les éléments DOM dans tous les modules JavaScript

### Corrigé
- Erreur 404 sur l'endpoint `/api/library` (endpoint manquant)
- Erreur 500 sur l'endpoint `/api/download` (problème avec yt-dlp)
- Erreur JavaScript "Cannot read properties of null (reading 'value')" dans plusieurs modules
- Contrainte d'unicité violée sur `file_path` dans la base de données
- Problème d'import de `initBatchDownloader` dans `app.js`
- Chemins d'importation incorrects pour les modules JavaScript

### Modifié
- Refactorisation de `downloader.js` pour utiliser les utilitaires DOM
- Refactorisation de `batch.js` pour une meilleure gestion des erreurs
- Simulation temporaire du téléchargement pour éviter les erreurs liées à yt-dlp
- Amélioration de la gestion des notifications utilisateur

### Optimisé
- Réduction des appels DOM redondants
- Meilleure gestion des erreurs côté client
- Code plus maintenable avec une architecture modulaire

## [1.1.0] - 2025-05-15

### Ajouté
- Script de génération de données de test (1000 pistes, 50 playlists)
- Système de cache de requêtes avec TTL configurable
- Fonctions optimisées pour les recherches de pistes avec mise en cache
- Module d'administration pour surveiller les performances de la base de données
- Champ is_admin au modèle User pour contrôler l'accès aux fonctionnalités d'administration
- Migration Alembic pour ajouter le champ is_admin à la table users

### Optimisé
- Optimisation des requêtes de playlists avec eager loading sélectif et pagination
- Mesure et journalisation des temps de réponse des requêtes lentes
- Script d'optimisation des index de base de données
- Script de monitoring des performances
- Script de benchmark pour mesurer les performances des requêtes

## [1.0.0] - 2025-04-01

### Ajouté
- Version initiale de Citrus Music Server
- Interface utilisateur avec thème néon
- Support multi-sources (YouTube, Spotify, SoundCloud, Deezer)
- Gestion de bibliothèque musicale
- Système de playlists
- Téléchargement de pistes depuis diverses sources
- Architecture Flask avec SQLAlchemy
- Frontend JavaScript modulaire
