import os
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import api.db.base as db_base
import api.db.session as db_sess
from tests.logger import logger  # <-- Ajout du logger

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    logger.error("La variable DATABASE_URL doit être définie pour les tests")
    raise RuntimeError("La variable DATABASE_URL doit être définie pour les tests")
if not DB_URL.startswith("postgresql://"):
    logger.error("DATABASE_URL doit commencer par postgresql://")
    raise RuntimeError("DATABASE_URL doit commencer par postgresql://")

ASYNC_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://")
engine = create_async_engine(ASYNC_URL, echo=False, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
db_sess.SessionLocal = TestingSessionLocal

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    logger.info("Initialisation de la base de test")
    await db_base.init_db()
    yield
    logger.info("Nettoyage de la base de test")
    async with engine.begin() as conn:
        await conn.run_sync(db_base.Base.metadata.drop_all)

@pytest_asyncio.fixture
async def async_client():
    """
    Fournit un client HTTP asynchrone pour FastAPI, pointant vers le service API Docker.
    """
    logger.debug("Création du client HTTP asynchrone pour les tests")
    async with AsyncClient(base_url="http://api:8000") as ac:
        yield ac

@pytest_asyncio.fixture
async def db_session():
    """
    Fournit une session DB asynchrone isolée pour chaque test (pour usage direct).
    """
    logger.debug("Création d'une session DB asynchrone de test")
    async with TestingSessionLocal() as session:
        yield session
