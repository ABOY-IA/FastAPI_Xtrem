import os
import pytest
import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import api.db.base as db_base
import api.db.session as db_sess
from api.main import app

# 1) URL de test
TEST_DB_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DB_URL:
    raise RuntimeError("La variable TEST_DATABASE_URL doit être définie pour les tests")

if not TEST_DB_URL.startswith("postgresql://"):
    raise RuntimeError("TEST_DATABASE_URL doit commencer par postgresql://")

TEST_ASYNC_URL = TEST_DB_URL.replace("postgresql://", "postgresql+asyncpg://")

# 2) Engine + Session async pour pytest
engine = create_async_engine(TEST_ASYNC_URL, echo=False, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
db_sess.SessionLocal = TestingSessionLocal

@pytest.fixture(scope="session")
def event_loop():
    """Créer une boucle d'événement dédiée pour pytest-asyncio."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_test_db(event_loop):
    """Initialise la base pour les tests puis la détruit à la fin."""
    async with engine.begin() as conn:
        await conn.run_sync(db_base.Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(db_base.Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def db_session():
    """Session DB asynchrone pour chaque test."""
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture(scope="function")
def client(setup_test_db):
    """Client de test FastAPI (sync, mais supporte l'app async)."""
    with TestClient(app) as c:
        yield c
