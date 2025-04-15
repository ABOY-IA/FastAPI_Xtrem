from fastapi import FastAPI
from api.db.base import init_db
from loguru import logger

def register_startup_events(app: FastAPI):
    @app.on_event("startup")
    async def on_startup():
        init_db()

async def connect_to_db():
    logger.info("✅ Connexion à la base de données")

async def disconnect_from_db():
    logger.info("🛑 Déconnexion de la base de données")

