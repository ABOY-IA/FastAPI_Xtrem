from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_register_user():
    response = client.post("/users/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword"
    })
    assert response.status_code in [201, 400]
    if response.status_code == 201:
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "testuser@example.com"

def test_login_success():
    response = client.post("/users/login", json={
        "username": "testuser",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] in ["user", "admin"]
    assert data["username"] == "testuser"

def test_login_fail():
    response = client.post("/users/login", json={
        "username": "testuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
