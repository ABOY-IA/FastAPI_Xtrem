import os
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
from api.core.tokens import create_access_token
from api.db.session import SessionLocal
from sqlalchemy.orm import Session
from api.db.services import get_user_by_username
from api.core import crypto  # Importation du module crypto pour chiffrer/déchiffrer

router = APIRouter()

# Schéma OAuth2 pour le flow "password" utilisé dans le login (reste inchangé ailleurs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Nouveau schéma HTTPBearer pour l'endpoint refresh, permettant de saisir manuellement le refresh token dans Swagger
refresh_token_scheme = HTTPBearer()

# Paramètres de sécurité
SECRET_KEY = os.getenv("SECRET_KEY", "mon_secret_default")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/refresh", tags=["Auth"])
def refresh_and_rotate_token(
    credentials: HTTPAuthorizationCredentials = Depends(refresh_token_scheme),
    db: Session = Depends(get_db)
):
    """
    Rotation sécurisée des refresh tokens.

    Cet endpoint reçoit un refresh token via le header Authorization
    (grâce à HTTPBearer, Swagger affichera un champ pour le renseigner).

    Le refresh token est décodé et validé (la claim "type" doit être "refresh").
    L'utilisateur est récupéré en base, et on vérifie que le refresh token fourni
    correspond à celui stocké (après déchiffrement depuis la table sensitive).
    Ensuite, un nouveau access token et un nouveau refresh token sont générés,
    le refresh token chiffré en base est mis à jour, et les nouveaux tokens sont renvoyés.
    """
    refresh_token = credentials.credentials
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            logger.warning("Provided token is not a refresh token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        username = payload.get("sub")
        role = payload.get("role")
        scopes = payload.get("scopes", [])
        if username is None:
            logger.warning("Refresh token payload missing 'sub'.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
    except JWTError as e:
        logger.warning(f"Error decoding refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Récupérer l'utilisateur en base
    user = get_user_by_username(db, username)
    if not user:
        logger.warning(f"User '{username}' not found in the database.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Vérifier que l'utilisateur possède un enregistrement sensible
    if not user.sensitive_data or not user.sensitive_data.encrypted_refresh_token:
        logger.warning(f"No stored refresh token for user '{username}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is not valid"
        )
    
    # Déchiffrer le refresh token stocké pour le comparer
    stored_refresh_token = crypto.decrypt_sensitive_data(
        user.sensitive_data.encrypted_refresh_token, user.encryption_key
    )
    if stored_refresh_token != refresh_token:
        logger.warning(f"Refresh token mismatch for user '{username}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is not valid"
        )
    
    # Générer un nouveau access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": username, "role": role, "scopes": scopes},
        expires_delta=access_token_expires
    )
    
    # Générer un nouveau refresh token avec la claim "type": "refresh"
    new_refresh_token = create_access_token(
        data={"sub": username, "role": role, "scopes": scopes, "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    # Chiffrer le nouveau refresh token et le stocker dans la table sensitive
    encrypted_new_refresh_token = crypto.encrypt_sensitive_data(
        new_refresh_token, user.encryption_key
    )
    user.sensitive_data.encrypted_refresh_token = encrypted_new_refresh_token

    # Vider le champ en clair dans la table users pour éviter toute redondance
    user.refresh_token = None
    
    db.commit()
    
    logger.info(f"Refresh token rotated for user '{username}'. New refresh token issued.")
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
