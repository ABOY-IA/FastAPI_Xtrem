from fastapi.testclient import TestClient
from api.main import app  # assure-toi que c'est bien le bon chemin vers ton app FastAPI

client = TestClient(app)


def test_create_user():
    response = client.post("/users/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 201

def test_login_user():
    response = client.post("/users/login", json={
        "username": "testuser",
        "password": "testpassword"
    })
    assert response.status_code == 200

def test_delete_user():
    response = client.delete("/users/testuser")
    assert response.status_code == 200
