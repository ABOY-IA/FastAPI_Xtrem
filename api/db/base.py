import asyncio
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
from .models import Base
from .session import async_engine
from api.logger import logger

async def init_db(max_retries: int = 30, delay: float = 2.0) -> None:
    """
    Crée toutes les tables en début d'application, via engine async.
    Tente plusieurs fois si la base n'est pas encore prête.
    """
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Base de données initialisée (tables créées)")
                return
        except Exception as e:
            last_exception = e
            logger.warning(
                f"[init_db] Tentative {attempt}/{max_retries} échouée : {e}. Nouvelle tentative dans {delay} secondes..."
            )
            await asyncio.sleep(delay)
    logger.error(f"[init_db] Impossible d'initialiser la base après {max_retries} tentatives. Dernière erreur : {last_exception}")
    raise last_exception
