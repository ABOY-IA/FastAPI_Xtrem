import os
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import AsyncGenerator

from api.core.tokens import create_access_token
from api.db.session import SessionLocal
from api.db.models import User, UserSensitiveData
from api.core.crypto import encrypt_sensitive_data, decrypt_sensitive_data
from api.logger import logger

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
refresh_token_scheme = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        request.state.db = session
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Erreur lors de la gestion de la session DB")
            raise
        finally:
            await session.close()

@router.post("/refresh", tags=["Auth"])
async def refresh_and_rotate_token(
    credentials: HTTPAuthorizationCredentials = Depends(refresh_token_scheme),
    db: AsyncSession = Depends(get_db)
):
    logger.debug("/auth/refresh route called")
    token = credentials.credentials
    # 1. Décodage et vérification du JWT refresh token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            logger.warning("Token reçu n'est pas de type refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        username = payload.get("sub")
        role = payload.get("role")
        scopes = payload.get("scopes", [])
        if not username:
            logger.warning("Token refresh sans username")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
    except JWTError as e:
        logger.warning(f"JWTError during refresh decode: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # DEBUG: Affiche tout le contenu de user_sensitive_data avant le JOIN
    result_debug = await db.execute(select(UserSensitiveData))
    all_sensitive_data = result_debug.scalars().all()
    logger.debug(f"ALL user_sensitive_data = {all_sensitive_data}")

    # 2. Récupération de l'utilisateur et de sa sensitive_data via OUTERJOIN
    result = await db.execute(
        select(User, UserSensitiveData)
        .outerjoin(UserSensitiveData, User.id == UserSensitiveData.user_id)
        .where(User.username == username)
    )
    row = result.first()
    if row:
        user, sensitive_data = row
    else:
        user, sensitive_data = None, None
        logger.debug(f"JOIN row is None for username {username}")

    logger.debug(f"user = {user}")
    logger.debug(f"sensitive_data = {sensitive_data}")
    if sensitive_data:
        logger.debug(f"sensitive_data.encrypted_refresh_token = {sensitive_data.encrypted_refresh_token}")

    if not user or not sensitive_data or not sensitive_data.encrypted_refresh_token:
        # SELECT brut pour voir ce qu'il y a pour cet utilisateur
        result2 = await db.execute(
            select(UserSensitiveData).where(UserSensitiveData.user_id == user.id if user else -1)
        )
        sds = result2.scalars().all()
        logger.debug(f"brute SELECT user_sensitive_data for user_id = {user.id if user else None} -> {sds}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # 3. Déchiffrement du refresh token stocké
    stored = decrypt_sensitive_data(sensitive_data.encrypted_refresh_token, user.encryption_key)
    logger.debug(f"REFRESH: token reçu = {repr(token)}")
    logger.debug(f"REFRESH: token stocké déchiffré = {repr(stored)}")

    # 4. Comparaison stricte (strip pour éviter les espaces parasites)
    if not stored or stored.strip() != token.strip():
        logger.warning("Refresh token reçu différent du token stocké")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # 5. Génération et stockage des nouveaux tokens
    new_access = create_access_token(
        data={"sub": username, "role": role, "scopes": scopes},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh = create_access_token(
        data={"sub": username, "role": role, "scopes": scopes, "type": "refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    sensitive_data.encrypted_refresh_token = encrypt_sensitive_data(new_refresh, user.encryption_key)
    await db.commit()
    logger.info(f"Refresh token rotaté pour l'utilisateur {username}")
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }
