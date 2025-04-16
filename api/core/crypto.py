from cryptography.fernet import Fernet
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
    fernet = Fernet(key.encode())
    encrypted = fernet.encrypt(data.encode())
    return encrypted.decode()

def decrypt_sensitive_data(encrypted_data: str, key: str) -> str:
    """
    Déchiffre les données sensibles à l'aide de la clé de l'utilisateur.
    """
    fernet = get_fernet(key)
    decrypted = fernet.decrypt(encrypted_data.encode())
    return decrypted.decode()
