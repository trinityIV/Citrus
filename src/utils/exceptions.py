"""
Exceptions personnalisées pour le projet
"""

class ServiceError(Exception):
    """Exception levée lors d'une erreur avec un service externe"""
    pass

class DownloadError(Exception):
    """Exception levée lors d'une erreur de téléchargement"""
    pass

class AuthenticationError(Exception):
    """Exception levée lors d'une erreur d'authentification"""
    pass

class ValidationError(Exception):
    """Exception levée lors d'une erreur de validation"""
    pass
