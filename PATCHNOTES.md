# Notes de Patch - Citrus Music Server

## Version 1.2.1 (10 juin 2025)

### Améliorations du script de gestion pour Raspberry Pi

- **Ajout d'une section "Outils d'optimisation"** dans le menu principal
  - Génération de données de test (1000 pistes, 50 playlists)
  - Optimisation des index de base de données
  - Benchmark de performances
  - Génération de rapports de monitoring

- **Nouvelle fonction de vérification d'état du serveur**
  - Affichage de l'état du processus (en cours d'exécution ou non)
  - Vérification de la réponse du serveur web
  - Affichage de l'utilisation des ressources (CPU, mémoire)
  - Vérification de l'espace disque disponible

- **Mise à jour de la fonction d'installation**
  - Ajout des dépendances pour les outils d'optimisation (matplotlib, numpy)
  - Installation de yt-dlp pour corriger les problèmes de téléchargement
  - Création automatique des dossiers nécessaires pour les rapports

- **Correction du chemin de lancement**
  - Mise à jour du chemin pour lancer l'application (`run.py` au lieu de `web_app.py`)

## Version 1.2.0 (10 juin 2025)

### Corrections de bugs critiques

#### 1. Endpoint `/api/library` manquant
- **Problème** : L'endpoint `/api/library` était manquant, causant des erreurs 404 côté client.
- **Solution** : Ajout d'un nouvel endpoint dans `api.py` avec les fonctionnalités suivantes :
  - Pagination des résultats (paramètres `limit` et `offset`)
  - Tri des pistes (paramètres `sort` et `order`)
  - Filtrage par artiste, album, etc.
  - Gestion des erreurs et journalisation

```python
@api_bp.route('/api/library', methods=['GET'])
@login_required
def get_library():
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    sort_by = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    # ...
```

#### 2. Erreur 500 sur l'endpoint `/api/download`
- **Problème** : Utilisation de `yt-dlp` non installé ou mal configuré, causant une erreur `WinError 2`.
- **Solution temporaire** : Simulation du téléchargement en créant un fichier audio vide et en insérant la piste en base.
- **Problème secondaire** : Contrainte d'unicité sur `file_path` violée.
- **Solution** : Ajout d'un timestamp dans le nom de fichier pour garantir l'unicité.

```python
# Générer un nom de fichier sécurisé avec timestamp pour éviter les doublons
import time
timestamp = int(time.time())
filename = secure_filename(f"{artist} - {title} - {timestamp}.mp3")
```

#### 3. Erreur JavaScript "Cannot read properties of null (reading 'value')"
- **Problème** : Accès à des éléments DOM qui peuvent ne pas exister.
- **Solution** : 
  - Création d'un module d'utilitaires DOM (`dom-utils.js`)
  - Refactorisation des modules JavaScript pour utiliser ces utilitaires
  - Ajout de vérifications de sécurité avant d'accéder aux propriétés des éléments

```javascript
// Avant
const url = document.getElementById('downloadUrl').value;

// Après
const url = getElementValue('downloadUrl');
```

#### 4. Fonction `initBatchDownloader` manquante
- **Problème** : La fonction était importée dans `app.js` mais non définie dans `batch.js`.
- **Solution** : Implémentation de la fonction dans `batch.js` pour gérer le formulaire de téléchargement par lots.

### Améliorations techniques

#### 1. Architecture JavaScript modulaire
- Création d'un module d'utilitaires DOM (`dom-utils.js`) avec les fonctions suivantes :
  - `getElement(id, required)` : Récupère un élément DOM de manière sécurisée
  - `getElementValue(id, defaultValue)` : Récupère la valeur d'un élément de formulaire
  - `setElementValue(id, value)` : Définit la valeur d'un élément de formulaire
  - `setElementText(id, text)` : Définit le contenu texte d'un élément
  - `setElementVisibility(id, visible)` : Affiche ou masque un élément
  - `addEventHandler(id, event, handler)` : Ajoute un gestionnaire d'événements

#### 2. Gestion des chemins d'importation
- Correction des chemins d'importation pour les modules JavaScript
- Utilisation de chemins absolus pour éviter les erreurs 404

```javascript
// Avant
import { ... } from '../dom-utils.js';

// Après
import { ... } from '/static/js/dom-utils.js';
```

#### 3. Gestion des doublons dans la base de données
- Vérification de l'existence d'une piste avant insertion
- Retour des informations existantes sans erreur si la piste existe déjà

```python
# Vérifier si une piste avec ce chemin existe déjà
existing_track = Track.query.filter_by(file_path=destination).first()
if existing_track:
    return jsonify({
        'success': True,
        'message': 'Piste déjà téléchargée',
        'track': {
            'id': existing_track.id,
            'title': existing_track.title,
            'artist': existing_track.artist,
            'file_path': existing_track.file_path
        }
    })
```

### Prochaines étapes recommandées

1. **Intégrer yt-dlp correctement** pour le téléchargement réel, avec gestion des erreurs et permissions
2. **Ajouter des tests automatisés** pour les endpoints API et le frontend
3. **Améliorer la gestion des erreurs côté client** pour une meilleure expérience utilisateur
4. **Optimiser les requêtes de bibliothèque** pour les grandes collections
5. **Implémenter un système de mise en cache des requêtes API** pour améliorer les performances

---

## Version 1.1.0 (15 mai 2025)

### Optimisations de base de données
- Système de cache de requêtes avec TTL configurable (`db_optimizations.py`)
- Fonctions optimisées pour les recherches de pistes avec mise en cache (`query_optimizations.py`)
- Optimisation des requêtes de playlists avec eager loading sélectif et pagination
- Module d'administration pour surveiller les performances de la base de données
- Ajout du champ `is_admin` au modèle User pour contrôler l'accès aux fonctionnalités d'administration
- Migration Alembic pour ajouter le champ `is_admin` à la table users
- Mesure et journalisation des temps de réponse des requêtes lentes

### Scripts d'optimisation
- Script de génération de données de test (1000 pistes, 50 playlists)
- Script d'optimisation des index de base de données
- Script de monitoring des performances
- Script de benchmark pour mesurer les performances des requêtes

---

## Version 1.0.0 (1er avril 2025)

Version initiale de Citrus Music Server.
