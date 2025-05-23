import pytest
import asyncio
from tests.logger import logger

@pytest.mark.asyncio
async def test_login_and_refresh_cycle(async_client):
    # --- 1) Création de l'utilisateur via l'API ---
    payload = {
        "username": "eve",
        "email": "eve@example.com",
        "password": "EvePass!23"
    }
    resp = await async_client.post("/users/register", json=payload)
    assert resp.status_code == 201, resp.text
    logger.info("Utilisateur 'eve' créé pour le test de refresh token")

    # --- 2) Login ---
    resp = await async_client.post(
        "/users/login",
        json={"username": "eve", "password": "EvePass!23"}
    )
    assert resp.status_code == 200, resp.text
    tok = resp.json()
    access1 = tok["access_token"]
    refresh1 = tok["refresh_token"]
    logger.info("Utilisateur 'eve' connecté pour le test de refresh token")

    # --- 3a) Accès à une route protégée (ex: /users/profile) ---
    protected = await async_client.get(
        "/users/profile",
        headers={"X-User": "eve", "Authorization": f"Bearer {access1}"}
    )
    assert protected.status_code == 200
    profile_data = protected.json()
    logger.debug(f"profile_data = {profile_data}")

    await asyncio.sleep(0.1)

    # --- 4) Rotation du refresh ---
    resp2 = await async_client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh1}"}
    )
    assert resp2.status_code == 200, resp2.text
    tok2 = resp2.json()
    assert tok2["access_token"] != access1
    assert tok2["refresh_token"] != refresh1
    logger.info("Rotation du refresh token réussie pour 'eve'")

    # --- 5) Ancien refresh invalide ---
    resp3 = await async_client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh1}"}
    )
    assert resp3.status_code == 401
    logger.info("Ancien refresh token invalidé comme attendu pour 'eve'")
