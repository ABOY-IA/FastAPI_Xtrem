from loguru import logger

async def connect_to_db():
    logger.info("✅ Connexion à la base de données")

async def disconnect_from_db():
    logger.info("🛑 Déconnexion de la base de données")