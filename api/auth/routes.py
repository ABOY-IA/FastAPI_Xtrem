import os
import sys
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import AsyncGenerator

from api.core.tokens import create_access_token
from api.db.session import SessionLocal
from api.db.models import User, UserSensitiveData
from api.core.crypto import encrypt_sensitive_data, decrypt_sensitive_data

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
refresh_token_scheme = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

@router.post("/refresh", tags=["Auth"])
async def refresh_and_rotate_token(
    credentials: HTTPAuthorizationCredentials = Depends(refresh_token_scheme),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    # 1. Décodage et vérification du JWT refresh token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        username = payload.get("sub")
        role = payload.get("role")
        scopes = payload.get("scopes", [])
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # 2. Récupération directe du refresh token en base pour debug ultime
    result = await db.execute(
        select(User, UserSensitiveData)
        .join(UserSensitiveData, User.id == UserSensitiveData.user_id)
        .where(User.username == username)
    )
    row = result.first()
    if row:
        user, sensitive_data = row
    else:
        user, sensitive_data = None, None

    print("DEBUG: user =", user, file=sys.stderr, flush=True)
    print("DEBUG: sensitive_data =", sensitive_data, file=sys.stderr, flush=True)
    if sensitive_data:
        print("DEBUG: sensitive_data.encrypted_refresh_token =", sensitive_data.encrypted_refresh_token, file=sys.stderr, flush=True)

    if not user or not sensitive_data or not sensitive_data.encrypted_refresh_token:
        # Ajoute ici un SELECT brut pour voir ce qu'il y a en base
        result2 = await db.execute(
            select(UserSensitiveData).where(UserSensitiveData.user_id == user.id if user else -1)
        )
        sds = result2.scalars().all()
        print("DEBUG: brute SELECT user_sensitive_data for user_id =", user.id if user else None, "->", sds, file=sys.stderr, flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # 3. Logs détaillés pour le debug
    print("DEBUG: user =", user, file=sys.stderr, flush=True)
    print("DEBUG: sensitive_data =", sensitive_data, file=sys.stderr, flush=True)
    if sensitive_data:
        print("DEBUG: sensitive_data.encrypted_refresh_token =", sensitive_data.encrypted_refresh_token, file=sys.stderr, flush=True)

    # 4. Vérification stricte de la présence du refresh token stocké
    if not user or not sensitive_data or not sensitive_data.encrypted_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # 5. Déchiffrement du refresh token stocké
    stored = decrypt_sensitive_data(sensitive_data.encrypted_refresh_token, user.encryption_key)
    print("REFRESH: token reçu =", repr(token), file=sys.stderr, flush=True)
    print("REFRESH: token stocké déchiffré =", repr(stored), file=sys.stderr, flush=True)

    # 6. Comparaison stricte (strip pour éviter les espaces parasites)
    if not stored or stored.strip() != token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    # 7. Génération et stockage des nouveaux tokens
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
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }
