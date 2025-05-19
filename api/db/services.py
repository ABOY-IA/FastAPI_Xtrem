from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from api.db.models import User

from passlib.context import CryptContext
from api.core.crypto import generate_user_key

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    role: str = "user",
    encryption_key: Optional[str] = None,
) -> User:
    # unicité
    if await get_user_by_username(db, username):
        raise ValueError(f"Le nom d'utilisateur '{username}' existe déjà.")
    if await get_user_by_email(db, email):
        raise ValueError(f"L'email '{email}' existe déjà.")
    # hash et clé
    hashed_password = get_password_hash(password)
    key = encryption_key or generate_user_key()
    # création
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
    return user

async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> Optional[User]:
    user = await get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
