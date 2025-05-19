from cryptography.fernet import Fernet, InvalidToken
from typing import Optional

def generate_user_key() -> str:
    """
    Génère une clé de chiffrement unique pour un utilisateur.
    """
    return Fernet.generate_key().decode()

def get_fernet(key: str) -> Fernet:
    return Fernet(key.encode())

def encrypt_sensitive_data(data: str, key: Optional[str]) -> str:
    """
    Chiffre les données sensibles avec la clé propre à l'utilisateur.
    Si aucune clé n'est fournie, renvoie la donnée en clair.
    """
    if not key:
        # Pas de clé d'encryption -> on renvoie la donnée brute
        return data
    fernet = get_fernet(key)
    encrypted = fernet.encrypt(data.encode())
    return encrypted.decode()

def decrypt_sensitive_data(encrypted_data: str, key: Optional[str]) -> str:
    """
    Déchiffre les données sensibles à l'aide de la clé de l'utilisateur.
    Si aucune clé n'est fournie, renvoie la donnée telle quelle.
    Si la donnée est vide ou invalide, retourne une chaîne vide.
    """
    if not key:
        # Pas de clé -> on renvoie l'entrée brute
        return encrypted_data
    if not encrypted_data:
        return ""
    fernet = get_fernet(key)
    try:
        decrypted = fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
    except InvalidToken:
        # Cas où la donnée n'est pas chiffrée ou la clé ne correspond pas
        return ""
