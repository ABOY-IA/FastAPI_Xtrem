import os
from datetime import datetime, timedelta
from jose import jwt

# Récupération des paramètres depuis les variables d'environnement
SECRET_KEY = os.getenv("SECRET_KEY", "mon_secret_default")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Génère un token JWT en encodant les données fournies.
    
    :param data: Dictionnaire contenant les informations à inclure dans le token.
    :param expires_delta: Durée d'expiration du token. Si None, utilise la valeur par défaut.
    :return: Token JWT encodé sous forme de chaîne de caractères.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

