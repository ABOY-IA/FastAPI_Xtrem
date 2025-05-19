from fastapi import FastAPI
from loguru import logger
from api.db.base import init_db

def register_startup_events(app: FastAPI):
    @app.on_event("startup")
    async def on_startup():
        logger.info("🔄 Initialisation DB...")
        await init_db()

    @app.on_event("shutdown")
    async def on_shutdown():
        logger.info("👋 Application shutting down")
