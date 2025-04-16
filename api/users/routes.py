from fastapi import APIRouter, HTTPException, Depends, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_
from loguru import logger
from api.db.session import SessionLocal
from api.db.schemas import UserCreate, UserOut, UserLogin
from api.db.services import create_user, authenticate_user, get_password_hash
from api.db.models import User
from api.core.security import create_access_token  # chemin à adapter selon ton projet
from datetime import timedelta

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

# Dépendance simplifiée pour obtenir l'utilisateur courant via un header "X-User"
def get_current_user(db: Session = Depends(get_db), x_user: str = Header(...)):
    user = db.query(User).filter(User.username == x_user).first()
    if not user:
        logger.warning(f"Authentication failed: header 'X-User' value '{x_user}' does not correspond to any user.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
    return user

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["Users"])
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Endpoint d'inscription d'un nouvel utilisateur.
    Vérifie que le username et l'email n'existent pas déjà,
    crée l'utilisateur et enregistre l'activité dans les logs.
    """
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
    Vérifie les identifiants, génère un token JWT si ok, et renvoie le rôle.
    """
    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        logger.warning(f"Failed login attempt for username: '{user.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token_expires = timedelta(minutes=30)  # tu peux le config dans ton settings
    access_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role},  # ce que tu veux mettre dans le token
        expires_delta=access_token_expires
    )

    logger.info(f"User logged in successfully: username='{db_user.username}', id={db_user.id}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": db_user.role,
        "username": db_user.username
    }

@router.post("/logout", tags=["Users"])
def logout():
    """
    Endpoint de déconnexion d'un utilisateur.
    Pour une API REST stateless, la déconnexion se gère côté client.
    On enregistre néanmoins l'événement dans les logs.
    """
    logger.info("User logout requested")
    return {"message": "Logout successful (client should remove tokens)."}

@router.patch("/profile", response_model=UserOut, tags=["Users"])
def update_profile(
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint de mise à jour partielle du profil de l'utilisateur connecté.
    Permet de modifier l'email, le mot de passe et la bio.
    Enregistre dans les logs l'action et renvoie l'utilisateur mis à jour.
    """
    updated = False
    # Mise à jour de l'email si fourni
    if "email" in update_data and update_data["email"]:
        current_user.email = update_data["email"]
        updated = True
    # Mise à jour du mot de passe si fourni
    if "password" in update_data and update_data["password"]:
        current_user.hashed_password = get_password_hash(update_data["password"])
        updated = True
    # Mise à jour de la bio si fourni (assurez-vous que votre modèle User comporte un champ 'bio')
    if "bio" in update_data and update_data["bio"]:
        current_user.bio = update_data["bio"]
        updated = True
    if not updated:
        logger.info(f"No update data provided for user '{current_user.username}'.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
    db.commit()
    db.refresh(current_user)
    logger.info(f"User profile updated successfully: username='{current_user.username}', id={current_user.id}")
    return current_user