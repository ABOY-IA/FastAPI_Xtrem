from fastapi import APIRouter, HTTPException, Depends, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_
from sqlalchemy.future import select
from typing import AsyncGenerator

from api.db.session import SessionLocal
from api.db.schemas import UserCreate, UserOut, UserLogin
from api.db.services import create_user, authenticate_user, get_user_by_username
from api.db.models import User, UserSensitiveData
from api.core.crypto import encrypt_sensitive_data, decrypt_sensitive_data
from api.core.tokens import create_access_token
from api.logger import logger
import os
from datetime import timedelta

router = APIRouter()

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

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    x_user: str = Header(...)
) -> User:
    user = await get_user_by_username(db, x_user)
    if not user:
        logger.warning(f"Échec d'authentification de l'utilisateur via header : {x_user}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not authenticated")
    return user

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    exists = await db.execute(
        select(User).where(
            or_(User.username == user.username, User.email == user.email)
        )
    )
    if exists.scalars().first():
        logger.warning(f"Tentative de création d'utilisateur avec username/email déjà utilisé : {user.username}/{user.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username or email already registered")
    new_user = await create_user(db, user.username, user.email, user.password)
    encrypted_bio = encrypt_sensitive_data(user.bio or "", new_user.encryption_key)
    sd = UserSensitiveData(user_id=new_user.id, encrypted_bio=encrypted_bio)
    db.add(sd)
    await db.commit()
    await db.refresh(new_user)
    logger.info(f"Nouvel utilisateur enregistré : {new_user.username} ({new_user.email})")
    return UserOut(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        bio=user.bio,
        role=new_user.role
    )

@router.post("/login")
async def login(
    user: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    db_user = await authenticate_user(db, user.username, user.password)
    if not db_user:
        logger.warning(f"Échec de login pour {user.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid credentials")
    scopes = ["admin", "read:profile", "write:profile"] if db_user.role == "admin" else ["read:profile"]
    access_delta = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    access_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role, "scopes": scopes},
        expires_delta=access_delta
    )
    refresh_delta = timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)))
    refresh_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role,
              "scopes": scopes, "type": "refresh"},
        expires_delta=refresh_delta
    )
    encrypted_rt = encrypt_sensitive_data(refresh_token, db_user.encryption_key)
    if db_user.sensitive_data:
        db_user.sensitive_data.encrypted_refresh_token = encrypted_rt
    else:
        sd = UserSensitiveData(
            user_id=db_user.id,
            encrypted_bio="",
            encrypted_refresh_token=encrypted_rt
        )
        db.add(sd)
    logger.debug(f"LOGIN: refresh_token = {repr(refresh_token)}")
    logger.debug(f"LOGIN: encrypted_rt = {repr(encrypted_rt)}")
    logger.debug(f"LOGIN: db_user.encryption_key = {repr(db_user.encryption_key)}")
    await db.commit()
    await db.refresh(db_user)
    logger.info(f"Utilisateur connecté : {db_user.username}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "username": db_user.username,
        "role": db_user.role
    }

@router.post("/logout")
async def logout():
    logger.info("Déconnexion utilisateur (endpoint appelé)")
    return {"message": "Logout successful"}

@router.get("/profile", response_model=UserOut)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    bio = None
    if current_user.sensitive_data:
        bio = decrypt_sensitive_data(
            current_user.sensitive_data.encrypted_bio,
            current_user.encryption_key
        )
    logger.info(f"Consultation du profil utilisateur : {current_user.username}")
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        bio=bio,
        role=current_user.role
    )
