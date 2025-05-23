from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from api.db.models import User
from api.core.crypto import generate_user_key
import bcrypt
from api.logger import logger

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    logger.debug("Mot de passe hashé")
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    result = bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    logger.debug(f"Vérification du mot de passe : {'succès' if result else 'échec'}")
    return result

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.sensitive_data))
        .where(User.username == username)
    )
    user = result.scalars().first()
    logger.debug(f"Recherche utilisateur par username '{username}' : {'trouvé' if user else 'non trouvé'}")
    return user

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(
        select(User)
        .options(selectinload(User.sensitive_data))
        .where(User.email == email)
    )
    user = result.scalars().first()
    logger.debug(f"Recherche utilisateur par email '{email}' : {'trouvé' if user else 'non trouvé'}")
    return user

async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    role: str = "user",
    encryption_key: Optional[str] = None,
) -> User:
    if await get_user_by_username(db, username):
        logger.warning(f"Échec création utilisateur : username '{username}' déjà utilisé")
        raise ValueError(f"Le nom d'utilisateur '{username}' existe déjà.")
    if await get_user_by_email(db, email):
        logger.warning(f"Échec création utilisateur : email '{email}' déjà utilisé")
        raise ValueError(f"L'email '{email}' existe déjà.")
    hashed_password = get_password_hash(password)
    key = encryption_key or generate_user_key()
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role,
        encryption_key=key,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(f"Nouvel utilisateur créé : {username} ({email})")
    return user

async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"Échec d'authentification pour '{username}'")
        return None
    logger.info(f"Authentification réussie pour '{username}'")
    return user
