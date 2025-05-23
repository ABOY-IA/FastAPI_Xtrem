import os
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt, JWTError
from api.logger import logger

SECRET_KEY = os.getenv("SECRET_KEY", "mon_secret_default")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login",
    scopes={
        "read:profile": "Permet de lire les informations du profil utilisateur.",
        "write:profile": "Permet de modifier les informations du profil utilisateur.",
        "admin": "Accès complet pour l'administration."
    }
)

def get_current_user_with_scopes(
    security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)
):
    """
    Décode et valide le token JWT pour s'assurer que l'utilisateur possède
    les scopes requis pour accéder à l'endpoint protégé.
    Renvoie un dictionnaire contenant le nom d'utilisateur et les scopes.
    """
    if not token:
        logger.warning("Aucun token JWT fourni")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_scopes = payload.get("scopes", [])
        if username is None:
            logger.warning("Token JWT sans username")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )
        # Vérification que tous les scopes requis sont présents
        for scope in security_scopes.scopes:
            if scope not in token_scopes:
                logger.warning(f"Permission insuffisante : scope manquant {scope}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Missing scope: {scope}",
                    headers={"WWW-Authenticate": f'Bearer scope="{scope}"'}
                )
        return {"username": username, "scopes": token_scopes}
    except JWTError:
        logger.warning("Échec de validation du token JWT")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
            headers={"WWW-Authenticate": "Bearer"}
        )
