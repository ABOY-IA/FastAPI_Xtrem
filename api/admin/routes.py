from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from loguru import logger
from typing import List
from api.db.session import SessionLocal
from api.db.models import User
from api.db.schemas import UserOut  # Schéma de sortie pour un utilisateur

router = APIRouter()

# Dépendance pour obtenir une session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dépendance simplifiée pour authentifier un administrateur via le header "X-User"
def get_admin_user(x_user: str = Header(...), db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.username == x_user).first()
    if not user or user.role != "admin":
        logger.warning(f"Admin access denied for username '{x_user}'.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin access required")
    return user

@router.get("/users", response_model=List[UserOut], tags=["Admin"])
def list_all_users(db: Session = Depends(get_db), admin_user: User = Depends(get_admin_user)):
    """
    Liste tous les utilisateurs.
    Accessible uniquement aux administrateurs.
    """
    users = db.query(User).all()
    logger.info(f"Admin '{admin_user.username}' retrieved {len(users)} users.")
    return users
