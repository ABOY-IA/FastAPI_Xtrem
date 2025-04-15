from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from loguru import logger
from api.db.session import SessionLocal
from api.db.schemas import UserCreate, UserOut, UserLogin
from api.db.services import create_user, authenticate_user
from api.db.models import User

# Configuration de Loguru pour enregistrer tous les logs dans "logs/api.log"
# Rotation quotidienne à 17h15, sans limite de taille, rétention illimitée, et niveau INFO.
logger.add("logs/api.log", rotation="17:15", retention=None, level="INFO", enqueue=True)

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
    """
    Endpoint d'inscription d'un nouvel utilisateur.
    Vérifie que le username et l'email n'existent pas déjà,
    crée l'utilisateur et enregistre l'activité dans les logs.
    """
    # Vérification de l'unicité du username ou de l'email
    if db.query(User).filter(or_(User.username == user.username, User.email == user.email)).first():
        logger.warning(f"Registration failed: username '{user.username}' or email '{user.email}' already exists.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    new_user = create_user(db, user.username, user.email, user.password)
    logger.info(f"User registered successfully: username='{new_user.username}', id={new_user.id}")
    return new_user

@router.post("/login", tags=["Users"])
def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Endpoint de connexion d'un utilisateur.
    Vérifie les identifiants et enregistre dans les logs la tentative de connexion,
    qu'elle soit échouée ou réussie.
    """
    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        logger.warning(f"Failed login attempt for username: '{user.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    logger.info(f"User logged in successfully: username='{db_user.username}', id={db_user.id}")
    return {"message": f"Welcome {db_user.username}!"}

@router.post("/logout", tags=["Users"])
def logout():
    """
    Endpoint de déconnexion d'un utilisateur.
    Pour une API REST stateless, la déconnexion se gère côté client.
    On enregistre néanmoins l'événement dans les logs.
    """
    logger.info("User logout requested")
    return {"message": "Logout successful (client should remove tokens)."}
