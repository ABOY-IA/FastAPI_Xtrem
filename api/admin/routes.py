from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from loguru import logger
from typing import List
from api.db.session import SessionLocal
from api.db.models import User
from api.db.schemas import UserOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_admin_user(x_user: str = Header(...), db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.username == x_user).first()
    if not user or user.role != "admin":
        logger.warning(f"Admin access denied for '{x_user}'.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin access required")
    return user

@router.get("/users", response_model=List[UserOut])
def list_all_users(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    users = db.query(User).all()
    logger.info(f"Admin '{admin.username}' retrieved {len(users)} users.")
    return [
        {"id": u.id, "username": u.username, "email": u.email, "bio": None, "role": u.role}
        for u in users
    ]

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    db.delete(user)
    db.commit()
    