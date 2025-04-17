import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.main import app
from fastapi.testclient import TestClient
from api.db.schemas import UserCreate# Importer tes modèles
from api.db.models import User# Importer tes modèles

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Crée l'engine et la session pour les tests
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crée une instance de TestClient
client = TestClient(app)

# Crée les tables dans la base de données pour les tests
@pytest.fixture(scope="module")
def setup_database():
    # Créer les tables
    User.metadata.create_all(bind=engine)
    # Retourner la session de test
    db = TestingSessionLocal()
    yield db
    # Nettoyer après le test
    db.close()
    User.metadata.drop_all(bind=engine)

# Fixture pour obtenir la session de test
@pytest.fixture()
def db(setup_database):
    return setup_database

# Test de l'enregistrement d'un utilisateur
def test_register_user(db):
    response = client.post("/users/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 201

    # Vérifie que l'utilisateur est bien enregistré dans la base de données
    user = db.query(User).filter(User.username == "testuser").first()
    assert user is not None
    assert user.username == "testuser"

# Test de la connexion de l'utilisateur
def test_login_user():
    response = client.post("/users/login", json={
        "username": "testuser",
        "password": "testpassword"
    })
    assert response.status_code == 200


def test_delete_user(db):
    # S'assurer que l'utilisateur est dans la DB
    user = db.query(User).filter(User.username == "testuser").first()
    assert user is not None

    response = client.delete(f"users/{user.username}")

    assert response.status_code == 200
    assert response.json() == {"message": "User 'testuser' deleted successfully."}
