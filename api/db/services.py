from sqlalchemy.orm import Session
from .models import User
from passlib.context import CryptContext
from typing import Optional
from api.core.crypto import generate_user_key

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    role: str = "user",
    encryption_key: Optional[str] = None,
) -> User:
    # 1) Unicité
    if get_user_by_username(db, username):
        raise ValueError(f"Le nom d'utilisateur '{username}' existe déjà.")
    if get_user_by_email(db, email):
        raise ValueError(f"L'email '{email}' existe déjà.")
    # 2) Hash du mot de passe
    hashed_password = get_password_hash(password)
    # 3) Clé d'encryption
    key = encryption_key or generate_user_key()
    # 4) Création de l'utilisateur
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role,
        encryption_key=key,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user