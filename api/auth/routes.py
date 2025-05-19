import os
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.core.tokens import create_access_token
from api.db.session import SessionLocal
from api.db.services import get_user_by_username
from api.core.crypto import encrypt_sensitive_data, decrypt_sensitive_data

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
refresh_token_scheme = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY","secret")
ALGORITHM = os.getenv("ALGORITHM","HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES","30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS","7"))

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

@router.post("/refresh", tags=["Auth"])
async def refresh_and_rotate_token(
    credentials: HTTPAuthorizationCredentials = Depends(refresh_token_scheme),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid token type")
        username = payload.get("sub")
        role = payload.get("role")
        scopes = payload.get("scopes", [])
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user or not user.sensitive_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found or no stored refresh token")

    stored = decrypt_sensitive_data(user.sensitive_data.encrypted_refresh_token, user.encryption_key)
    if stored != token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Refresh token mismatch")

    # nouvel access + refresh
    new_access = create_access_token(
        data={"sub":username,"role":role,"scopes":scopes},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    new_refresh = create_access_token(
        data={"sub":username,"role":role,"scopes":scopes,"type":"refresh"},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    user.sensitive_data.encrypted_refresh_token = encrypt_sensitive_data(new_refresh, user.encryption_key)
    await db.commit()
    return {"access_token": new_access, "refresh_token": new_refresh, "token_type":"bearer"}
