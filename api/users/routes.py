from fastapi import APIRouter, HTTPException, Depends, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_
from loguru import logger
from api.db.session import SessionLocal
from api.db.schemas import UserCreate, UserOut, UserLogin
from api.db.services import create_user, authenticate_user, get_password_hash
from api.db.models import User, UserSensitiveData
from api.core import crypto
from api.core.tokens import create_access_token
import os
from datetime import timedelta

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), x_user: str = Header(...)) -> User:
    user = db.query(User).filter(User.username == x_user).first()
    if not user:
        logger.warning(f"Auth failed for X-User '{x_user}'.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
    return user

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(or_(User.username == user.username, User.email == user.email)).first():
        logger.warning(f"Register failed: '{user.username}' or '{user.email}' exists.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")
    new_user = create_user(db, user.username, user.email, user.password)
    # On ne stocke pas la bio en clair dans users
    new_user.bio = None
    db.commit()
    db.refresh(new_user)
    # Chiffrement de la bio
    encrypted_bio = crypto.encrypt_sensitive_data(user.bio or "", new_user.encryption_key)
    sd = UserSensitiveData(user_id=new_user.id, encrypted_bio=encrypted_bio)
    db.add(sd)
    db.commit()
    logger.info(f"User registered: {new_user.username} (id={new_user.id})")
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "bio": user.bio,
        "role": new_user.role
    }

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        logger.warning(f"Failed login: '{user.username}'.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    scopes = ["admin","read:profile","write:profile"] if db_user.role == "admin" else ["read:profile"]
    access_delta = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    access_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role, "scopes": scopes},
        expires_delta=access_delta
    )
    refresh_delta = timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)))
    refresh_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role, "scopes": scopes, "type": "refresh"},
        expires_delta=refresh_delta
    )
    encrypted_rt = crypto.encrypt_sensitive_data(refresh_token, db_user.encryption_key)
    # Stockage du refresh token chiffré
    if db_user.sensitive_data:
        db_user.sensitive_data.encrypted_refresh_token = encrypted_rt
    else:
        from api.db.models import UserSensitiveData
        sd = UserSensitiveData(user_id=db_user.id, encrypted_bio="", encrypted_refresh_token=encrypted_rt)
        db.add(sd)
    db_user.refresh_token = None
    db.commit()
    logger.info(f"User logged in: {db_user.username} (id={db_user.id})")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "username": db_user.username,
        "role": db_user.role
    }

@router.post("/logout")
def logout():
    logger.info("Logout")
    return {"message": "Logout successful"}

@router.get("/profile", response_model=UserOut)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.sensitive_data:
        bio = crypto.decrypt_sensitive_data(current_user.sensitive_data.encrypted_bio or "", current_user.encryption_key)
    else:
        bio = None
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "bio": bio,
        "role": current_user.role
    }

@router.patch("/profile", response_model=UserOut)
def update_profile(
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = False
    if update_data.get("email"):
        current_user.email = update_data["email"]
        updated = True
    if update_data.get("password"):
        current_user.hashed_password = get_password_hash(update_data["password"])
        updated = True
    if "bio" in update_data:
        if current_user.sensitive_data:
            current_user.sensitive_data.encrypted_bio = crypto.encrypt_sensitive_data(update_data["bio"], current_user.encryption_key)
        else:
            from api.db.models import UserSensitiveData
            db.add(UserSensitiveData(
                user_id=current_user.id,
                encrypted_bio=crypto.encrypt_sensitive_data(update_data["bio"], current_user.encryption_key)
            ))
        updated = True
    if not updated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data to update")
    db.commit()
    db.refresh(current_user)
    if current_user.sensitive_data:
        bio = crypto.decrypt_sensitive_data(current_user.sensitive_data.encrypted_bio or "", current_user.encryption_key)
    else:
        bio = None
    logger.info(f"Profile updated: {current_user.username} (id={current_user.id})")
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "bio": bio,
        "role": current_user.role
    }
