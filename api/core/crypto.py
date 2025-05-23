from cryptography.fernet import Fernet, InvalidToken
from typing import Optional
from api.logger import logger

def generate_user_key() -> str:
    """Génère une clé de chiffrement unique pour un utilisateur."""
    key = Fernet.generate_key().decode()
    logger.debug("Nouvelle clé de chiffrement générée pour un utilisateur")
    return key

def get_fernet(key: str) -> Fernet:
    return Fernet(key.encode())

def encrypt_sensitive_data(data: str, key: Optional[str]) -> str:
    """
    Chiffre les données sensibles avec la clé propre à l'utilisateur.
    Si aucune clé n'est fournie, renvoie la donnée en clair.
    """
    if not key:
        logger.debug("Aucune clé d'encryption fournie, donnée non chiffrée")
        return data
    fernet = get_fernet(key)
    encrypted = fernet.encrypt(data.encode())
    logger.debug("Donnée sensible chiffrée")
    return encrypted.decode()

def decrypt_sensitive_data(encrypted_data: str, key: Optional[str]) -> str:
    """
    Déchiffre les données sensibles à l'aide de la clé de l'utilisateur.
    Si aucune clé n'est fournie, renvoie la donnée telle quelle.
    Si la donnée est vide ou invalide, retourne une chaîne vide.
    """
    if not key:
        logger.debug("Aucune clé fournie pour le déchiffrement, donnée renvoyée brute")
        return encrypted_data
    if not encrypted_data:
        logger.debug("Donnée chiffrée vide reçue")
        return ""
    fernet = get_fernet(key)
    try:
        decrypted = fernet.decrypt(encrypted_data.encode())
        logger.debug("Donnée sensible déchiffrée")
        return decrypted.decode()
    except InvalidToken:
        logger.warning("Échec du déchiffrement : clé invalide ou donnée non chiffrée")
        return ""
