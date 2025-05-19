import os
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import api.db.base as db_base
import api.db.session as db_sess

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("La variable DATABASE_URL doit être définie pour les tests")

if not DB_URL.startswith("postgresql://"):
    raise RuntimeError("DATABASE_URL doit commencer par postgresql://")

ASYNC_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(ASYNC_URL, echo=False, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
db_sess.SessionLocal = TestingSessionLocal

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """
    Crée toutes les tables de la base UNE FOIS au début de la session de tests,
    et détruit toutes les tables à la fin de la session.
    Cela évite les conflits de transaction entre les requêtes HTTP des tests.
    """
    await db_base.init_db()
    yield
    # Nettoyage à la toute fin de la session de tests :
    async with engine.begin() as conn:
        await conn.run_sync(db_base.Base.metadata.drop_all)

@pytest_asyncio.fixture
async def async_client():
    """
    Fournit un client HTTP asynchrone pour FastAPI, pointant vers le service API Docker.
    """
    async with AsyncClient(base_url="http://api:8000") as ac:
        yield ac

@pytest_asyncio.fixture
async def db_session():
    """
    Fournit une session DB asynchrone isolée pour chaque test (pour usage direct).
    """
    async with TestingSessionLocal() as session:
        yield session
