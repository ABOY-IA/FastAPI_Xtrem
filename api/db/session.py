import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("La variable d'environnement DATABASE_URL doit être définie")

# on construit l'URL asyncpg à partir de l'URL postgres classique
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    raise RuntimeError("DATABASE_URL doit commencer par postgresql://")

# Engine asynchrone pour les sessions
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)

# Session factory asynchrone
SessionLocal: sessionmaker[AsyncSession] = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def connect_to_db() -> None:
    """
    Utilisé par test_co_db.py pour vérifier qu'on peut pinger la base.
    """
    async with async_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
        # pas de commit nécessaire pour un simple SELECT
