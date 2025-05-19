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
engine = create_async_engine(TEST_ASYNC_URL, echo=True, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
db_sess.SessionLocal = TestingSessionLocal

# 3) Création / destruction du schéma
@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    await db_base.init_db()
    yield
    # drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(db_base.Base.metadata.drop_all)

# 4) Boucle d’événements
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# 5) Client FastAPI (sync) devant un app async
@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
