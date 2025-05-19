from fastapi import FastAPI
import uvicorn
from api.events import register_startup_events
from api.users.routes import router as users_router
from api.admin.routes import router as admin_router
from api.auth.routes import router as auth_router

app = FastAPI(
    title="FastAPI Xtrem (100% async)",
    description="API utilisateurs/sécurité, toute en async.",
    version="0.2.0-async"
)

register_startup_events(app)

@app.get("/", tags=["Root"])
async def read_root() -> dict:
    return {"message": "Hello World"}

@app.get("/health", tags=["Monitoring"])
async def health() -> dict:
    return {"status": "ok"}

app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
