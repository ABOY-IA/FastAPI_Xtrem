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
    crée l'utilisateur, génère une clé unique de chiffrement,
    chiffre la bio et stocke celle-ci dans la table dédiée.
    """
    if db.query(User).filter(or_(User.username == user.username, User.email == user.email)).first():
        logger.warning(f"Registration failed: username '{user.username}' or email '{user.email}' already exists.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    # Création de l'utilisateur via le service existant (mot de passe à hasher en production)
    new_user = create_user(db, user.username, user.email, user.password)
    
    # Génération de la clé de chiffrement unique pour l'utilisateur
    encryption_key = crypto.generate_user_key()
    new_user.encryption_key = encryption_key

    # IMPORTANT : pour garantir que la donnée sensible ne reste pas en clair dans la table users,
    # on vide le champ bio dans l'enregistrement principal.
    new_user.bio = None
    db.commit()
    db.refresh(new_user)

    # Chiffrement de la bio et création de l'enregistrement dans la table user_sensitive_data
    encrypted_bio = crypto.encrypt_sensitive_data(user.bio, encryption_key)
    sensitive_data = UserSensitiveData(user_id=new_user.id, encrypted_bio=encrypted_bio)
    db.add(sensitive_data)
    db.commit()
    logger.info(f"User registered successfully: username='{new_user.username}', id={new_user.id}")
    
    # Construction de la réponse : on renvoie la bio en clair (comme donnée initiale)
    response = {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "bio": user.bio,  # La bio en clair, pour la réponse uniquement
        "role": new_user.role
    }
    return response

@router.post("/login", tags=["Users"])
def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Endpoint de connexion d'un utilisateur.
    Vérifie les identifiants et génère deux tokens JWT :
      - Un access token à durée courte pour authentifier les requêtes.
      - Un refresh token à durée plus longue pour renouveler l'access token, ici chiffré et stocké dans la table sensitive.
    Les scopes sont définis en fonction du rôle de l'utilisateur :
      - Admin : ["admin", "read:profile", "write:profile"]
      - Utilisateur classique : ["read:profile"]
    Le refresh token est stocké en base pour permettre sa rotation sécurisée.
    """
    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        logger.warning(f"Failed login attempt for username: '{user.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Définir les scopes en fonction du rôle
    scopes = ["admin", "read:profile", "write:profile"] if db_user.role == "admin" else ["read:profile"]

    # Génération du token d'accès (durée courte)
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    access_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role, "scopes": scopes},
        expires_delta=access_token_expires
    )

    # Génération du refresh token (durée plus longue), avec la claim "type": "refresh"
    refresh_token_expires = timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)))
    refresh_token = create_access_token(
        data={"sub": db_user.username, "role": db_user.role, "scopes": scopes, "type": "refresh"},
        expires_delta=refresh_token_expires
    )

    # Chiffrer le refresh token avec la clé de l'utilisateur
    encrypted_refresh_token = crypto.encrypt_sensitive_data(refresh_token, db_user.encryption_key)
    
    # Stocker le refresh token chiffré dans la table sensitive
    if db_user.sensitive_data:
        db_user.sensitive_data.encrypted_refresh_token = encrypted_refresh_token
    else:
        # Si l'enregistrement n'existe pas encore (ce qui est rare si la création est faite à l'inscription)
        from api.db.models import UserSensitiveData
        sensitive_data = UserSensitiveData(
            user_id=db_user.id,
            encrypted_bio="",
            encrypted_refresh_token=encrypted_refresh_token
        )
        db.add(sensitive_data)
    
    db_user.refresh_token = None # On ne stocke pas le refresh token en clair dans la table users
    db.commit()

    logger.info(f"User logged in successfully: username='{db_user.username}', id={db_user.id}. Scopes: {scopes}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout", tags=["Users"])
def logout():
    """
    Endpoint de déconnexion d'un utilisateur.
    La déconnexion se gère côté client, on enregistre simplement l'action dans les logs.
    """
    logger.info("User logout requested")
    return {"message": "Logout successful (client should remove tokens)."}

@router.get("/profile", response_model=UserOut, tags=["Users"])
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint pour récupérer le profil de l'utilisateur connecté.
    La bio est déchiffrée à l'aide de la clé de chiffrement de l'utilisateur.
    """
    # Si l'utilisateur dispose d'une donnée sensible enregistrée, déchiffrez la bio
    if current_user.sensitive_data:
        decrypted_bio = crypto.decrypt_sensitive_data(current_user.sensitive_data.encrypted_bio, current_user.encryption_key)
        current_user.bio = decrypted_bio
    else:
        current_user.bio = None
    return current_user

@router.patch("/profile", response_model=UserOut, tags=["Users"])
def update_profile(
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint de mise à jour partielle du profil de l'utilisateur connecté.
    Permet de modifier l'email, le mot de passe et la bio.
    Pour la bio, la nouvelle valeur est chiffrée et stockée dans la table dédiée.
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
    # Mise à jour de la bio si fournie
    if "bio" in update_data and update_data["bio"]:
        # Mettre à jour ou créer l'enregistrement de la donnée sensible
        if current_user.sensitive_data:
            current_user.sensitive_data.encrypted_bio = crypto.encrypt_sensitive_data(update_data["bio"], current_user.encryption_key)
        else:
            from api.db.models import UserSensitiveData  # Au cas où il n'y avait pas de bio renseignée
            sensitive_data = UserSensitiveData(user_id=current_user.id, encrypted_bio=crypto.encrypt_sensitive_data(update_data["bio"], current_user.encryption_key))
            db.add(sensitive_data)
        updated = True

    if not updated:
        logger.info(f"No update data provided for user '{current_user.username}'.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    db.commit()
    db.refresh(current_user)
    
    # Pour la réponse, on déchiffre la bio depuis la table dédiée
    if current_user.sensitive_data:
        decrypted_bio = crypto.decrypt_sensitive_data(current_user.sensitive_data.encrypted_bio, current_user.encryption_key)
        current_user.bio = decrypted_bio
    else:
        current_user.bio = None

    logger.info(f"User profile updated successfully: username='{current_user.username}', id={current_user.id}")
    return current_user
