from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
from .models import Base
from .session import async_engine
from api.logger import logger

async def init_db() -> None:
    """
    Crée toutes les tables en début d'application, via engine async.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Base de données initialisée (tables créées)")
