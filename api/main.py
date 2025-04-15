from fastapi import FastAPI
import uvicorn
from api.events import register_startup_events, connect_to_db, disconnect_from_db
from api.users.routes import router as users_router
from api.admin.routes import router as admin_router

# Création de l'application FastAPI avec ses métadonnées
app = FastAPI(
    title="FastAPI Xtrem",
    description="API complète pour la gestion des utilisateurs et sécurité.",
    version="0.1.0"
)

# Enregistrement des événements de démarrage pour initialiser la base (création des tables)
register_startup_events(app)

# Ajout des gestionnaires d'événements pour la connexion et la déconnexion (logs)
app.add_event_handler("startup", connect_to_db)
app.add_event_handler("shutdown", disconnect_from_db)

# Endpoint racine pour vérifier le bon fonctionnement de l'API
@app.get("/", tags=["Root"])
def read_root() -> dict:
    """
    Endpoint de test pour vérifier que l'API fonctionne.
    Renvoie un dictionnaire JSON avec le message "Hello World".
    """
    return {"message": "Hello World"}

# Inclusion du routeur pour les endpoints utilisateurs
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)