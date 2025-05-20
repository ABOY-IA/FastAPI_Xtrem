import pytest

@pytest.mark.order(1)
@pytest.mark.asyncio
async def test_create_user(async_client):
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword"
    }
    resp = await async_client.post("/users/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert data["role"] == "user"

@pytest.mark.order(2)
@pytest.mark.asyncio
async def test_login_user_returns_tokens(async_client):
    await async_client.post("/users/register", json={
        "username": "loginuser",
        "email": "login@example.com",
        "password": "pwd1234"
    })
    resp = await async_client.post("/users/login", json={
        "username": "loginuser",
        "password": "pwd1234"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["access_token"], str)
    assert isinstance(data["refresh_token"], str)
    assert data["token_type"] == "bearer"
