from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from api.db.session import SessionLocal
from api.db.schemas import UserCreate, UserOut, UserLogin
from api.db.services import create_user, authenticate_user
from api.db.models import User

router = APIRouter()

# Dépendance pour obtenir une session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["Users"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Vérifier que le nom d'utilisateur ou l'email n'existent pas déjà
    if db.query(User).filter((User.username == user.username) | (User.email == user.email)).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    new_user = create_user(db, user.username, user.email, user.password)
    return new_user

@router.post("/login", tags=["Users"])
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    return {"message": f"Welcome {db_user.username}!"}

@router.post("/logout", tags=["Users"])
def logout():
    # Dans une API REST stateless, la déconnexion se gère côté client (en supprimant les tokens)
    return {"message": "Logout successful (client should remove tokens)."}