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

def get_current_user(db: Session = Depends(get_db), x_user: str = Header(...)):
    user = db.query(User).filter(User.username == x_user).first()
    if not user:
        logger.warning(f"Header X-User invalid: '{x_user}'")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
    return user

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["Users"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Vérification d'unicité
    if db.query(User).filter(or_(User.username == user.username, User.email == user.email)).first():
        logger.warning(f"Registration failed: '{user.username}' or '{user.email}' already exists.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")

    # Génération clé d'encryption
    encryption_key = crypto.generate_user_key()
    # Création de l'utilisateur avec cette clé
    new_user = create_user(db, user.username, user.email, user.password, encryption_key=encryption_key)

    # Chiffrement de la bio et stockage dans la table sensitive
    if user.bio:
        encrypted_bio = crypto.encrypt_sensitive_data(user.bio, encryption_key)
        sensitive = UserSensitiveData(user_id=new_user.id, encrypted_bio=encrypted_bio)
        db.add(sensitive)
        db.commit()

    logger.info(f"User registered successfully: username='{new_user.username}', id={new_user.id}")
    # Réponse
    return UserOut(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        bio=user.bio,
        role=new_user.role
    )

@router.post("/login", tags=["Users"])
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        logger.warning(f"Failed login for '{user.username}'")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Scopes selon rôle
    scopes = (["admin", "read:profile", "write:profile"]
              if db_user.role == "admin"
              else ["read:profile"])

    # Génération des tokens
    access_exp = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    access_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role, "scopes": scopes},
        expires_delta=access_exp
    )
    refresh_exp = timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)))
    refresh_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role, "scopes": scopes, "type": "refresh"},
        expires_delta=refresh_exp
    )

    # Chiffrement & stockage du refresh token
    encrypted_refresh = crypto.encrypt_sensitive_data(refresh_token, db_user.encryption_key)
    if db_user.sensitive_data:
        db_user.sensitive_data.encrypted_refresh_token = encrypted_refresh
    else:
        sensitive = UserSensitiveData(
            user_id=db_user.id,
            encrypted_bio="",
            encrypted_refresh_token=encrypted_refresh
        )
        db.add(sensitive)
    db.commit()

    logger.info(f"User logged in: username='{db_user.username}', id={db_user.id}, scopes={scopes}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "username": db_user.username,
        "role": db_user.role
    }

@router.post("/logout", tags=["Users"])
def logout():
    logger.info("Logout requested")
    return {"message": "Logout successful (client should remove tokens)."}

@router.get("/profile", response_model=UserOut, tags=["Users"])
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Déchiffre la bio si présente
    bio_plain = None
    if current_user.sensitive_data and current_user.sensitive_data.encrypted_bio:
        bio_plain = crypto.decrypt_sensitive_data(
            current_user.sensitive_data.encrypted_bio,
            current_user.encryption_key
        )
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        bio=bio_plain,
        role=current_user.role
    )

@router.patch("/profile", response_model=UserOut, tags=["Users"])
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
        enc = crypto.encrypt_sensitive_data(update_data["bio"], current_user.encryption_key)
        if current_user.sensitive_data:
            current_user.sensitive_data.encrypted_bio = enc
        else:
            sensitive = UserSensitiveData(user_id=current_user.id, encrypted_bio=enc)
            db.add(sensitive)
        updated = True

    if not updated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    db.commit()
    db.refresh(current_user)

    bio_plain = None
    if current_user.sensitive_data and current_user.sensitive_data.encrypted_bio:
        bio_plain = crypto.decrypt_sensitive_data(
            current_user.sensitive_data.encrypted_bio,
            current_user.encryption_key
        )

    logger.info(f"Profile updated: username='{current_user.username}', id={current_user.id}")
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        bio=bio_plain,
        role=current_user.role
    )
