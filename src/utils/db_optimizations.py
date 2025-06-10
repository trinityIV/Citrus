"""
Utilitaires pour l'optimisation des requêtes de base de données
"""

import time
import functools
import logging
from typing import Dict, Any, Optional, Callable, TypeVar, List, Tuple
from flask import g, current_app
from sqlalchemy import text
from sqlalchemy.orm import Query, joinedload, contains_eager, load_only
from ..database import db_session

logger = logging.getLogger(__name__)

# Type générique pour les fonctions décorées
T = TypeVar('T')

class QueryCache:
    """
    Gestionnaire de cache pour les requêtes SQL fréquentes
    """
    
    def __init__(self, max_size: int = 100, ttl: int = 60):
        """
        Initialise le cache avec une taille maximale et un TTL
        
        Args:
            max_size: Nombre maximum d'entrées dans le cache
            ttl: Durée de vie des entrées en secondes
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache si elle existe et n'est pas expirée
        
        Args:
            key: Clé de l'entrée à récupérer
            
        Returns:
            La valeur associée à la clé ou None si elle n'existe pas ou est expirée
        """
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self.hits += 1
                return value
            else:
                # Supprimer l'entrée expirée
                del self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Ajoute ou met à jour une entrée dans le cache
        
        Args:
            key: Clé de l'entrée
            value: Valeur à associer à la clé
        """
        # Si le cache est plein, supprimer l'entrée la plus ancienne
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.items(), key=lambda x: x[1][1])[0]
            del self.cache[oldest_key]
        
        self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Vide le cache"""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur l'utilisation du cache
        
        Returns:
            Un dictionnaire contenant les statistiques du cache
        """
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'ttl': self.ttl
        }


# Cache global pour les requêtes
query_cache = QueryCache()


def cached_query(ttl: int = 60) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Décorateur pour mettre en cache le résultat d'une fonction de requête
    
    Args:
        ttl: Durée de vie du cache en secondes
        
    Returns:
        Le décorateur configuré avec le TTL spécifié
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Générer une clé de cache unique basée sur la fonction et ses arguments
            cache_key = f"{func.__module__}.{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Vérifier si le résultat est déjà en cache
            cached_result = query_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Exécuter la fonction et mettre le résultat en cache
            result = func(*args, **kwargs)
            query_cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator


def optimize_query(query: Query, model_class: Any, select_columns: Optional[List[str]] = None) -> Query:
    """
    Optimise une requête SQLAlchemy en sélectionnant uniquement les colonnes nécessaires
    
    Args:
        query: La requête SQLAlchemy à optimiser
        model_class: La classe du modèle principal de la requête
        select_columns: Liste des noms de colonnes à sélectionner (None pour toutes)
        
    Returns:
        La requête optimisée
    """
    if select_columns:
        # Convertir les noms de colonnes en objets Column
        columns = [getattr(model_class, col) for col in select_columns]
        query = query.options(load_only(*columns))
    
    return query


def get_db_stats() -> Dict[str, Any]:
    """
    Récupère des statistiques sur la base de données
    
    Returns:
        Un dictionnaire contenant les statistiques de la base de données
    """
    stats = {}
    
    try:
        # Nombre total de tables
        result = db_session.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
        stats['table_count'] = result.scalar()
        
        # Taille de la base de données (SQLite)
        result = db_session.execute(text("PRAGMA page_count"))
        page_count = result.scalar()
        
        result = db_session.execute(text("PRAGMA page_size"))
        page_size = result.scalar()
        
        stats['db_size'] = page_count * page_size
        
        # Statistiques par table
        tables = db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).scalars().all()
        table_stats = {}
        
        for table in tables:
            if table.startswith('sqlite_'):
                continue
                
            row_count = db_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            table_stats[table] = {'row_count': row_count}
        
        stats['tables'] = table_stats
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques de la base de données: {str(e)}")
    
    return stats


def optimize_db() -> Dict[str, Any]:
    """
    Optimise la base de données SQLite
    
    Returns:
        Un dictionnaire contenant les résultats de l'optimisation
    """
    results = {}
    
    try:
        # Analyser la base de données
        db_session.execute(text("ANALYZE"))
        results['analyze'] = True
        
        # Optimiser les index
        db_session.execute(text("PRAGMA optimize"))
        results['optimize'] = True
        
        # Vider le cache de requêtes
        query_cache.clear()
        results['cache_cleared'] = True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'optimisation de la base de données: {str(e)}")
        results['error'] = str(e)
    
    return results
