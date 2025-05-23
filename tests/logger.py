import os
from loguru import logger
import sys

# Chemin absolu vers le fichier de log partagé
LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'app.log'))

# S'assure que le dossier logs existe (même si lancé depuis un sous-répertoire)
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# Configuration loguru
logger.remove()  # Supprime le handler par défaut
logger.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

# Handler fichier partagé, avec rotation et retention
logger.add(
    LOG_PATH,
    rotation="10 MB",         # Nouveau fichier tous les 10 Mo
    retention="10 days",      # Conserve les logs 10 jours
    level="DEBUG",            # Tout loguer dans le fichier
    enqueue=True,             # Sécurité multiprocess
    backtrace=True,           # Traceback détaillé pour les erreurs
    diagnose=True             # Infos détaillées sur les erreurs
)
