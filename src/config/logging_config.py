import os
import logging
from logging.handlers import RotatingFileHandler

# Création du dossier logs s'il n'existe pas
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Configuration des logs
def setup_logging():
    # Logger principal
    logger = logging.getLogger('citrus')
    logger.setLevel(logging.DEBUG)

    # Format des logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler pour les erreurs (errors.log)
    error_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, 'errors.log'),
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Handler pour les warnings (warnings.log)
    warning_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, 'warnings.log'),
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=5
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(formatter)

    # Handler pour les infos (app.log)
    info_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, 'app.log'),
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=5
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)

    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Ajout des handlers au logger
    logger.addHandler(error_handler)
    logger.addHandler(warning_handler)
    logger.addHandler(info_handler)
    logger.addHandler(console_handler)

    return logger
